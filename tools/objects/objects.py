from datetime import datetime
import random
import re
from os import path, listdir
from time import time as timestamp

from tools.effects.effects import ExplicitTextEffect, GrandSpeechMasterEffect, StutterEffect, VocalDyslexia, \
    VowelExchangeEffect
from tools.objects.base import ClonableObject, InertObject, UsableObject, DestructibleObject, TargetedObject, \
    userlist_dist
from tools.tools import cached_loader

DATA_PATH = path.join(path.dirname(path.realpath(__file__)), "data")


class DiseaseObject(ClonableObject, InertObject):

    DISEASES = ["syphilis", "diarrhée", "chaude-pisse", "gripe aviaire"]

    def __init__(self, patient_zero, disease=None):
        if disease is None:
            self.disease = random.choice(self.DISEASES)
        self.patient_zero = patient_zero

    @property
    def name(self):
        return "la %s de %s" % (self.disease, self.patient_zero)


class Flower(InertObject):
    FLOWERS = ["rose", "lys blanc", "iris", "chrysanthème", "oeillet", "jonquille", "muguet",
               "tulipe", "orchidée"]

    def __init__(self):
        self.flower_name = random.choice(self.FLOWERS)

    @property
    def name(self):
        return self.flower_name


class SimpleInstrument(UsableObject):
    SND_DIR = path.join(DATA_PATH, "instruments/")
    INSTRUMENTS_MAPPING = {"gong": "gong.mp3"}
    COOLDOWN = 30 # in seconds

    def __init__(self, instrument=None):
        if instrument is None:
            instrument = random.choice(list(self.INSTRUMENTS_MAPPING.keys()))

        self.instrument_name = instrument.capitalize()
        self.fx_filepath = path.join(self.SND_DIR, self.INSTRUMENTS_MAPPING[instrument])
        self.last_used = datetime(1972, 1, 1)

    @property
    def name(self):
        return self.instrument_name

    def use(self, loult_state, server, obj_params):
        if (datetime.now() - self.last_used).seconds < self.COOLDOWN:
            return

        server.channel_obj.broadcast(binary_payload=self._load_byte(self.fx_filepath))
        self.last_used = datetime.now()


class BaseballBat(UsableObject, DestructibleObject):
    FIGHTING_FX_DIR = path.join(DATA_PATH, "fighting/")

    def __init__(self, target_userid, target_username):
        super().__init__()
        self.target_name = target_username
        self.target_userid = target_userid
        self.remaining_hits = random.randint(5, 15)
        self.sounds = []
        for filename in listdir(self.FIGHTING_FX_DIR):
            realpath = path.join(self.FIGHTING_FX_DIR, filename)
            self.sounds.append(cached_loader.load_byte(realpath))
    
    @property
    def name(self):
        return "Batte pour frapper %s" % self.target_name

    def use(self, loult_state, server, obj_params):
        # checking if target user is present, sending a notif and a sound
        if self.target_userid in server.channel_obj.users:
            server.channel_obj.broadcast(type="notification",
                                         msg="%s donne un coup de batte à %s"
                                             % (server.user.poke_params.fullname, self.target_name),
                                         binary_payload=random.choice(self.sounds))
            self.remaining_hits -= 1
        else:
            server.send_json(type="notification",
                             msg="Cette batte ne sert qu'à taper %s" % self.target_name)

        # if it's the last hit, notifying and destroying the object
        if self.remaining_hits <= 0:
            self.should_be_destroyed = True
            server.channel_obj.broadcast(type="notification",
                                         msg="%s a cassé sa batte sur %s"
                                             % (server.user.poke_params.fullname, self.target_name))


class Crown(UsableObject, DestructibleObject):
    NAME = "Couronne du loult"

    class ServantEffect(ExplicitTextEffect):
        TIMEOUT = 300
        SUFFIXES = ["seigneur %s", "maître %s", "mon roi", "mon bon %s", "ô grand %s", "sire %s"]

        def __init__(self, pokename):
            super().__init__()
            self.suffixes = [suff % pokename if "%s" in suff else suff for suff in self.SUFFIXES]

        def process(self, text: str):
            return text.strip("!,.:?") + ", " + random.choice(self.suffixes)

    def use(self, loult_state, server, obj_params):
        for user in server.channel_obj.users.values():
            if user is not server.user:
                user.state.add_effect(self.ServantEffect(server.user.poke_params.pokename))
        server.channel_obj.broadcast(type="notification",
                                     msg="%s est maintenant le roi du loult" % server.user.poke_params.fullname)
        self.should_be_destroyed = True


