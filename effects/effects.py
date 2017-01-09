import random
import re
from datetime import datetime
from pysndfx import AudioEffectsChain
from os import path, listdir
from scipy.io.wavfile import read

import numpy

from effects.phonems import PhonemList, Phonem, FrenchPhonems
from .tools import mix_tracks, get_sounds

# TODO : effet théatre, effet speech random, effet beat, effet voix robot,
# effet javanais, effet hangul au hasard


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
    """An effect group is basically a 'meta-effect'. It returns, through the property 'effects' a
    list of already instanciated effect objects, which are all going to be added the a user's effects
    lists. In practice, it's a simple way to have effects that are both on sound, phonems and text.

    Before returning the list of effects, one has to make sure that the effects return by the 'effects' property
    all have the same timeout time as the effect group that returns them. This can be done by setting the optional
    _timeout instance attribute (*NOT* the TIMEOUT class attribute) of an Effect object"""

    _sub_effects = []

    @property
    def effects(self):
        return self._sub_effects


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


class AudioEffect(Effect):

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


class MwfeEffect(ExplicitTextEffect):
    NAME = "YE LA"
    TIMEOUT = 150
    _mwfe_punchlines = [
        "CHU LA",
        "OK BEN NIK TA MER",
        "JGO CHIER",
        "JGO FL",
        "A GERBER WALLAH",
        "YE OU JR",
        "YA QUOI",
        "OUÉVÈWB?"
    ]

    def process(self, text : str):
        if random.randint(0,3) != 0:
            text = text.upper()
            if random.randint(0,4) == 0:
                text = "MDR " + text
        else:
            text = random.choice(self._mwfe_punchlines)
        return text


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


class PhonemicShuffleEffect(PhonemicEffect):
    NAME = "interprète kiglon"
    TIMEOUT = 120

    def process(self, phonems : PhonemList):
        random.shuffle(phonems)
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
            elif phonem.name in FrenchPhonems.CONSONANTS and phonems[i+1].name not in FrenchPhonems.VOWELS:
                reconstructed += [phonem, euh_phonem]
            elif phonem.name == "o":
                phonem.name = "O"
                reconstructed.append(phonem)
            else:
                reconstructed.append(phonem)
        print(str(reconstructed))
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


class CrapweEffect(PhonemicEffect):
    NAME = "crapwe"
    TIMEOUT = 150

    def process(self, phonems: PhonemList):
        for phonem in phonems:
            if phonem.name in FrenchPhonems.VOWELS and random.randint(1, 4) == 1:
                phonem.duration *= 8
                if phonem.pitch_modifiers:
                    orgnl_pitch_avg = numpy.average([pitch for pos, pitch in phonem.pitch_modifiers])
                else:
                    orgnl_pitch_avg = 150
                phonem.set_from_pitches_list([orgnl_pitch_avg + ((-1) ** i * 30) for i in range(4)])

        return phonems


class TurboHangoul(PhonemicEffect):
    NAME = "turbo hangoul"
    TIMEOUT = 150

    def process(self, phonems: PhonemList):
        for phonem in phonems:
            if phonem.name in FrenchPhonems.VOWELS and random.randint(1, 3) == 1:
                phonem.duration *= 8
                phonem.set_from_pitches_list([364, 364])

        return phonems

#### Here are the audio effects ####


class ReversedEffect(AudioEffect):
    """?sdef vlop sdaganliup uirt vlad"""
    NAME = "inversion"
    TIMEOUT = 120

    def process(self, wave_data: numpy.ndarray):
        return wave_data[::-1]


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
        return apply_audio_effects(wave_data)


class GhostEffect(AudioEffect):
    """Adds a ghostly effect"""
    NAME="stalker"
    TIMEOUT = 120

    def process(self, wave_data: numpy.ndarray):
        reverb, reverse = ReverbManEffect(), ReversedEffect()
        return reverse.process(reverb.process(reverse.process(wave_data)))


class IssouEffect(AudioEffect):
    # TODO : refactor plus compact des fonctions sur les deux dossiers différents
    """el famoso"""
    main_dir = path.join(path.dirname(path.realpath(__file__)), "data/issou")
    issou_dir = path.join(main_dir, "issou")
    other_dir = path.join(main_dir, "other")
    NAME = "el famoso"
    TIMEOUT = 120

    def __init__(self):
        super().__init__()

        self.issou_sounds = get_sounds(self.issou_dir)
        self.other_sounds = get_sounds(self.other_dir)
        self.pending_issou, self.pending_other = [], []
        self._create_pattern()

    def _create_pattern(self):
        random.shuffle(self.issou_sounds)
        random.shuffle(self.other_sounds)
        self.pending_other = self.other_sounds[:random.randint(1,3)]
        self.pending_issou = self.issou_sounds[:random.randint(2,4)]

    def process(self, wave_data: numpy.ndarray):
        if random.randint(0,3) == 1:
            if self.pending_other:
                return self.pending_other.pop()
            elif self.pending_issou:
                return self.pending_issou.pop()
            else:
                self._create_pattern()
                return self.process(wave_data)
        else:
            return wave_data


class AmbianceEffect(AudioEffect):
    """Adds a random mood to the audio"""
    NAME = "ambiance"
    TIMEOUT = 180
    effects_mapping = {
        "starwars_mood" : ("lasèw", 0.3),
        "bonfire_mood" : ("les feux de l'amouw", 0.6),
        "seastorm_mood" : ("bretagne", 0.1),
        "war_mood" : ("wesh yé ou ryan ce pd", 0.4),
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
    main_dir = path.join(path.dirname(path.realpath(__file__)), "data/beats/other")
    NAME = "JR"
    TIMEOUT = 150

    def __init__(self):
        super().__init__()
        beat_filename = random.choice(listdir(self.main_dir))
        with open(path.join(self.main_dir, beat_filename), "rb") as sndfile:
            self.rate, self.track = read(sndfile)

    def process(self, wave_data: numpy.ndarray):
        if len(self.track) < len(wave_data):
            beat_track = numpy.tile(self.track, (len(wave_data) // len(self.track)) + 1)
            return mix_tracks(beat_track * 0.4, wave_data, align="center")
        else:
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
        available_words = ["putain", "con", "oh là", "t'es fada"]

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