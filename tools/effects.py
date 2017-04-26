import json
import pickle
import random
from datetime import datetime
from functools import partial
from itertools import cycle
from math import ceil, floor
from os import path, listdir
from typing import List

import numpy
from pysndfx import AudioEffectsChain
from scipy.io.wavfile import read

from tools.melody import chords_ratios, chord_progressions, get_harmonies
from tools.phonems import PhonemList, Phonem, FrenchPhonems
from tools.tools import VoiceParameters
import tools
from tools.audio_tools import mix_tracks, get_sounds


# TODO : effet théatre, effet speech random, effet voix robot,
# effet javanais


class Effect:
    NAME = ""
    TIMEOUT = 0

    def __init__(self):
        self.creation = datetime.now()
        self._timeout = None

    @property
    def timeout(self):
        return self.TIMEOUT if self._timeout is None else self._timeout

    @property
    def name(self):
        return self.NAME # using a property, in case it gets more fancy than just a class constant

    def is_expired(self):
        return (datetime.now() - self.creation).seconds > self.timeout

    def process(self, **kwargs):
        pass


class EffectGroup(Effect):
    """An effect group is basically a 'meta-effect'. It returns, through the property 'tools' a
    list of already instanciated effect objects, which are all going to be added the a user's tools
    lists. In practice, it's a simple way to have tools that are both on sound, phonems and text.

    Before returning the list of tools, one has to make sure that the tools return by the 'tools' property
    all have the same timeout time as the effect group that returns them. This can be done by setting the optional
    _timeout instance attribute (*NOT* the TIMEOUT class attribute) of an Effect object"""

    _sub_effects = []

    @property
    def effects(self) -> List[Effect]:
        return [effect_cls() for effect_cls in self._sub_effects]


class TextEffect(Effect):

    def process(self, text : str) -> str:
        """This function takes text and applies (or not, it's up the dev) alterations to that text"""
        pass


class ExplicitTextEffect(TextEffect):
    """Effect that modifies the text that is rendered AND sent to mbrola"""
    pass


class HiddenTextEffect(TextEffect):
    """Effect that modifies the text before it is sent to mbrola, but the end user doesn't see it"""
    pass


class PhonemicEffect(Effect):
    """Effect that modifies Phonems before they're sent to mbrola"""

    def process(self, phonems : PhonemList) -> PhonemList:
        """"""


class VoiceEffect(Effect):
    """Affects the voice before the audio rendering"""

    def process(self, voice_params : VoiceParameters) -> VoiceParameters:
        pass


class AudioEffect(Effect):
    """Modifies the audio file, after the mbrola rendering"""

    def process(self, wave_data: numpy.ndarray) -> numpy.ndarray:
        pass


#### Here are the text effects ####

class SnebwewEffect(ExplicitTextEffect):
    """Finds, using a simple heuristic, random nouns and changes them to snèbwèw"""
    NAME = "snèbwèw"
    TIMEOUT = 240
    pronouns = ["le", "la", "un", "une", "du", "son", "sa", "mon", "ce", "ma", "cette", "au", "les", "aux", "à",
                "tu", "je", "a"]

    def process(self, text: str):
        splitted = text.split() # fak ye baudrive
        reconstructed = ''
        it = iter(splitted)
        endswith_sneb = False
        for word in it:
            if word:
                reconstructed += word + ' '
                if word.lower() in self.pronouns and random.randint(1,2) == 1:
                    reconstructed += "SNÈBWÈW" + ' '
                    endswith_sneb = True
                    try:
                        next(it)
                    except StopIteration:
                        break
                else:
                    endswith_sneb = False
        if endswith_sneb:
            reconstructed = reconstructed[:-1] + "ENNW"

        return reconstructed


class SpoinkEffect(ExplicitTextEffect):
    NAME = "mme"
    TIMEOUT = 150
    _spoink_punchlines = ["hihihi", "onwww", "jtm", "jvm", "c'est genre hyper irrespectueux", "onwwwwww",
                          "onw pleuwww", "pleplpleplelepelepeleuwww", "peuw", "jtm mr", "t two cwle",
                          "dacowe"]

    def process(self, text : str):
        if random.randint(0, 3) != 0:
            if random.randint(0, 4) == 0:
                text = "hihihihi " + text
        else:
            text = random.choice(self._spoink_punchlines)
        return text


