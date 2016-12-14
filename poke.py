#!/usr/bin/python3
#-*- encoding: Utf-8 -*-
import logging
import random
from asyncio import get_event_loop
from collections import OrderedDict
from colorsys import hsv_to_rgb
from copy import deepcopy
from hashlib import md5
from html import escape
from json import loads, dumps
from os import urandom
from re import sub
from shlex import quote
from struct import pack
from subprocess import run, PIPE
from time import time
from typing import List, Dict, Set
from scipy.io import wavfile
from io import BytesIO
from datetime import datetime, timedelta
from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory

from effects import get_random_effect
from effects.effects import Effect, BiteDePingouinEffect, AudioEffect
from salt import SALT

pokemon = {1:'Bulbizarre',2:'Herbizarre',3:'Florizarre',4:'Salamèche',5:'Reptincel',6:'Dracaufeu',7:'Carapuce',
           8:'Carabaffe',9:'Tortank',10:'Chenipan',11:'Chrysacier',12:'Papilusion',13:'Aspicot',14:'Coconfort',
           15:'Dardargnan',16:'Roucool',17:'Roucoups',18:'Roucarnage',19:'Rattata',20:'Rattatac',21:'Piafabec',
           22:'Rapasdepic',23:'Abo',24:'Arbok',25:'Pikachu',26:'Raichu',27:'Sabelette',28:'Sablaireau',29:'Nidoran♀',
           30:'Nidorina',31:'Nidoqueen',32:'Nidoran♂',33:'Nidorino',34:'Nidoking',35:'Mélofée',36:'Mélodelfe',
           37:'Goupix',38:'Feunard',39:'Rondoudou',40:'Grodoudou',41:'Nosferapti',42:'Nosferalto',43:'Mystherbe',
           44:'Ortide',45:'Rafflesia',46:'Paras',47:'Parasect',48:'Mimitoss',49:'Aéromite',50:'Taupiqueur',
           51:'Triopikeur',52:'Miaouss',53:'Persian',54:'Psykokwak',55:'Akwakwak',56:'Férosinge',57:'Colossinge',
           58:'Caninos',59:'Arcanin',60:'Ptitard',61:'Tétarte',62:'Tartard',63:'Abra',64:'Kadabra',65:'Alakazam',
           66:'Machoc',67:'Machopeur',68:'Mackogneur',69:'Chétiflor',70:'Boustiflor',71:'Empiflor',72:'Tentacool',
           73:'Tentacruel',74:'Racaillou',75:'Gravalanch',76:'Grolem',77:'Ponyta',78:'Galopa',79:'Ramoloss',
           80: 'Flagadoss',81:'Magneti',82:'Magneton',83:'Canarticho',84:'Doduo',85:'Dodrio',86:'Otaria',
           87:'Lamantine',88:'Tadmorv',89:'Grotadmorv',90:'Kokiyas',91:'Crustabri',92:'Fantominus',93:'Spectrum',
           94:'Ectoplasma',95:'Onix',96:'Soporifik',97:'Hypnomade',98:'Krabby',99:'Krabboss',100:'Voltorbe',
           101:'Electrode',102:'Noeunoeuf',103:'Noadkoko',104:'Osselait',105:'Ossatueur',106:'Kicklee',107:'Tygnon',
           108:'Excelangue',109:'Smogo',110:'Smogogo',111:'Rhinocorne',112:'Rhinoféros',113:'Leveinard',
           114:'Saquedeneu',115:'Kangourex',116:'Hypotrempe',117:'Hypocéan',118:'Poissirène',119:'Poissoroy',
           120:'Stari',121:'Staross',122:'Mr.Mime',123:'Insécateur',124:'Lippoutou',125:'Elektek',126:'Magmar',
           127:'Scarabrute',128:'Tauros',129:'Magicarpe',130:'Léviator',131:'Lokhlass',132:'Métamorph',133:'Evoli',
           134:'Aquali',135:'Voltali',136:'Pyroli',137:'Porygon',138:'Amonita',139:'Amonistar',140:'Kabuto',
           141:'Kabutops',142:'Ptéra',143:'Ronflex',144:'Artikodin',145:'Electhor',146:'Sulfura',147:'Minidraco',
           148:'Draco',149:'Dracolosse',150:'Mewtwo',151:'Mew',152:'Germignon',153:'Macronium',154:'Méganium',
           155:'Héricendre',156:'Feurisson',157:'Typhlosion',158:'Kaïminus',159:'Crocrodil',160:'Aligatueur',
           161:'Fouinette',162:'Fouinar',163:'Hoot-hoot',164:'Noarfang',165:'Coxy',166:'Coxyclaque',167:'Mimigal',
           168:'Migalos',169:'Nostenfer',170:'Loupio',171:'Lanturn',172:'Pichu',173:'Mélo',174:'Toudoudou',
           175:'Togépi',176:'Togétic',177:'Natu',178:'Xatu',179:'Wattouat',180:'Lainergie',181:'Pharamp',
           182:'Joliflor',183:'Marill',184:'Azumarill',185:'Simularbre',186:'Tarpaud',187:'Granivol',188:'Floravol',
           189:'Cotovol',190:'Capumain',191:'Tournegrin',192:'Héliatronc',193:'Yanma',194:'Axoloto',195:'Maraiste',
           196:'Mentali',197:'Noctali',198:'Cornebre',199:'Roigada',200:'Feuforêve',201:'Zarbi',202:'Qulbutoke',
           203:'Girafarig',204:'Pomdepic',205:'Foretress',206:'Insolourdo',207:'Scorplane',208:'Steelix',
           209:'Snubbull',210:'Granbull',211:'Qwilfish',212:'Cizayox',213:'Caratroc',214:'Scarhino',215:'Farfuret',
           216:'Teddiursa',217:'Ursaring',218:'Limagma',219:'Volcaropod',220:'Marcacrain',221:'Cochignon',
           222:'Corayon',223:'Remoraid',224:'Octillery',225:'Cadoizo',226:'Demanta',227:'Airmure',228:'Malosse',
           229:'Démolosse',230:'Hyporoi',231:'Phanpy',232:'Donphan',233:'Porygon2',234:'Cerfrousse',235:'Queulorior',
           236:'Débugant',237:'Kapoera',238:'Lippouti',239:'Elekid',240:'Magby',241:'Ecremeuh',242:'Leuphorie',
           243:'Raïkou',244:'Enteï',245:'Suicune',246:'Embrylex',247:'Ymphect',248:'Tyranocif',249:'Lugia',
           250:'Ho-oh',251:'Célébi',252:'Arcko',253:'Massko',254:'Jungko',255:'Poussifeu',256:'Galifeu',
           257:'Brasegali',258:'Gobou',259:'Flobio',260:'Laggron',261:'Medhyena',262:'Grahyena',263:'Zigzaton',
           264:'Lineon',265:'Chenipotte',266:'Armulys',267:'Charmillon',268:'Blindalys',269:'Papinox',270:'Nenupiot',
           271:'Lombre',272:'Ludicolo',273:'Grainipiot',274:'Pifeuil',275:'Tengalice',276:'Nirondelle',
           277:'Heledelle',278:'Goelise',279:'Bekipan',280:'Tarsal',281:'Kirlia',282:'Gardevoir',283:'Arakdo',
           284:'Maskadra',285:'Balignon',286:'Chapignon',287:'Parecool',288:'Vigoroth',289:'Monaflemit',290:'Ningale',
           291:'Ninjask',292:'Munja',293:'Chuchmur',294:'Ramboum',295:'Brouhabam',296:'Makuhita',297:'Hariyama',
           298:'Azurill',299:'Tarinor',300:'Skitty',301:'Delcatty',302:'Tenefix',303:'Mysdibule',304:'Galekid',
           305:'Galegon',306:'Galeking',307:'Meditikka',308:'Charmina',309:'Dynavolt',310:'Elecsprint',311:'Posipi',
           312:'Negapi',313:'Muciole',314:'Lumivole',315:'Roselia',316:'Gloupti',317:'Avaltout',318:'Carvanha',
           319:'Sharpedo',320:'Wailmer',321:'Wailord',322:'Chamallot',323:'Camerupt',324:'Chartor',325:'Spoink',
           326:'Groret',327:'Spinda',328:'Kraknoix',329:'Vibrannif',330:'Libegon',331:'Cacnea',332:'Cacturne',
           333:'Tylton',334:'Altaria',335:'Mangriff',336:'Seviper',337:'Seleroc',338:'Solaroc',339:'Barloche',
           340:'Barbicha',341:'Ecrapince',342:'Colhomar',343:'Balbuto',344:'Kaorine',345:'Lilia',346:'Vacilys',
           347:'Anorith',348:'Armaldo',349:'Barpau',350:'Milobellus',351:'Morpheo',352:'Kecleon',353:'Polichombr',
           354:'Branette',355:'Skelenox',356:'Teraclope',357:'Tropius',358:'Eoko',359:'Absol',360:'Okéoké',
           361:'Stalgamin',362:'Oniglali',363:'Obalie',364:'Phogleur',365:'Kaimorse',366:'Coquiperl',367:'Serpang',
           368:'Rosabyss',369:'Relicanth',370:'Lovdisc',371:'Draby',372:'Drakhaus',373:'Drattak',374:'Terhal',
           375:'Metang',376:'Metalosse',377:'Regirock',378:'Regice',379:'Registeel',380:'Latias',381:'Latios',
           382:'Kyogre',383:'Groudon',384:'Rayquaza',385:'Jirachi',386:'Deoxys',387:'Tortipouss',388:'Boskara',
           389:'Torterra',390:'Ouisticram',391:'Chimpenfeu',392:'Simiabraz',393:'Tiplouf',394:'Prinplouf',
           395:'Pingoleon',396:'Étourmi',397:'Étourvol',398:'Étouraptor',399:'Keunotor',400:'Castorno',401:'Crikzik',
           402:'Melocrik',403:'Lixy',404:'Luxio',405:'Luxray',406:'Rozbouton',407:'Roserade',408:'Kranidos',
           409:'Charkos',410:'Dinoclier',411:'Bastiodon',412:'Cheniti',413:'Cheniselle',414:'Papilord',
           415:'Apitrini',416:'Apireine',417:'Pachirisu',418:'Mustebouée',419:'Musteflott',420:'Ceribou',
           421:'Ceriflor',422:'Sancoki',423:'Tritosor',424:'Capidextre',425:'Baudrive',426:'Grodrive',
           427:'Laporeille',428:'Lockpin',429:'Magirêve',430:'Corboss',431:'Chaglam',432:'Chaffreux',433:'Korillon',
           434:'Moufouette',435:'Moufflair',436:'Archeomire',437:'Archeodong',438:'Manzaï',439:'MimeJr.',
           440:'Ptiravi',441:'Pijako',442:'Spiritomb',443:'Griknot',444:'Carmache',445:'Carchacrok',446:'Goinfrex',
           447:'Riolu',448:'Lucario',449:'Hippopotas',450:'Hippodocus',451:'Rapion',452:'Drascore',453:'Cradopaud',
           454:'Coatox',455:'Vortente',456:'Ecayon',457:'Lumineon',458:'Babimanta',459:'Blizzi',460:'Blizzaroi',
           461:'Dimoret',462:'Magnezone',463:'Coudlangue',464:'Rhinastoc',465:'Bouldeneu',466:'Elekable',
           467:'Maganon',468:'Togekiss',469:'Yanmega',470:'Phyllali',471:'Givrali',472:'Scorvol',473:'Mammochon',
           474:'Porygon-Z',475:'Gallame',476:'Tarinorme',477:'Noctunoir',478:'Momartik',479:'Motisma',
           480:'Crehelf',481:'Crefollet',482:'Crefadet',483:'Dialga',484:'Palkia',485:'Heatran',486:'Regigigas',
           487:'Giratina',488:'Cresselia',489:'Phione',490:'Manaphy',491:'Darkrai',492:'Shaymin',493:'Arceus'}
