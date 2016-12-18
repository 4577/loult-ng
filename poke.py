#!/usr/bin/python3
#-*- encoding: Utf-8 -*-
import logging
import random
from asyncio import get_event_loop
from collections import OrderedDict
from colorsys import hsv_to_rgb
from datetime import datetime, timedelta
from hashlib import md5
from html import escape
from io import BytesIO
from json import loads, dumps
from os import urandom
from re import sub
from shlex import quote
from struct import pack
from subprocess import run, PIPE
from time import time
from typing import List, Dict, Set

from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
from scipy.io import wavfile

from config import pokemon, ATTACK_RESTING_TIME
from effects import get_random_effect
from effects.effects import Effect, AudioEffect, TextEffect
from salt import SALT


# Alias with default parameters
json = lambda obj: dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf8')


class User:
    """Stores a user's state and parameters, which are also used to render the user's audio messages"""
    lang_voices_mapping = {"fr" : ("fr" , (1, 2, 3, 4, 5, 6, 7)),
                           "en" : ("us" , (1, 2, 3)),
                           "es" : ("us" , (1, 2)),
                           "de" : ("de" , (4, 5, 6, 7))}

    volumes_presets = {'us1': 1.658, 'us2': 1.7486, 'us3': 3.48104, 'es1': 3.26885, 'es2': 1.84053}

    links_translation = {'fr': 'cliquez mes petits chatons',
                         'de': 'Klick drauf!',
                         'es': 'Clico JAJAJA',
                         'en': "Click it mate"}

    def __init__(self, cookie_hash, channel, client):
        """Initiating a user using its cookie md5 hash"""
        self.speed = (cookie_hash[5] % 50) + 100
        self.pitch = cookie_hash[0] % 100
        self.voice_id = cookie_hash[1]
        self.poke_id = (cookie_hash[2] | (cookie_hash[3] << 8)) % len(pokemon) + 1
        self.pokename = pokemon[self.poke_id]
        self.color = hsv_to_rgb(cookie_hash[4] / 255, 1, 0.7)
        self.color = '#' + pack('3B', *(int(255 * i) for i in self.color)).hex()

        self.user_id = cookie_hash.hex()[-5:]

        self.channel = channel
        self.client = client
        self.active_text_effects, self.active_audio_effects = [], []
        self.last_attack = datetime.now() # any user has to wait some time before attacking, after entering the chan

    def __hash__(self):
        return self.user_id.__hash__()

    def __eq__(self, other):
        return self.user_id == other.user_id

    @property
    def info(self):
        return {
            'userid': self.user_id,
            'params': {
                'name': self.pokename,
                'img': '/pokemon/%s.gif' % str(self.poke_id).zfill(3),
                'color': self.color
            }
        }

    def render_message(self, text, lang):

        def apply_effects(input_obj, effect_list : List[Effect]):
            if effect_list:
                for effect in effect_list:
                    if effect.is_expired():
                        self.client.sendMessage(json({"type":"attack", "event" : "timeout",
                                                      "effect" : effect.name}))
                        effect_list.remove(effect) # if the effect has expired, remove it
                    else:
                        if isinstance(effect, TextEffect):
                            input_obj = effect.process(*input_obj)
                        elif isinstance(effect, AudioEffect):
                            input_obj = effect.process(input_obj)

            return input_obj

        cleaned_text = text[:500]
        displayed_text, rendered_text = apply_effects((cleaned_text, cleaned_text), self.active_text_effects)
        rendered_text = sub('(https?://[^ ]*[^.,?! :])', self.links_translation[lang], rendered_text)
        rendered_text = rendered_text.replace('#', 'hashtag ')
        rendered_text = quote(rendered_text.strip(' -"\'`$();:.'))

        # Language support : default to french if value is incorrect
        lang, voices = self.lang_voices_mapping.get(lang, self.lang_voices_mapping["fr"])
        voice = voices[self.voice_id % len(voices)]

        if lang != 'fr':
            sex = voice
        else:
            sex = 4 if voice in (2, 4) else 1

        volume = 1
        if lang != 'fr' and lang != 'de':
            volume = self.volumes_presets['%s%d' % (lang, voice)] * 0.5

        # Synthesis of the voice using the output text
        synth_string = 'MALLOC_CHECK_=0 espeak -s %d -p %d --pho -q -v mb/mb-%s%d %s | MALLOC_CHECK_=0 mbrola -v %g -e /usr/share/mbrola/%s%d/%s%d - -.wav' % (
                self.speed, self.pitch, lang, sex, rendered_text, volume, lang, voice, lang, voice)
        logging.debug("Running synth command %s" % synth_string)
        wav = run(synth_string, shell=True, stdout=PIPE, stderr=PIPE).stdout
        wav = wav[:4] + pack('<I', len(wav) - 8) + wav[8:40] + pack('<I', len(wav) - 44) + wav[44:]

        # if there are effets in the audio_effect list, we run it
        if self.active_audio_effects:
            # converting the wav to ndarray, which is much easier to manipulate for DSP
            rate, data = wavfile.read(BytesIO(wav),)
            # casting the data array to the right format (float32, for usage by pysndfx)
            data = apply_effects((data / (2. ** 15)).astype('float32'), self.active_audio_effects)
            data = (data * (2. ** 15)).astype("int16")
            # then, converting it back to bytes
            bytes_obj = bytes()
            bytes_buff = BytesIO(bytes_obj)
            wavfile.write(bytes_buff, rate, data)
            wav = bytes_buff.read()

        return displayed_text, wav