class PoiloEffect(ExplicitTextEffect):
    NAME = "poil au snèbwèw"
    TIMEOUT = 180

    tree_pickle = path.join(path.dirname(path.realpath(__file__)),
                            "data/pwezie/rhyme_tree.pckl")

    article_mapping = {("m", "s") : "au",
                       ("m", "p") : "aux",
                       ("f", "s") : "à la",
                       ("f", "p") : "aux"}

    def __init__(self):
        super().__init__()
        with open(self.tree_pickle, "rb") as pkfile:
            self.rtree = pickle.load(pkfile)

    def process(self, text : str):
        splitted = text.strip("?! ,:").split()
        if splitted:
            rhyme = self.rtree.find_rhyme(text)
            if rhyme is not None:
                if splitted[-1][0] in ["aoeiuyéèê"]:
                    article = "à l'"
                else:
                    try:
                        article = self.article_mapping[(rhyme.data["genre"], rhyme.data["nombre"])]
                    except KeyError:
                        article = "au"
                return text + " poil %s %s" % (article, rhyme.text)

        return text # default to "pass"


class TouretteEffect(HiddenTextEffect):
    """Randomly inserts insults in between words"""
    NAME = "syndrome de tourette"
    TIMEOUT = 120
    available_swears = ["pute", "salope", "chier", "kk", "chienne", "merde", "cul", "bite", "chatte", "suce"]

    def process(self, text: str):
        # the variable is called splitted because it pisses off this australian cunt that mboevink is
        space_splitted = [word for word in text.split(" ") if word != ""]
        reconstructed = ""
        for word in space_splitted:
            reconstructed += " " + word + " "
            if random.randint(1,6) == 1:
                reconstructed += " ".join([random.choice(self.available_swears)
                                           for i in range(random.randint(1,4))])
        return reconstructed


class SpeechMasterEffect(HiddenTextEffect):
    """Increases your speech abilities by 76%"""
    NAME = "maître de l'élocution"
    TIMEOUT = 120
    available_punctuation = "?,!.:'"

    def process(self, text: str):
        space_splitted = [word for word in text.split(" ") if word != ""]
        reconstructed = " ".join([word + random.choice(self.available_punctuation)
                                  for word in space_splitted])
        return reconstructed


#### Here are the phonemic effects ####

class PhonemicNwwoiwwEffect(PhonemicEffect):
    NAME = "nwwoiww"
    TIMEOUT = 150

    def process(self, phonems : PhonemList):
        w_phonem = Phonem("w", 103, [])
        for i, phonem in enumerate(phonems):
            if phonem.name == "R":
                phonem.name = "w"
                if random.randint(0,1) == 0:
                    for j in range(2):
                        phonems.insert(i, w_phonem)
                else:
                    phonem.duration = 206
        return phonems


class PhonemicFofoteEffect(PhonemicEffect):
    NAME = "fofotage"
    TIMEOUT = 150

    def process(self, phonems : PhonemList):
        for phonem in phonems:
            if phonem.name in ["s", "v", "z", "S", "Z"]:
                phonem.name = "f"
        return phonems


class AccentAllemandEffect(PhonemicEffect):
    NAME = "aus meinem Vaterland"
    TIMEOUT = 150
    _tranlation_table = {"Z" : "S", # je -> che
                         "v" : "f", # vous -> fous
                         "b" : "p", # boule -> poule
                         "g" : "k" } # gant -> kan

    def process(self, phonems : PhonemList):
        for phonem in phonems:
            if phonem.name in self._tranlation_table:
                phonem.name = self._tranlation_table[phonem.name]
            elif phonem.name in FrenchPhonems.ORALS and random.randint(1,3) == 1:
                phonem.duration *= 2
            elif phonem.name == "d" and random.randint(1,2) == 1:
                phonem.name = "t"
        return phonems