class MagicWand(UsableObject, TargetedObject):
    NAME = "Baguette Magique"
    COOLDOWN = 15 * 60 # in seconds

    class DuckEffect(ExplicitTextEffect):
        TIMEOUT = 300

        def process(self, text : str):
            return re.sub(r"[\w]+","qurk", text)

    def __init__(self):
        self.last_used = datetime(1972, 1, 1)

    def use(self, loult_state, server, obj_params):
        if (datetime.now() - self.last_used).seconds < self.COOLDOWN:
            return server.send_json(type="notification",
                                    msg="Plus de mana dans la baguette, il faut attendre!")

        target_id, target = self._acquire_target(server, obj_params)
        if target is None:
            return
        server.channel_obj.broadcast(type="notification",
                                     msg="%s s'est fait changer en canard" % target.poke_params.fullname)

        target.state.add_effect(self.DuckEffect())
        params = target.poke_params
        params.img_id = "qurk"
        params.pokename = "Qurkee"
        target._info = None
        server.channel_obj.update_userlist()


        self.last_used = datetime.now()


class Scolopamine(UsableObject, DestructibleObject, TargetedObject):
    NAME = "Scolopamine"

    def use(self, loult_state, server, obj_params):
        target_id, target = self._acquire_target(server, obj_params)
        if target is None:
            return

        server.user.state.inventory.objects += target.state.inventory.objects
        target.state.inventory.objects = []
        target.state.add_effect(GrandSpeechMasterEffect())

        server.channel_obj.broadcast(type="notification",
                                     msg="%s a drogué %s et puis a piqué tout son inventaire!"
                                         % (server.user.poke_params.fullname, target.poke_params.fullname))
        self.should_be_destroyed = True


class WhiskyBottle(UsableObject, DestructibleObject, TargetedObject):
    NAME = "Bouteille de whisky"
    EFFECTS = [GrandSpeechMasterEffect, StutterEffect, VocalDyslexia, VowelExchangeEffect]
    FILLING_MAPPING = {0: "vide", 1: "presque vide", 2: "moitié vide",
                       3: "presque pleine", 4: "pleine"}
    BOTTLE_FX = path.join(DATA_PATH, "broken_bottle.mp3")
    GULP_FX = path.join(DATA_PATH, "gulp.mp3")

    def __init__(self):
        super().__init__()
        self.remaining_use = 4

    @property
    def name(self):
        return self.NAME + " (%s)" % self.FILLING_MAPPING[self.remaining_use]

    def use(self, loult_state, server, obj_params):
        # user decides to use it on someone else, meaning throwing it
        if obj_params:
            target_id, target = self._acquire_target(server, obj_params)
            if target is None:
                return

            target_dist = userlist_dist(server.channel_obj, server.user.user_id, target_id)
            if target_dist > 1:
                return server.send_json(type="notification",
                                        msg="Trop loin pour lancer la bouteille dessus!")

            server.channel_obj.broadcast(type="notification",
                                         msg="%s lance une bouteille de whisky sur %s"
                                             % (server.user.poke_params.fullname, target.poke_params.fullname),
                                         binary_payload=self._load_byte(self.BOTTLE_FX))
            for client in target.clients:
                client.sendClose(code=4006, reason='Reconnect please')
            self.should_be_destroyed = True
        else:
            if self.remaining_use <= 0:
                return server.send_json(type="notification",
                                        msg="La bouteille est vide!")
            server.channel_obj.broadcast(type="notification",
                                         msg="%s se descend du whisky!" % server.user.poke_params.fullname,
                                         binary_payload=self._load_byte(self.GULP_FX))
            for effect_type in self.EFFECTS:
                server.user.state.add_effect(effect_type())
            self.remaining_use -= 1