ATTACK_RESTING_TIME = 1 # in seconds, the time a pokemon has to wait before being able to attack again
# Alias with default parameters
json = lambda obj: dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf8')


class User:
    """Stores a user's state and parameters, which are also used to render the user's audio messages"""
    lang_voices_mapping = {"fr" : ("fr" , (1, 2, 3, 4, 6, 7)),
                           "en" : ("us" , (1, 2, 3)),
                           "es" : ("us" , (1, 2)),
                           "de" : ("de" , (4, 5, 6, 7))}

    volumes_presets = {'us1': 1.658, 'us2': 1.7486, 'us3': 3.48104, 'es1': 3.26885, 'es2': 1.84053}

    def __init__(self, cookie_hash, channel):
        """Initiating a user using its cookie md5 hash"""
        self.speed = (cookie_hash[5] % 50) + 100
        self.pitch = cookie_hash[0] % 100
        self.voice_id = cookie_hash[1]
        self.poke_id = (cookie_hash[2] | (cookie_hash[3] << 8)) % len(pokemon) + 1
        self.pokename = pokemon[self.poke_id]
        self.color = hsv_to_rgb(cookie_hash[4] / 255, 1, 0.5)
        self.color = '#' + pack('3B', *(int(255 * i) for i in self.color)).hex()

        self.user_id = cookie_hash.hex()[-5:]

        self.channel = channel
        self.active_text_effects, self.active_sound_effects = [], []
        self.last_attack = datetime.now() # any user has to wait 1 minute before attacking, after connecting

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
                        effect_list.remove(effect) # if the effect has expired, remove it
                    else:
                        input_obj = effect.process(input_obj)

            return input_obj

        cleaned_text = text[:500]
        cleaned_text = apply_effects(cleaned_text, self.active_text_effects)
        cleaned_text = sub('(https?://[^ ]*[^.,?! :])', 'cliquez mes petits chatons', cleaned_text)
        cleaned_text = cleaned_text.replace('#', 'hashtag ')
        quoted_text = quote(cleaned_text.strip(' -"\'`$();:.'))

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

        # Synthesis & rate limit
        synth_string = 'MALLOC_CHECK_=0 espeak -s %d -p %d --pho -q -v mb/mb-%s%d %s | MALLOC_CHECK_=0 mbrola -v %g -e /usr/share/mbrola/%s%d/%s%d - -.wav' % (
                self.speed, self.pitch, lang, sex, quoted_text, volume, lang, voice, lang, voice)
        logging.debug("Running synth command %s" % synth_string)
        wav = run(synth_string, shell=True, stdout=PIPE, stderr=PIPE).stdout
        wav = wav[:4] + pack('<I', len(wav) - 8) + wav[8:40] + pack('<I', len(wav) - 44) + wav[44:]

        if self.active_sound_effects:
            # converting the wav to ndarray, which is much easier to manipulate for DSP
            rate, data = wavfile.read(BytesIO(wav))
            data = apply_effects(data, self.active_sound_effects)
            # then, converting it back to bytes
            bytes_obj = bytes()
            bytes_buff = BytesIO(bytes_obj)
            wavfile.write(bytes_buff, rate, data)
            wav = bytes_buff.read()

        return cleaned_text, wav