class AccentMarseillaisEffect(PhonemicEffect):
    NAME = "du vieux port"
    TIMEOUT = 150

    def process(self, phonems: PhonemList):
        reconstructed = PhonemList([])
        ng_phonem = Phonem("N", 100)
        euh_phonem = Phonem("2", 79)
        phonems.append(Phonem("_", 10)) # end-silence-padding, just to be safe
        for i, phonem in enumerate(phonems):
            if phonem.name in FrenchPhonems.NASAL_WOVELS:
                reconstructed += [phonem, ng_phonem]
            elif phonem.name in FrenchPhonems.CONSONANTS - {"w"} and phonems[i+1].name not in FrenchPhonems.VOWELS:
                reconstructed += [phonem, euh_phonem]
            elif phonem.name == "o":
                phonem.name = "O"
                reconstructed.append(phonem)
            else:
                reconstructed.append(phonem)
        return reconstructed


class StutterEffect(PhonemicEffect):
    TIMEOUT = 150
    NAME = "be be te"

    def process(self, phonems : PhonemList):
        silence = Phonem("_", 61)
        reconstructed = PhonemList([])
        for i, phonem in enumerate(phonems):
            if phonems[i].name in FrenchPhonems.CONSONANTS \
                    and phonems[i+1].name in FrenchPhonems.VOWELS \
                    and random.randint(1,3) == 1:
                    reconstructed += [phonems[i], phonems[i+1]] * 2
            elif phonem.name in FrenchPhonems.VOWELS and random.randint(1,3) == 1:
                reconstructed += [phonem, silence, phonem]
            else:
                reconstructed.append(phonem)
        return reconstructed


