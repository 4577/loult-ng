#!/usr/bin/python3
#-*- encoding: Utf-8 -*-
import logging
import random
from asyncio import get_event_loop
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timedelta
from hashlib import md5
from html import escape
from json import loads, dumps
from os import urandom, path
from re import sub
from time import time
from functools import lru_cache
from typing import List, Dict, Set, Tuple

from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory

from config import ATTACK_RESTING_TIME, BAN_TIME, PUNITIVE_MSG_COUNT, \
     BANNED_WORDS
from salt import SALT
from tools.combat import CombatSimulator
from tools.effects import Effect, AudioEffect, HiddenTextEffect, ExplicitTextEffect, PhonemicEffect, \
     VoiceEffect
from tools.phonems import PhonemList
from tools.tools import AudioRenderer, SpoilerBipEffect, add_msg_html_tag, VoiceParameters, PokeParameters, UserState, \
    prepare_text_for_tts, BannedWords

# Alias with default parameters
json = lambda obj: dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf8')


class User:
    """Stores a user's state and parameters, which are also used to render the user's audio messages"""

    def __init__(self, cookie_hash, channel, client):
        """Initiating a user using its cookie md5 hash"""
        self.audio_renderer = AudioRenderer()
        self.voice_params = VoiceParameters.from_cookie_hash(cookie_hash)
        self.poke_params = PokeParameters.from_cookie_hash(cookie_hash)
        self.user_id = cookie_hash.hex()[-16:]

        self.channel = channel
        self.clients = [client]
        self.state = UserState()
        self._info = None

    def __hash__(self):
        return self.user_id.__hash__()

    def __eq__(self, other):
        return self.user_id == other.user_id

    def throw_dice(self, type="attack") -> Tuple[int, int]:
        bonus = (datetime.now() - self.state.last_attack).seconds // ATTACK_RESTING_TIME if type == "attack" else 0
        return random.randint(1, 100), bonus


    @property
    def info(self):
        if self._info is None:
            self._info = {
                'userid': self.user_id,
                'params': {
                    'name': self.poke_params.pokename,
                    'img': '/pokemon/%s.gif' % str(self.poke_params.poke_id).zfill(3),
                    'color': self.poke_params.color
                }
            }
        return self._info

    @staticmethod
    def apply_effects(input_obj, effect_list: List[Effect]):
        if effect_list:
            for effect in effect_list:
                if effect.is_expired():
                    effect_list.remove(effect)  # if the effect has expired, remove it
                else:
                    input_obj = effect.process(input_obj)

        return input_obj

    def _vocode(self, text: str, lang: str) -> bytes:
        """Renders a text and a language to a wav bytes object using espeak + mbrola"""
        # if there are voice effects, apply them to the voice renderer's voice and give them to the renderer
        if self.state.effects[VoiceEffect]:
            voice_params = self.apply_effects(self.voice_params, self.state.effects[VoiceEffect])
        else:
            voice_params = self.voice_params

        # apply the beep effect for spoilers
        beeped = SpoilerBipEffect(self.audio_renderer, voice_params).process(text, lang)

        if isinstance(beeped, PhonemList) or self.state.effects[PhonemicEffect]:

            modified_phonems = None
            if isinstance(beeped, PhonemList) and self.state.effects[PhonemicEffect]:
                # if it's already a phonem list, we apply the effect diretcly
                modified_phonems = self.apply_effects(beeped, self.state.effects[PhonemicEffect])
            elif isinstance(beeped, PhonemList):
                # no effects, only the beeped phonem list
                modified_phonems = beeped
            elif self.state.effects[PhonemicEffect]:
                # first running the text-to-phonems conversion, then applying the phonemic tools
                phonems = self.audio_renderer.string_to_phonemes(text, lang, voice_params)
                modified_phonems = self.apply_effects(phonems, self.state.effects[PhonemicEffect])

            #rendering audio using the phonemlist
            return self.audio_renderer.phonemes_to_audio(modified_phonems, lang, voice_params)
        else:
            # regular render
            return self.audio_renderer.string_to_audio(text, lang, voice_params)

    def render_message(self, text: str, lang: str):
        cleaned_text = text[:500]
        # applying "explicit" effects (visible to the users)
        displayed_text = self.apply_effects(cleaned_text, self.state.effects[ExplicitTextEffect])
        # applying "hidden" texts effects (invisible on the chat, only heard in the audio)
        rendered_text = self.apply_effects(displayed_text, self.state.effects[HiddenTextEffect])
        rendered_text = prepare_text_for_tts(rendered_text, lang)

        # rendering the audio from the text
        wav = self._vocode(rendered_text, lang)

        # if there are effets in the audio_effect list, we run it
        if self.state.effects[AudioEffect]:
            # converting to f32 (more standard) and resampling to 16k if needed
            rate , data = self.audio_renderer.to_f32_16k(wav)
            # applying the effects pipeline to the sound
            data = self.apply_effects(data, self.state.effects[AudioEffect])
            # converting the sound's ndarray back to bytes
            wav = self.audio_renderer.to_wav_bytes(data, rate)

        return displayed_text, wav