class LoultServer(WebSocketServerProtocol):
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
        self.channel = request.path.lower().split('/', 2)[-1]
        self.cookie = cookie_hash
        self.cnx = False
        self.sendend = 0
        self.lasttxt = 0

        return None, retn

    def onOpen(self):
        """Triggered once the WSS is opened. Mainly onsist of registering the user in the channel, and
        sending the channel's information (connected users and the backlog) to the user"""
        print("WebSocket connection open.")

        # telling the  connected users'register to register the current user in the current channel
        self.user = loult_state.channel_connect(self, self.cookie, self.channel)

        self.cnx = True  # connected!

        # deep-copying the channel's userlist and telling the current JS client which userid is "its own"
        my_userlist = {user_id : user.info for user_id, user in loult_state.users[self.channel].items()}
        my_userlist[self.user.user_id]['params']['you'] = True  # tells the JS client this is the user's pokemon
        # sending the current user list to the client
        self.sendMessage(json({
            'type': 'userlist',
            'users': list(my_userlist.values())
        }))

        self.sendMessage(json({
            'type': 'backlog',
            'msgs': loult_state.backlog[self.channel]
        }))

    def _broadcast_to_channel(self, msg_dict, binary_payload=None):
        for client in loult_state.clients[self.channel]:
            client.sendMessage(json(msg_dict))
            if binary_payload:
                client.sendMessage(binary_payload, isBinary=True)

    def _msg_handler(self, msg_data):
        # user object instance renders both the output sound and output text
        output_msg, wav = self.user.render_message(msg_data["msg"], msg_data.get("lang", "fr"))

        # rate limit
        now = time()

        if now - self.lasttxt <= 0.1:
            return
        self.lasttxt = now

        calc_sendend = max(self.sendend, now)
        calc_sendend += len(wav) * 8 / 6000000

        synth = calc_sendend < now + 2.5
        if synth:
            self.sendend = calc_sendend

        info = loult_state.log_to_backlog(loult_state.users[self.channel][self.user.user_id].info['params'],
                                          output_msg, self.channel)

        # broadcast message and rendered audio to all clients in the channel
        self._broadcast_to_channel({'type': 'msg',
                                    'userid': self.user.user_id,
                                    'msg': info['msg'],
                                    'date': info['date']},
                                   wav if synth else None)

    def _attack_handler(self, msg_data):
        adversary_id, adversary = loult_state.get_user_by_name(msg_data["target"], self.channel, msg_data.get("order", 0))

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
                    affected_user.active_sound_effects.append(effect)
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


    def onMessage(self, payload, isBinary):
        """Triggered when a user receives a message"""
        msg = loads(payload.decode('utf8'))

        if msg['type'] == 'msg':
            # when the message is just a simple text message (regular chat)
            self._msg_handler(msg)

        elif msg["type"] == "attack":
            # when the current client attacks someone else
            self._attack_handler(msg)


    def onClose(self, wasClean, code, reason):
        """Triggered when the WS connection closes. Mainly consists of deregistering the user"""
        if hasattr(self, 'cnx') and self.cnx:
            loult_state.channel_leave(self, self.user, self.channel)

        print("WebSocket connection closed: {0}".format(reason))


