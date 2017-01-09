#!/usr/bin/python3
#-*- encoding: Utf-8 -*-
import logging
import random
from asyncio import get_event_loop
from collections import OrderedDict
from colorsys import hsv_to_rgb
from copy import deepcopy
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
from typing import List, Dict, Set, Any, Tuple

from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
from scipy.io import wavfile

from config import pokemon, ATTACK_RESTING_TIME
from effects import get_random_effect
from effects.effects import Effect, AudioEffect, TextEffect, HiddenTextEffect, ExplicitTextEffect, PhonemicEffect, \
    EffectGroup
from effects.phonems import PhonemList
from effects.tools import resample
from salt import SALT


# Alias with default parameters
json = lambda obj: dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf8')


class User:
    """Stores a user's state and parameters, which are also used to render the user's audio messages"""
    lang_voices_mapping = {"fr" : ("fr" , (1, 2, 3, 4, 5, 6, 7)),
                           "en" : ("us" , (1, 2, 3)),
                           "es" : ("es" , (1, 2)),
                           "de" : ("de" , (4, 5, 6, 7))}

    volumes_presets = {'fr1': 1.17138, 'fr2': 1.60851,'fr3': 1.01283, 'fr4': 1.0964, 'fr5': 2.64384, 'fr6': 1.35412,
                       'fr7': 1.96092, 'us1': 1.658, 'us2': 1.7486, 'us3': 3.48104, 'es1': 3.26885, 'es2': 1.84053}

    links_translation = {'fr': 'cliquez mes petits chatons',
                         'de': 'Klick drauf!',
                         'es': 'Clico JAJAJA',
                         'en': "Click it mate"}

    def __init__(self, cookie_hash, channel, client):
        """Initiating a user using its cookie md5 hash"""
        self.speed = (cookie_hash[5] % 80) + 90
        self.pitch = cookie_hash[0] % 100
        self.voice_id = cookie_hash[1]
        self.poke_id = (cookie_hash[2] | (cookie_hash[3] << 8)) % len(pokemon) + 1
        self.pokename = pokemon[self.poke_id]
        self.color = hsv_to_rgb(cookie_hash[4] / 255, 1, 0.7)
        self.color = '#' + pack('3B', *(int(255 * i) for i in self.color)).hex()

        self.user_id = cookie_hash.hex()[-16:]

        self.channel = channel
        self.client = client
        self.effects = {cls : [] for cls in (AudioEffect, HiddenTextEffect, ExplicitTextEffect, PhonemicEffect)}
        self.last_attack = datetime.now() # any user has to wait some time before attacking, after entering the chan
        self._info = None

    def __hash__(self):
        return self.user_id.__hash__()

    def __eq__(self, other):
        return self.user_id == other.user_id

    def add_effect(self, effect : Effect):
        """Adds an effect to one of the active effects list (depending on the effect type)"""
        if isinstance(effect, EffectGroup): # if the effect is a meta-effect (a group of several effects)
            added_effects = effect.effects
        else:
            added_effects = [effect]

        for efct in added_effects:
            for cls in (AudioEffect, HiddenTextEffect, ExplicitTextEffect, PhonemicEffect):
                if isinstance(efct, cls):
                    self.effects[cls].append(efct)
                    break

    @property
    def info(self):
        if self._info is None:
            self._info = {
                'userid': self.user_id,
                'params': {
                    'name': self.pokename,
                    'img': '/pokemon/%s.gif' % str(self.poke_id).zfill(3),
                    'color': self.color
                }
            }
        return self._info

    def apply_effects(self, input_obj, effect_list: List[Effect]):
        if effect_list:
            for effect in effect_list:
                if effect.is_expired():
                    effect_list.remove(effect)  # if the effect has expired, remove it
                else:
                    input_obj = effect.process(input_obj)

        return input_obj

    def _vocode(self, text, lang) -> bytes:
        """Renders a text and a language to a wav bytes object using espeak + mbrola"""
        # Language support : default to french if value is incorrect
        lang, voices = self.lang_voices_mapping.get(lang, self.lang_voices_mapping["fr"])
        voice = voices[self.voice_id % len(voices)]

        if lang != 'fr':
            sex = voice
        else:
            sex = 4 if voice in (2, 4) else 1

        volume = 1
        if lang != 'de':
            volume = self.volumes_presets['%s%d' % (lang, voice)] * 0.5

        if self.effects[PhonemicEffect]:
            # first running the text-to-phonems conversion, then applying the phonemic effects, then rendering audio
            phonem_synth_string = 'MALLOC_CHECK_=0 espeak -s %d -p %d --pho -q -v mb/mb-%s%d %s ' \
                                  % (self.speed, self.pitch, lang, sex, text)
            logging.debug("Running espeak command %s" % phonem_synth_string)
            phonems = PhonemList(run(phonem_synth_string, shell=True, stdout=PIPE, stderr=PIPE)
                                 .stdout
                                 .decode("utf-8")
                                 .strip())
            modified_phonems = self.apply_effects(phonems, self.effects[PhonemicEffect])
            audio_synth_string = 'MALLOC_CHECK_=0 mbrola -v %g -e /usr/share/mbrola/%s%d/%s%d - -.wav' \
                                 % (volume, lang, voice, lang, voice)
            logging.debug("Running mbrola command %s" % audio_synth_string)
            wav = run(audio_synth_string, shell=True, stdout=PIPE,
                      stderr=PIPE, input=str(modified_phonems).encode("utf-8")).stdout
        else:
            # regular render
            synth_string = 'MALLOC_CHECK_=0 espeak -s %d -p %d --pho -q -v mb/mb-%s%d %s ' \
                           '| MALLOC_CHECK_=0 mbrola -v %g -e /usr/share/mbrola/%s%d/%s%d - -.wav' \
                           % (self.speed, self.pitch, lang, sex, text, volume, lang, voice, lang, voice)
            logging.debug("Running synth command %s" % synth_string)
            wav = run(synth_string, shell=True, stdout=PIPE, stderr=PIPE).stdout

        return wav[:4] + pack('<I', len(wav) - 8) + wav[8:40] + pack('<I', len(wav) - 44) + wav[44:]

    def render_message(self, text, lang):
        cleaned_text = text[:500]
        # applying "explicit" effects (visible to the users)
        displayed_text = self.apply_effects(cleaned_text, self.effects[ExplicitTextEffect])
        # applying "hidden" effects (invisible on the chat, only heard in the audio)
        rendered_text = self.apply_effects(displayed_text, self.effects[HiddenTextEffect])
        rendered_text = sub('(https?://[^ ]*[^.,?! :])', self.links_translation[lang], rendered_text)
        rendered_text = rendered_text.replace('#', 'hashtag ')
        rendered_text = quote(rendered_text.strip(' -"\'`$();:.'))

        # rendering the audio from the text
        wav = self._vocode(rendered_text, lang)

        # if there are effets in the audio_effect list, we run it
        if self.effects[AudioEffect]:
            # converting the wav to ndarray, which is much easier to use for DSP
            rate, data = wavfile.read(BytesIO(wav))
            data = (data / (2. ** 15)).astype('float32')
            if rate != 16000:
                data = resample(data, rate)
                rate = 16000
            # casting the data array to the right format (float32, for usage by pysndfx)
            data = self.apply_effects(data, self.effects[AudioEffect])

            # casting it back to int16
            data = (data * (2. ** 15)).astype("int16")
            # then, converting it back to binary data
            bytes_obj = bytes()
            bytes_buff = BytesIO(bytes_obj)
            wavfile.write(bytes_buff, rate, data)
            wav = bytes_buff.read()

        return displayed_text, wav