class PolynectarPotion(UsableObject, DestructibleObject, TargetedObject):
    NAME = "potion polynectar"

    def use(self, loult_state, server, obj_params):
        target_id, target = self._acquire_target(server, obj_params)
        if target is None:
            return

        server.channel_obj.broadcast(type="notification",
                                     msg="%s a pris l'apparence de %s!"
                                         % (server.user.poke_params.fullname, target.poke_params.fullname))
        usr = server.user
        usr.poke_params = target.poke_params
        usr.voice_params = target.voice_params
        usr.poke_profile = target.poke_profile
        usr._info = None
        server.channel_obj.update_userlist()
        self.should_be_destroyed = True


class Microphone(UsableObject):
    MIKEDROP_FX = path.join(DATA_PATH, "mikedrop.mp3")
    NAME = 'micro'

    def use(self, loult_state, server, obj_params):
        server.channel_obj.broadcast(type="notification",
                                     msg="%s drop le mike!" % server.user.poke_params.fullname,
                                     binary_payload=self._load_byte(self.MIKEDROP_FX))
        for client in server.user.clients:
            client.sendClose(code=4006, reason='Mike drop, bitch')


class C4(InertObject):
    NAME = "C4"


class Detonator(UsableObject):
    NAME = "Détonateur"
    EXPLOSION_FX = path.join(DATA_PATH, "explosion.mp3")

    def use(self, loult_state, server, obj_params):
        blown_up_users = []
        for user in server.channel_obj.users.values():
            if user.state.inventory.search_by_class(C4):
                user.state.inventory.remove_by_class(C4)
                for client in user.clients:
                    client.sendClose(code=4006, reason='reconnect later')
                blown_up_users.append(user.poke_params.fullname)
        if blown_up_users:
            server.channel_obj.broadcast(type="notification",
                                         msg="%s a fait sauter %s!"
                                             % (server.user.poke_params.fullname, ", ".join(blown_up_users)),
                                         binary_payload=self._load_byte(self.EXPLOSION_FX))


class SuicideJacket(UsableObject, DestructibleObject):
    NAME = "ceinture d'explosif"
    EXPLOSION_FX = path.join(DATA_PATH, "suicide_bomber.mp3")

    def use(self, loult_state, server, obj_params):
        hit_usrs = [usr for usr in server.channel_obj.users.values()
                    if userlist_dist(server.channel_obj, server.user.user_id, usr.user_id) < 3
                    and usr is not server.user]
        server.channel_obj.broadcast(type="notification",
                                     msg="%s s'est fait sauter, emportant avec lui %s"
                                         % (server.user.poke_params.fullname
                                            , ", ".join([usr.poke_params.fullname for usr in hit_usrs])),
                                     binary_payload=self._load_byte(self.EXPLOSION_FX))
        for user in hit_usrs:
            for client in user.clients:
                client.sendClose(code=4006, reason="Reconnect please")
        server.channel_obj.broadcast(type='antiflood', event='banned',
                                     flooder_id=server.user.user_id,
                                     date=timestamp() * 1000)
        loult_state.ban_cookie(server.user.cookie_hash)
        for client in server.user.clients:
            client.sendClose(code=4006, reason='reconnect later')
        self.should_be_destroyed = True


class Costume(UsableObject):
    NAME = "costume"
    CHARACTERS = ["link", "mario", "wario", "sonic"]

    def __init__(self):
        self.character = random.choice(self.CHARACTERS) # type:str

    @property
    def name(self):
        return self.NAME + " de %s" % self.character.capitalize()

    def use(self, loult_state, server, obj_params):
        if hasattr(server.user, "costume") and server.user.costume == self.character:
            return server.send_json(type="notification",
                                    msg="Vous ne pouvez pas enfiler deux fois d'affilée le costume!")

        server.channel_obj.broadcast(type="notification",
                                     msg="%s enfile un costume de %s"
                                         % (server.user.poke_params.fullname, self.character.capitalize()))
        params = server.user.poke_params
        params.img_id = self.character
        params.pokename = self.character.capitalize()
        server.user._info = None
        server.user.costume = self.character
        server.channel_obj.update_userlist()


class RectalExam(UsableObject, TargetedObject, DestructibleObject):
    NAME = "examen rectal"

    def use(self, loult_state, server, obj_params):
        target_id, target = self._acquire_target(server, obj_params)
        if target is None:
            return

        from ..objects import get_random_object
        rdm_objects = [get_random_object() for _ in range(random.randint(2,4))]
        for obj in rdm_objects:
            server.user.state.inventory.add(obj)
        names_list = ", ".join(obj.name for obj in rdm_objects)

        if target is server.user:
            msg = "%s a sorti %s de son cul!" % (server.user.poke_params.fullname, names_list)
        else:
            msg = "%s fouille dans le cul de %s et trouve %s! " \
                  % (server.user.poke_params.fullname, target.poke_params.fullname, names_list)

        server.channel_obj.broadcast(type="notification", msg=msg)
        self.should_be_destroyed = True