class LoultServer(WebSocketServerProtocol):

    def __init__(self, banned_words=BANNED_WORDS):
        super().__init__()
        self.cookie, self.channel_n, self.channel_obj, self.sendend, self.lasttxt = None, None, None, None, None
        self.cnx = False
        self.banned_words = BannedWords(banned_words)

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

        if cookie_hash in loult_state.banned_cookies:
            if datetime.now() < loult_state.banned_cookies[cookie_hash]: # if user is shadowmuted, refuse connection
                self.sendClose()
                return None, retn
            else:
                del loult_state.banned_cookies[cookie_hash] # if ban has expired, remove user from banned cookie list

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

    def _handle_automute(self):
        if self.user.state.has_been_warned: # user has already been warned. Shadowmuting him/her and notifying everyone
            self.user.state.is_shadowmuted = True
            self._broadcast_to_channel({'type': 'automute',
                                        'event': 'automuted',
                                        'flooder_id': self.user.user_id,
                                        'date' : time() * 1000})
            loult_state.banned_cookies[self.cookie] = datetime.now() + timedelta(minutes=BAN_TIME)
        else:
            # resets the user's msg log, then warns the user
            self.user.state.last_msgs_timestamps = []
            self.user.state.has_been_warned = True
            self.sendMessage(json({'type': 'automute',
                                   'event': 'flood_warning',
                                   'date': time() * 1000}))
            alarm_sound = self._open_sound_file("tools/data/alerts/alarm.wav")
            self.sendMessage(alarm_sound, isBinary=True)

    def _msg_handler(self, msg_data : Dict):
        # user object instance renders both the output sound and output text
        output_msg, wav = self.user.render_message(msg_data["msg"], msg_data.get("lang", "fr"))

        # message is not sent to the others, but directly to the user
        if self.user.state.is_shadowmuted:
            now = time() * 1000
            self.sendMessage(json({'type': 'msg',
                                   'userid': self.user.user_id,
                                   'msg': output_msg,
                                   'date': now}))
            self.sendMessage(wav, isBinary=True)

        elif (self.user.state.is_flooding or
              self.banned_words(msg_data["msg"])):
            self._handle_automute()

        else:
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

            # add output
            output_msg = add_msg_html_tag(output_msg)
            # send to the backlog
            info = self.channel_obj.log_to_backlog(self.user.user_id, output_msg)

            # broadcast message and rendered audio to all clients in the channel
            self.user.state.log_msg()
            self._broadcast_to_channel({'type': 'msg',
                                        'userid': self.user.user_id,
                                        'msg': output_msg,
                                        'date': info['date']},
                                       wav if synth else None)

    @lru_cache()
    def _open_sound_file(self, relative_path):
        """Sends a wav file from a path relative to the current directory."""
        full_path = path.join(path.dirname(path.realpath(__file__)), relative_path)
        with open(full_path, "rb") as sound_file:
            return sound_file.read()

    def _handle_flooder_attack(self, flooder : User):
        punition_msg = "OH T KI LÀ"
        punition_sound = self._open_sound_file("tools/data/alerts/ohtki.wav")
        now = time() * 1000
        loop = get_event_loop()

        async def punish(flooder, count):
            """
            Yes, it's a recursive asynchronous function.
            If it weren't, this function would stall everything
            until it completes. It's defined here to create a
            closure instead of having to pass many arguments.
            """
            if count > 0 and flooder in self.channel_obj.users.values():
                for client in flooder.clients:
                    client.sendMessage(json({'type': 'msg',
                                             'userid': self.user.user_id,
                                             'msg': punition_msg,
                                             'date': now}))
                    client.sendMessage(punition_sound, isBinary=True)
                loop.create_task(punish(flooder, count - 1))

        # recursion launched here
        loop.create_task(punish(flooder, PUNITIVE_MSG_COUNT))

        self._broadcast_to_channel({'type': 'attack',
                                    'date': now,
                                    'event': 'attack',
                                    'attacker_id': self.user.user_id,
                                    'defender_id': flooder.user_id})
        self._broadcast_to_channel({'type': 'attack',
                                    'date': time() * 1000,
                                    'event': 'effect',
                                    'target_id': flooder.user_id,
                                    'effect': "pillonage"})

    def _attack_handler(self, msg_data : Dict):
        # cleaning up none values in case of fuckups
        msg_data = {key: value for key, value in msg_data.items() if value is not None}

        adversary_id, adversary = self.channel_obj.get_user_by_name(msg_data.get("target",
                                                                                 self.user.poke_params.pokename),
                                                                    msg_data.get("order", 1) - 1)

        # checking if the target user is found, and if the current user has waited long enough to attack
        if adversary is None:
            self.sendMessage(json({'type': 'attack', 'event': 'invalid'}))
        elif datetime.now() - self.user.state.last_attack < timedelta(seconds=ATTACK_RESTING_TIME):
            return
        elif adversary.state.is_shadowmuted:
            # if targeted user is shadowmuted, just bombard him/her with the same message
            self._handle_flooder_attack(adversary)
        else:
            self._broadcast_to_channel({'type': 'attack',
                                        'date': time() * 1000,
                                        'event' : 'attack',
                                        'attacker_id': self.user.user_id,
                                        'defender_id': adversary_id})

            combat_sim = CombatSimulator()
            combat_sim.run_attack(self.user, adversary, self.channel_obj)
            self._broadcast_to_channel({'type': 'attack',
                                        'date': time() * 1000,
                                        'event': 'dice',
                                        'attacker_dice' : combat_sim.atk_dice,
                                        "defender_dice" : combat_sim.def_dice,
                                        'attacker_bonus' : combat_sim.atk_bonus,
                                        "defender_bonus" : combat_sim.def_bonus,
                                        'attacker_id': self.user.user_id, 'defender_id': adversary_id})

            if combat_sim.affected_users: # there are users affected by some effects
                for user, effect in combat_sim.affected_users:
                    self._broadcast_to_channel({'type': 'attack',
                                                'date': time() * 1000,
                                                'event': 'effect',
                                                'target_id': user.user_id,
                                                'effect': effect.name,
                                                'timeout': effect.timeout})
            else: # list is empty, no one was attacked
                self._broadcast_to_channel({'type': 'attack',
                                            'date': time() * 1000,
                                            'event': 'nothing'})

            self.user.state.last_attack = datetime.now()

    def _move_handler(self, msg_data : Dict):
        # checking if all the necessary data is here
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
            self.users[user.user_id].clients.remove(client)

            # if the user is not connected anymore, we signal its disconnect to the others
            if len(self.users[user.user_id].clients) < 1:
                self.clients.discard(client)
                del self.users[user.user_id]

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
            self.users[new_user.user_id] = new_user
            return new_user
        else:
            self.users[new_user.user_id].clients.append(client)
            return self.users[new_user.user_id]  # returning an already existing instance of the user

    def log_to_backlog(self, user_id, msg: str):
        # creating new entry
        info = {
            'user': self.users[user_id].info['params'],
            'msg': msg,
            'date': time() * 1000
        }

        # adding it to list and removing oldest entry
        self.backlog.append(info)
        self.backlog = self.backlog[-10:]
        return info

    def get_user_by_name(self, pokemon_name: str, order=0) -> (int, User):

        for user_id, user in self.users.items():
            if user.poke_params.pokename.lower() == pokemon_name.lower():
                if order <= 0:
                    return user_id, user
                else:
                    order -= 1

        return None, None


class LoultServerState:

    def __init__(self, banned_words=BANNED_WORDS):
        self.chans = {} # type:Dict[str,Channel]
        self.banned_cookies = {} #type:Dict[str,datetime]

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