class LoultServer(WebSocketServerProtocol):

    def __init__(self):
        super().__init__()
        self.cookie, self.channel, self.sendend, self.lasttxt = None, None, None, None
        self.cnx = False

    def onConnect(self, request):
        """HTTP-level request, triggered when the client opens the WSS connection"""
        print("Client connecting: {0}".format(request.peer))

        # trying to extract the cookie from the request header. Else, creating a new cookie and
        # telling the client to store it with a Set-Cookie header
        retn = {}
        try:
            ck = request.headers['cookie'].split('id=')[1].split(';')[0]
        except (KeyError, IndexError):
            ck = urandom(16).hex()
            retn = {'Set-Cookie': 'id=%s; expires=Tue, 19 Jan 2038 03:14:07 UTC; Path=/' % ck}

        cookie_hash = md5((ck + SALT).encode('utf8')).digest()
        self.cookie = cookie_hash
        self.channel = request.path.lower().split('/', 2)[-1]
        self.channel = sub("/.*", "", self.channel)
        self.sendend = datetime.now()
        self.lasttxt = datetime.now()

        return None, retn

    def onOpen(self):
        """Triggered once the WSS is opened. Mainly consists of registering the user in the channel, and
        sending the channel's information (connected users and the backlog) to the user"""
        print("WebSocket connection open.")

        # telling the  connected users'register to register the current user in the current channel
        self.user = loult_state.channel_connect(self, self.cookie, self.channel)

        self.cnx = True  # connected!

        # copying the channel's userlist info and telling the current JS client which userid is "its own"
        my_userlist = OrderedDict([(user_id , user.info)
                                  for user_id, user in loult_state.chans[self.channel].users.items()])
        my_userlist[self.user.user_id]['params']['you'] = True  # tells the JS client this is the user's pokemon
        # sending the current user list to the client
        self.sendMessage(json({
            'type': 'userlist',
            'users': list(my_userlist.values())
        }))

        self.sendMessage(json({
            'type': 'backlog',
            'msgs': loult_state.chans[self.channel].backlog
        }))

    def _broadcast_to_channel(self, msg_dict, binary_payload=None):
        for client in loult_state.chans[self.channel].clients:
            client.sendMessage(json(msg_dict))
            if binary_payload:
                client.sendMessage(binary_payload, isBinary=True)

    def _msg_handler(self, msg_data : Dict):

        # user object instance renders both the output sound and output text
        output_msg, wav = self.user.render_message(msg_data["msg"], msg_data.get("lang", "fr"))

        # rate limit: if the previous message is less than 100 milliseconds from this one, we stop the broadcast
        now = datetime.now()
        if now - self.lasttxt <= timedelta(milliseconds=100):
            return
        self.lasttxt = now # updating with current time

        # estimating the end of the current voice render, to rate limit again
        calc_sendend = max(self.sendend, now) + timedelta(seconds=len(wav) * 8 / 6000000)
        synth = calc_sendend < now + timedelta(seconds=2.5)
        if synth:
            self.sendend = calc_sendend

        info = loult_state.log_to_backlog(loult_state.chans[self.channel].users[self.user.user_id].info['params'],
                                          output_msg, self.channel)

        # broadcast message and rendered audio to all clients in the channel
        self._broadcast_to_channel({'type': 'msg',
                                    'userid': self.user.user_id,
                                    'msg': info['msg'],
                                    'date': info['date']},
                                   wav if synth else None)

    def _attack_handler(self, msg_data : Dict):
        adversary_id, adversary = loult_state.get_user_by_name(msg_data.get("target", self.user.pokename),
                                                                            self.channel,
                                                                            msg_data.get("order", 0))

        # checking if the target user is found, and if the current user has waited long enough to attack
        if adversary is not None and (datetime.now() - timedelta(seconds=ATTACK_RESTING_TIME)) > self.user.last_attack:
            self._broadcast_to_channel({'type': 'attack',
                                        'event' : 'attack',
                                        'attacker_id': self.user.user_id,
                                        'defender_id': adversary_id})

            attack_dice, defend_dice = random.randint(0,100), random.randint(0,100)
            self._broadcast_to_channel({'type': 'attack',
                                        'event': 'dice',
                                        'attacker_dice' : attack_dice, "defender_dice" : defend_dice,
                                        'attacker_id': self.user.user_id, 'defender_id': adversary_id})

            affected_user = None
            if attack_dice > defend_dice:
                affected_user = adversary
            elif random.randint(1,3) == 1:
                affected_user = self.user

            if affected_user is not None:
                effect = get_random_effect()
                if isinstance(effect, AudioEffect):
                    affected_user.active_audio_effects.append(effect)
                else:
                    affected_user.active_text_effects.append(effect)

                self._broadcast_to_channel({'type': 'attack',
                                            'event': 'effect',
                                            'target_id': affected_user.user_id,
                                            'effect': effect.name})
            else:
                self._broadcast_to_channel({'type': 'attack',
                                            'event': 'nothing'})

            self.user.last_attack = datetime.now()
        else:
            self.sendMessage(json({'type': 'attack',
                                   'event': 'invalid'}))

    def _move_handler(self, msg_data : Dict):
        # checking if all the necesary data is here
        if not {"x", "y", "id"}.issubset(set(msg_data.keys())):
            return
        # signalling all users in channel that this user moved
        self._broadcast_to_channel({'type' : 'move',
                                    'id' : escape(msg_data['id'][:12]),
                                    'userid': self.user.user_id,
                                    'x' : float(msg_data['x']),
                                    'y' : float(msg_data['y'])})

    def onMessage(self, payload, isBinary):
        """Triggered when a user receives a message"""
        msg = loads(payload.decode('utf8'))

        if msg['type'] == 'msg':
            # when the message is just a simple text message (regular chat)
            self._msg_handler(msg)

        elif msg["type"] == "attack":
            # when the current client attacks someone else
            self._attack_handler(msg)

        elif msg["type"] == "move":
            # when a user moves
            self._move_handler(msg)

    def onClose(self, wasClean, code, reason):
        """Triggered when the WS connection closes. Mainly consists of deregistering the user"""
        if hasattr(self, 'cnx') and self.cnx:
            loult_state.channel_leave(self, self.user, self.channel)

        print("WebSocket connection closed: {0}".format(reason))