class WealthDetector(UsableObject, TargetedObject):
    NAME = "détecteur de richesse"
    
    def use(self, loult_state, server, obj_params):
        target_id, target = self._acquire_target(server, obj_params)
        if target is None:
            return

        server.channel_obj.broadcast(type="notification",
                                     msg="%s utilise le détecteur de richesse sur %s"
                                         % (server.user.poke_params.fullname, target.poke_params.fullname))
        server.send_json(type="notification",
                         msg="%s a %i objets dans son inventaire"
                             % (target.poke_params.fullname, len(target.state.inventory.objects)))


class Cigarettes(UsableObject, DestructibleObject):
    NAME = "cigarettes"
    BRANDS = ["Lucky Loult", "Lucky Loult Menthol", "Mrleboro", "Chesterfnre", "Sheitanes Maïs",
              "Aguloises"]
    CIG_FX = path.join(DATA_PATH, "cigarette_lighting.mp3")

    def __init__(self):
        super().__init__()
        self.brand = random.choice(self.BRANDS)
        self.cigarettes = 20

    @property
    def name(self):
        return self.brand + " (%i)" % self.cigarettes

    @property
    def destroy(self):
        return self.cigarettes <= 0

    def use(self, loult_state, server, obj_params):
        if not server.user.state.inventory.search_by_class(Lighter):
            return server.send_json(type="notification",
                                    msg="Il vous faut un briquet pour pouvoir allumer une clope!")

        self.cigarettes -= 1
        server.channel_obj.broadcast(type="notification",
                                     msg="%s allume une clope et prend un air cool"
                                         % server.user.poke_params.fullname,
                                     binary_payload=self._load_byte(self.CIG_FX))
        if random.randint(1, 10) == 1:
            server.channel_obj.broadcast(type="notification",
                                         msg="%s choppe le cancer et meurt sur le champ!"
                                             % server.user.poke_params.fullname)
            for client in server.user.clients:
                client.sendClose(code=4006, reason="Reconnect please.")


class Lighter(UsableObject):
    NAME = "briquet"
    COOLDOWN = 30 # in seconds
    CIG_FX = path.join(DATA_PATH, "lighter.mp3")

    def __init__(self):
        self.last_use = datetime(1972, 1, 1)

    def use(self, loult_state, server, obj_params):
        if (datetime.now() - self.last_use).seconds < self.COOLDOWN:
            return
        server.channel_obj.broadcast(binary_payload=self._load_byte(self.CIG_FX))
        self.last_use = datetime.now()


class MollyChute(UsableObject, DestructibleObject):
    NAME = "paras de MD"

    class LoveEffect(ExplicitTextEffect):
        NAME = "un paras"
        love_sentence = ["Attendez je vais kiffer le son là",
                         "J'ai envie de vous faire un calin à tous",
                         "Je peux t'embrasser %s?",
                         "Vous êtes tous vraiment trop sympa en fait",
                         "C'est tout doux quand je te caresse les cheveux %s",
                         "Arrêtez de vous dire des trucs méchants moi je vous aime tous",
                         "Franchement le monde est trop beau",
                         "T'es vraiment trop sympa en fait %s",
                         "C'est vraiment la plus belle soirée de ma vie"]
        TIMEOUT = 300

        def __init__(self, users_names):
            super().__init__()
            self.users = users_names

        def process(self, text: str):
            if random.randint(1, 3) == 1:
                sentence = random.choice(self.love_sentence)
                if "%s" in sentence:
                    return sentence % random.choice(self.users)
                else:
                    return sentence
            else:
                return text

    def use(self, loult_state, server, obj_params):
        efct = self.LoveEffect([usr.poke_params.pokename for usr in server.channel_obj.users.values()])
        server.user.state.add_effect(efct)
        server.channel_obj.broadcast(type="notification",
                                     msg="%s prend de la MD!" % server.user.poke_params.fullname)
        self.should_be_destroyed = True