class VocalDyslexia(PhonemicEffect):
    NAME = "dysclesie vocael"
    TIMEOUT = 150

    def process(self, phonems : PhonemList):

        def permutation(i, j, input_list):
            input_list[i], input_list[j] = input_list[j], input_list[i]

        def double_permutation(i, input_list):
            input_list[i-1], input_list[i], input_list[i+1], input_list[i+2] = \
                input_list[i+1], input_list[i+2], input_list[i-1], input_list[i]
        if len(phonems) > 5:
            permut_count = random.randint(1, len(phonems) // 5) # approx 1 permut/10 phonems
            permut_points = [random.randint(1, len(phonems) - 3) for i in range(permut_count)]
            for point in permut_points:
                permutation(point, point + 1, phonems)

        return phonems


class AutotuneEffect(PhonemicEffect):
    pitch_file = path.join(path.dirname(path.realpath(__file__)), "data/melody/pitches.json")
    NAME = "lou a du talent"
    TIMEOUT = 150

    def __init__(self):
        super().__init__()
        with open(self.pitch_file) as pitch_file:
            self.pitches = json.load(pitch_file)
        self.progression = random.choice(chord_progressions)
        self.octave = 3

    def _get_note(self):
        for chord in cycle(self.progression):
            if chord.endswith("m"):
                note, chord_type = chord.strip("m"), "minor"
            else:
                note, chord_type = chord, "major"

            harmonies_ptich = get_harmonies(self.pitches[note + str(self.octave)], chord_type)
            for _ in range(4):
                yield random.choice(harmonies_ptich)

    def process(self, phonems : PhonemList):
        notes = self._get_note()
        for pho in phonems:
            if pho.name in FrenchPhonems.VOWELS:
                pitch = next(notes)
                pho.set_from_pitches_list([pitch] * 2)
                pho.duration *= 2

        return phonems


class CrapweEffect(PhonemicEffect):
    """Dilates random vowels and modifies the pitch to go up and down"""
    NAME = "crapwe force"
    TIMEOUT = 150

    def __init__(self, intensity=None):
        super().__init__()
        self.intensity = random.randint(1, 4) if intensity is None else intensity
        self._name = self.NAME + " " + str(self.intensity)

    @property
    def name(self):
        return self._name

    def process(self, phonems: PhonemList):
        for phonem in phonems:
            if phonem.name in FrenchPhonems.VOWELS and random.randint(1, 4) >= self.intensity:
                phonem.duration *= 8
                if phonem.pitch_modifiers:
                    orgnl_pitch_avg = numpy.average([pitch for pos, pitch in phonem.pitch_modifiers])
                else:
                    orgnl_pitch_avg = 150
                phonem.set_from_pitches_list([orgnl_pitch_avg + ((-1) ** i * 30) for i in range(4)])

        return phonems


class TurboHangoul(PhonemicEffect):
    NAME = "turbo hangoul force"
    TIMEOUT = 150

    def __init__(self, intensity=None):
        super().__init__()
        self.intensity = random.randint(1,4) if intensity is None else intensity
        self._name = self.NAME + " " + str(self.intensity)

    @property
    def name(self):
        return self._name

    def process(self, phonems: PhonemList):
        for phonem in phonems:
            if phonem.name in FrenchPhonems.VOWELS and random.randint(1, 4) <= self.intensity:
                phonem.duration *= 8
                phonem.set_from_pitches_list([364 - 10, 364])

        return phonems


class GrandSpeechMasterEffect(PhonemicEffect):
    NAME = "grand maître de l'élocution"
    TIMEOUT = 150

    def process(self, phonems: PhonemList):
        for phonem in phonems:
            if phonem.name in FrenchPhonems._all:
                phonem.duration = int(phonem.duration * (random.random() * 4 + 0.7))

        return phonems

#### Here are the voice effets ####

class VoiceSpeedupEffect(VoiceEffect):
    TIMEOUT = 150
    NAME = "en stress"

    def __init__(self):
        super().__init__()
        self.multiplier = random.uniform(1.5, 2.4)

    def process(self, voice_params : VoiceParameters):
        voice_params.speed = int(self.multiplier * voice_params.speed)
        return voice_params


#### Here are the audio effects ####


class ReverbManEffect(AudioEffect):
    """Adds a pretty heavy reverb effect"""
    NAME = "reverbman"
    TIMEOUT = 180

    def __init__(self):
        super().__init__()
        self._name = random.choice(["ouévèwbèw", self.NAME, "lou monastèw"])

    @property
    def name(self):
        return self._name

    def process(self, wave_data: numpy.ndarray):
        wave_data = numpy.concatenate([wave_data, numpy.zeros(16000, wave_data.dtype)])
        apply_audio_effects = AudioEffectsChain().reverb(reverberance=100, hf_damping=100)
        return apply_audio_effects(wave_data, sample_in=16000, sample_out=16000)


class GhostEffect(AudioEffect):
    """Adds a ghostly effect"""
    NAME = "stalker"
    TIMEOUT = 120

    def process(self, wave_data: numpy.ndarray):
        reverb, reverse = ReverbManEffect(), tools.ReversedEffect()
        return reverse.process(reverb.process(reverse.process(wave_data)))


class RobotVoiceEffect(AudioEffect):
    NAME = "13-NRV"
    TIMEOUT = 150

    def process(self, wave_data: numpy.ndarray):
        apply_audio_effects = AudioEffectsChain().pitch(200).tremolo(500).delay(0.6, 0.8, [33],[0.9])
        return apply_audio_effects(wave_data, sample_in=16000, sample_out=16000)

class GaDoSEffect(AudioEffect):
    NAME = "glwe dwse"
    TIMEOUT = 150

    def process(self, wave_data: numpy.ndarray):
        effects_partials = [partial(AudioEffectsChain().pitch(pitch),
                                    sample_in=16000, sample_out=16000)
                            for pitch in [200, 100, -100, -200]]
        reverb = AudioEffectsChain().reverb(reverberance=50, hf_damping=100)

        return reverb(sum([effect(wave_data) for effect in effects_partials]),
                      sample_in=16000, sample_out=16000)

class AmbianceEffect(AudioEffect):
    """Adds a random mood to the audio"""
    NAME = "ambiance"
    TIMEOUT = 180
    effects_mapping = {
        "starwars_mood" : ("lasèw", 0.1),
        "bonfire_mood" : ("les feux de l'amouw", 0.6),
        "seastorm_mood" : ("bretagne", 0.08),
        "war_mood" : ("wesh yé ou ryan ce pd", 0.2),
    }
    data_folder = path.join(path.dirname(path.realpath(__file__)), "data/ambiance/")

    def __init__(self):
        super().__init__()
        filename = random.choice(list(self.effects_mapping.keys()))
        self._name, self.gain = self.effects_mapping[filename]
        with open(path.join(self.data_folder, filename + ".wav"), "rb") as sndfile:
            self.rate, self.track_data = read(sndfile)

    @property
    def name(self):
        return self._name

    def process(self, wave_data: numpy.ndarray):
        padding_time = self.rate * 2
        rnd_pos = random.randint(0,len(self.track_data) - len(wave_data) - padding_time)
        return mix_tracks(self.track_data[rnd_pos:rnd_pos + len(wave_data) + padding_time] * self.gain,
                          wave_data,
                          align="center")


class BeatsEffect(AudioEffect):
    main_dir = path.join(path.dirname(path.realpath(__file__)), "data/beats/")
    NAME = "JR"
    TIMEOUT = 150

    _directories = {"posay" : ["other"],
                    "tape ton para": ["ez3kiel", "outrun", "serbian_film"],
                    "JR" : ["jr"]}

    def __init__(self):
        super().__init__()
        self._name, directories = random.choice(list(self._directories.items()))
        dir = random.choice(directories)
        beat_filename = random.choice(listdir(path.join(self.main_dir, dir)))
        with open(path.join(self.main_dir, dir, beat_filename), "rb") as sndfile:
            self.rate, self.track = read(sndfile)

    @property
    def name(self):
        return self._name

    def process(self, wave_data: numpy.ndarray):
        if len(self.track) < len(wave_data):
            beat_track = numpy.tile(self.track, (len(wave_data) // len(self.track)) + 1)
            return mix_tracks(beat_track * 0.4, wave_data, align="center")
        else:
            return wave_data


class SitcomEffect(AudioEffect):
    main_dir = path.join(path.dirname(path.realpath(__file__)), "data/sitcom")
    _subfolders = ["laugh_track", "boo", "applaud"]
    NAME = "sitcom"
    TIMEOUT = 150

    def __init__(self):
        super().__init__()
        self.tracks = dict()
        for subfolder in self._subfolders:
            self.tracks[subfolder] = get_sounds(path.join(self.main_dir, subfolder))
            # sorting by length
            self.tracks[subfolder].sort(key = lambda s: len(s))

    def find_nearest(self, track_list, value):
        nearest_bigger_index = next((i for i, x in enumerate(track_list) if len(x) > value), None)
        return nearest_bigger_index - 1 if nearest_bigger_index > 0 else 0

    def process(self, wave_data: numpy.ndarray):
        if random.randint(0,1):
            randoum = random.randint(1, 3)
            if randoum == 1:
                wave_data = numpy.concatenate((wave_data, random.choice(self.tracks["laugh_track"])))
            elif randoum == 2:
                wave_data = numpy.concatenate((wave_data, random.choice(self.tracks["applaud"])))
            elif randoum == 3:
                boo_track_id = self.find_nearest(self.tracks["boo"], len(wave_data))
                wave_data = mix_tracks(wave_data, self.tracks["boo"][boo_track_id], align="right")

        return wave_data


class WpseEffect(AudioEffect):
    main_dir = path.join(path.dirname(path.realpath(__file__)), "data/maturity")
    subfolders = ["burps", "prout"]
    NAME = "c pas moi lol"
    TIMEOUT = 130

    def __init__(self):
        super().__init__()
        self.type_folder = random.choice(self.subfolders)
        self.samples = get_sounds(path.join(self.main_dir, self.type_folder))

    def process(self, wave_data: numpy.ndarray):
        if random.randint(1,2) == 1:
            sample = random.choice(self.samples) * 0.3
            if self.type_folder == "burps":
                wave_data = numpy.insert(wave_data, random.randint(1,len(wave_data)), sample)
            else:
                wave_data = mix_tracks(wave_data, sample, offset=random.randint(1,len(wave_data)))

        return wave_data


class WpseEffectTwo(AudioEffect):
    main_dir = path.join(path.dirname(path.realpath(__file__)), "data/burps")
    NAME = "élite du web"
    TIMEOUT = 130

    def __init__(self):
        super().__init__()
        self.samples = get_sounds(self.main_dir)

    def process(self, wave_data: numpy.ndarray):
        if random.randint(1, 2) == 1:
            sample = random.choice(self.samples) * 0.3

        return wave_data

#### Here are the effects groups ####


class VenerEffect(EffectGroup):
    TIMEOUT = 120
    NAME = "YÉ CHAUD"
    _sound_file = path.join(path.dirname(path.realpath(__file__)),
                            "data/vener/stinkhole_shave_me_extract.wav")

    class UPPERCASEEffect(ExplicitTextEffect):
        TIMEOUT = 120

        def process(self, text : str):
            return text.upper()

    @property
    def effects(self):
        monkey_patched = AmbianceEffect()
        monkey_patched._timeout = 120
        monkey_patched.gain = 0.2
        with open(self._sound_file, "rb") as sndfile:
            monkey_patched.rate, monkey_patched.track_data = read(sndfile)
        return [self.UPPERCASEEffect(), monkey_patched]


class VieuxPortEffect(EffectGroup):
    TIMEOUT = 150
    NAME = "du vieux port"

    class VieuxPortInterjections(HiddenTextEffect):
        """Kinda like a tourette effect, but but just a couple of southern interjections"""
        TIMEOUT = 150
        available_words = ["putain", "con", "bonne mère", "t'es fada", "peuchère"]

        def process(self, text: str):
            # the variable is called splitted because it pisses off this australian cunt that mboevink is
            space_splitted = [word for word in text.split(" ") if word != ""]
            reconstructed = ""
            for word in space_splitted:
                reconstructed += " " + word + " "
                if random.randint(1, 6) == 1:
                    reconstructed += ", %s ," % random.choice(self.available_words)
            if random.randint(1,3) == 1:
                reconstructed += ", %s" % random.choice(self.available_words)
            return reconstructed

    @property
    def effects(self):
        southern_accent = AccentMarseillaisEffect()
        southern_accent._timeout = 150
        return [southern_accent, self.VieuxPortInterjections()]


class MwfeEffect(EffectGroup):
    NAME = "YE LA"
    TIMEOUT = 150

    class TextMwfeEffect(ExplicitTextEffect):
        TIMEOUT = 150

        _mwfe_punchlines = ["CHU LA", "OK BEN NIK TA MER", "JGO CHIER", "JGO FL", "PUTT 1 1 1 1 1 1 COUZ 1 1 1 1 1 1",
                            "A GERBER WALLAH", "YE OU JR", "YA QUOI", "OUÉVÈWB?", "PK LA VIE"]

        def process(self, text: str):
            if random.randint(0, 3) != 0:
                text = text.upper()
                if random.randint(0, 4) == 0:
                    text = random.choice(["MDR ", "WESH "]) + text
            else:
                text = random.choice(self._mwfe_punchlines)
            return text

    class VoiceMwfeEffect(VoiceEffect):
        TIMEOUT = 150

        def process(self, voice_params : VoiceParameters):
            return VoiceParameters(speed=110, pitch=60, voice_id=7)

    _sub_effects = [TextMwfeEffect, VoiceMwfeEffect]


class GodSpeakingEffect(EffectGroup):
    TIMEOUT = 120
    NAME = "gode mode"
    _sound_file = path.join(path.dirname(path.realpath(__file__)),
                            "data/godspeaking/godspeaking.wav")

    @property
    def effects(self):
        monkey_patched = AmbianceEffect()
        monkey_patched._timeout = 120
        monkey_patched.gain = 0.4
        with open(self._sound_file, "rb") as sndfile:
            monkey_patched.rate, monkey_patched.track_data = read(sndfile)
        return [ReverbManEffect(), monkey_patched]


class TurfuEffect(EffectGroup):
    TIMEOUT = 150
    NAME = "du turfu"

    @property
    def effects(self):
        hangoul, crapw = TurboHangoul(4), CrapweEffect(4)
        hangoul._timeout = 150
        crapw._timeout = 150
        return [hangoul, crapw]