class LoultServer(WebSocketServerProtocol):

    def __init__(self):
        super().__init__()
        self.cookie, self.channel_n, self.channel_obj, self.sendend, self.lasttxt = None, None, None, None, None
        self.cnx = False

    def onConnect(self, request):
        """HTTP-level request, triggered when the client opens the WSS connection"""
        logging.info("Client connecting: {0}".format(request.peer))

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
        self.channel_n = request.path.lower().split('/', 2)[-1]
        self.channel_n = sub("/.*", "", self.channel_n)
        self.sendend = datetime.now()
        self.lasttxt = datetime.now()

        return None, retn

    def onOpen(self):
        """Triggered once the WSS is opened. Mainly consists of registering the user in the channel, and
        sending the channel's information (connected users and the backlog) to the user"""
        print("WebSocket connection open.")

        # telling the  connected users'register to register the current user in the current channel
        self.channel_obj, self.user = loult_state.channel_connect(self, self.cookie, self.channel_n)

        self.cnx = True  # connected!

        # copying the channel's userlist info and telling the current JS client which userid is "its own"
        my_userlist = OrderedDict([(user_id , deepcopy(user.info))
                                   for user_id, user in self.channel_obj.users.items()])
        my_userlist[self.user.user_id]['params']['you'] = True  # tells the JS client this is the user's pokemon
        # sending the current user list to the client
        self.sendMessage(json({
            'type': 'userlist',
            'users': list(my_userlist.values())
        }))

        self.sendMessage(json({
            'type': 'backlog',
            'msgs': self.channel_obj.backlog
        }))

    def _broadcast_to_channel(self, msg_dict, binary_payload=None):
        for client in self.channel_obj.clients:
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

        info = self.channel_obj.log_to_backlog(self.user.user_id, output_msg)

        # broadcast message and rendered audio to all clients in the channel
        self._broadcast_to_channel({'type': 'msg',
                                    'userid': self.user.user_id,
                                    'msg': info['msg'],
                                    'date': info['date']},
                                   wav if synth else None)

    def _attack_handler(self, msg_data : Dict):
        # cleaning up none values in case of fuckups
        msg_data = {key: value for key, value in msg_data.items() if value is not None}

        adversary_id, adversary = self.channel_obj.get_user_by_name(msg_data.get("target", self.user.pokename),
                                                                    msg_data.get("order", 0))

        # checking if the target user is found, and if the current user has waited long enough to attack
        if adversary is not None and (datetime.now() - timedelta(seconds=ATTACK_RESTING_TIME)) > self.user.last_attack:
            self._broadcast_to_channel({'type': 'attack',
                                        'date': time() * 1000,
                                        'event' : 'attack',
                                        'attacker_id': self.user.user_id,
                                        'defender_id': adversary_id})

            attack_dice, defend_dice = random.randint(0,100), random.randint(0,100)
            self._broadcast_to_channel({'type': 'attack',
                                        'date': time() * 1000,
                                        'event': 'dice',
                                        'attacker_dice' : attack_dice, "defender_dice" : defend_dice,
                                        'attacker_id': self.user.user_id, 'defender_id': adversary_id})

            # if the attacker won, the user affected by the effect is the defender, else, there's a a 1/3 chance
            # that the attacker gets the effect (a rebound)
            affected_user = None
            if attack_dice > defend_dice:
                affected_user = adversary
            elif random.randint(1,3) == 1:
                affected_user = self.user

            if affected_user is not None:
                effect = get_random_effect()
                affected_user.add_effect(effect)

                self._broadcast_to_channel({'type': 'attack',
                                            'date': time() * 1000,
                                            'event': 'effect',
                                            'target_id': affected_user.user_id,
                                            'effect': effect.name,
                                            'timeout' : effect.timeout})
            else:
                self._broadcast_to_channel({'type': 'attack',
                                            'date': time() * 1000,
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
            self.channel_obj.channel_leave(self, self.user)

        logging.info("WebSocket connection closed: {0}".format(reason))


class Channel:
    def __init__(self, channel_name):
        self.name = channel_name
        self.clients = set()  # type:Set[LoultServer]
        self.users = OrderedDict()  # type:OrderedDict[str, User]
        self.refcnts = {}  # type:Dict[str,int]
        self.backlog = []  # type:List

    def _signal_user_connect(self, client: LoultServer, user: User):
        client.sendMessage(json({
            'type': 'connect',
            'date': time() * 1000,
            **user.info}))

    def _signal_user_disconnect(self, client: LoultServer, user: User):
        client.sendMessage(json({
            'type': 'disconnect',
            'date': time() * 1000,
            'userid': user.user_id
        }))

    def channel_leave(self, client: LoultServer, user: User):
        try:
            self.refcnts[user.user_id] -= 1

            # if the user is not connected anymore, we signal its disconnect to the others
            if self.refcnts[user.user_id] < 1:
                self.clients.discard(client)
                del self.users[user.user_id]
                del self.refcnts[user.user_id]

                for client in self.clients:
                    self._signal_user_disconnect(client, user)

                # if no one's connected dans the backlog is empty, we delete the channel from the register
                if not self.clients and not self.backlog:
                    del loult_state.chans[self.name]
        except KeyError:
            pass

    def user_connect(self, new_user : User, client : LoultServer):
        if new_user.user_id not in self.users:
            for other_client in self.clients:
                if other_client != client:
                    self._signal_user_connect(other_client, new_user)
            self.refcnts[new_user.user_id] = 1
            self.users[new_user.user_id] = new_user
            return new_user
        else:
            self.refcnts[new_user.user_id] += 1
            return self.users[new_user.user_id]  # returning an already existing instance of the user

    def log_to_backlog(self, user_id, msg: str):
        # creating new entry
        info = {
            'user': self.users[user_id].info['params'],
            'msg': sub('(https?://[^ ]*[^.,?! :])', r'<a href="\1" target="_blank">\1</a>',
                       escape(msg[:500])),
            'date': time() * 1000
        }

        # adding it to list and removing oldest entry
        self.backlog.append(info)
        self.backlog = self.backlog[-10:]
        return info

    def get_user_by_name(self, pokemon_name: str, order=0) -> (int, User):

        for user_id, user in self.users.items():
            if user.pokename.lower() == pokemon_name.lower():
                if order == 0:
                    return user_id, user
                else:
                    order -= 1

        return None, None


class LoultServerState:

    def __init__(self):
        self.chans = {} # type:Dict[str,Channel]

    def channel_connect(self, client : LoultServer, user_cookie : str, channel_name : str) -> Tuple[Channel, User]:
        # if the channel doesn't exist, we instanciate it and add it to the channel dict
        if channel_name not in self.chans:
            self.chans[channel_name] = Channel(channel_name)
        channel_obj = self.chans[channel_name]
        channel_obj.clients.add(client)

        return channel_obj, channel_obj.user_connect(User(user_cookie, channel_name, client), client)


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