class Channel:
    def __init__(self, channel_name):
        self.name = channel_name
        self.clients = set()  # type:Set[LoultServer]
        self.users = OrderedDict()  # type:OrderedDict[str, User]
        self.refcnts = {}  # type:Dict[str,int]
        self.backlog = []  # type:List


class LoultServerState:

    def __init__(self):
        self.chans = {} # type:Dict[str,Channel]

    def _signal_user_connect(self, client : LoultServer, user : User):
        client.sendMessage(json({
            'type': 'connect',
            **user.info}))

    def channel_connect(self, client : LoultServer, user_cookie : str, channel_name : str) -> User:
        # if the channel doesn't exist, we instanciate it and add it to the channel dict
        if channel_name not in self.chans:
            self.chans[channel_name] = Channel(channel_name)
        channel_obj = self.chans[channel_name]
        channel_obj.clients.add(client)

        new_user = User(user_cookie, channel_name, client)
        if new_user.user_id not in channel_obj.users:
            for other_client in channel_obj.clients:
                if other_client != client:
                    self._signal_user_connect(other_client, new_user)
            channel_obj.refcnts[new_user.user_id] = 1
            channel_obj.users[new_user.user_id] = new_user
            return new_user
        else:
            channel_obj.refcnts[new_user.user_id] += 1
            return channel_obj.users[new_user.user_id] # returning an already existing instance of the user

    def _signal_user_disconnect(self, client: LoultServer, user: User):
        client.sendMessage(json({
            'type': 'disconnect',
            'userid': user.user_id
        }))

    def channel_leave(self, client : LoultServer, user : User, channel_name : str):
        try:
            channel_obj = self.chans[channel_name]
            channel_obj.refcnts[user.user_id] -= 1

            # if the user is not connected anymore, we signal its disconnect to the others
            if channel_obj.refcnts[user.user_id] < 1:
                channel_obj.clients.discard(client)
                del channel_obj.users[user.user_id]
                del channel_obj.refcnts[user.user_id]

                for client in channel_obj.clients:
                    self._signal_user_disconnect(client, user)

                # if no one's connected dans the backlog is empty, we delete the channel
                if not channel_obj.clients and not channel_obj.backlog:
                    del self.chans[channel_name]
        except KeyError:
            pass

    def log_to_backlog(self, user_data, msg : str, channel : str):
        # creating new entry
        info = {
            'user': user_data,
            'msg': sub('(https?://[^ ]*[^.,?! :])', r'<a href="\1" target="_blank">\1</a>',
                       escape(msg[:500])),
            'date': time() * 1000
        }

        # adding it to list and removing oldest entry
        self.chans[channel].backlog.append(info)
        self.chans[channel].backlog = self.chans[channel].backlog[-10:]
        return info

    def get_user_by_name(self, pokemon_name : str, channel : str, order = 0) -> (int, User):

        for user_id, user in self.chans[channel].users.items():
            if user.pokename.lower() == pokemon_name.lower():
                if order == 0:
                    return user_id, user
                else:
                    order -= 1

        return None, None


loult_state = LoultServerState()

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)

    factory = WebSocketServerFactory(server='Lou.lt/NG') # 'ws://127.0.0.1:9000',
    factory.protocol = LoultServer
    factory.setProtocolOptions(autoPingInterval=60, autoPingTimeout=30)

    loop = get_event_loop()
    coro = loop.create_server(factory, '127.0.0.1', 9000)
    server = loop.run_until_complete(coro)

    loop.run_forever()