class LoultServerState:

    def __init__(self):
        self.clients = {} # type:Dict[str,Set[LoultServer]]
        self.users = {} # type:Dict[str,Dict[str, User]]
        self.refcnts = {} # type:Dict[str, Dict[str,int]]
        self.backlog = {} # type:Dict[str,List]

    def _signal_user_connect(self, client : LoultServer, user : User):
        client.sendMessage(json({
            'type': 'connect',
            **user.info}))

    def channel_connect(self, client : LoultServer, user_cookie : str, channel : str) -> User:
        if channel not in self.clients:
            self.clients[channel] = set()
            self.users[channel] = OrderedDict()
            self.refcnts[channel] = {}

            if channel not in self.backlog:
                self.backlog[channel] = []

        self.clients[channel].add(client)

        new_user = User(user_cookie, channel)
        if new_user.user_id not in self.users[channel]:
            for other_client in self.clients[channel]:
                self._signal_user_connect(other_client, new_user)
            self.refcnts[channel][new_user.user_id] = 1
            self.users[channel][new_user.user_id] = new_user
            return new_user
        else:
            self.refcnts[channel][new_user.user_id] += 1
            return self.users[new_user.user_id] # returning an already existing version of the user


    def _signal_user_disconnect(self, client: LoultServer, user: User):
        client.sendMessage(json({
            'type': 'disconnect',
            'userid': user.user_id
        }))

    def channel_leave(self, client : LoultServer, user : User, channel : str):
        try:
            self.refcnts[channel][user.user_id] -= 1

            if self.refcnts[channel][user.user_id] < 1:
                self.clients[channel].discard(client)
                del self.users[channel][user.user_id]
                del self.refcnts[channel][user.user_id]

                for client in self.clients[channel]:
                    self._signal_user_disconnect(client, user)

                if not self.clients[channel]:
                    del self.clients[channel]
                    del self.users[channel]
                    del self.refcnts[channel]

                    if not self.backlog[channel]:
                        del self.backlog[channel]
        except KeyError:
            pass

    def log_to_backlog(self, user_data, msg, channel):
        # creating new entry
        info = {
            'user': user_data,
            'msg': sub('(https?://[^ ]*[^.,?! :])', r'<a href="\1" target="_blank">\1</a>',
                       escape(msg[:500])),
            'date': time() * 1000
        }

        # adding it to list and removing oldest entry
        self.backlog[channel].append(info)
        self.backlog[channel] = loult_state.backlog[channel][-10:]
        return info


    def get_user_by_name(self, pokemon_name : str, channel : str, order = 0) -> (int, User):

        for user_id, user in self.users[channel].items():
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

