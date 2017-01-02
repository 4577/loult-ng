import random
import re
from datetime import datetime
from pysndfx import AudioEffectsChain
from os import path, listdir
from scipy.io.wavfile import read

import numpy

from .tools import mix_tracks

# TODO : effet théatre, effet speech random, effet beat, effet voix robot,
# effet javanais, cheveux sur la langue, effet hangul au hasard


class Effect:
    NAME = ""
    TIMEOUT = 0

    def __init__(self):
        self.creation = datetime.now()

    @property
    def name(self):
        return self.NAME # using a property, in case it gets more fancy than just a class constant

    def is_expired(self):
        return (datetime.now() - self.creation).seconds > self.TIMEOUT

    def process(self, **kwargs):
        pass


class TextEffect(Effect):

    def process(self, text : str):
        """The displayed text is the text sent to the chat, the rendered_text goes through mbrola"""
        pass


class ExplicitTextEffect(TextEffect):
    """Effect that modifies the text that is rendered AND sent to mbrola"""
    pass


class HiddenTextEffect(TextEffect):
    """Effect that modifies the text before it is sent to mbrola, but the end user doesn't see it"""
    pass


class PhonemicEffect(Effect):
    """Effect that modifies Phonems before they're sent to mbrola"""
    pass


class AudioEffect(Effect):

    def process(self, wave_data: numpy.ndarray):
        pass


#### Here are the text effects ####

class SnebwewEffect(ExplicitTextEffect):
    """Finds, using a simple heuristic, random nouns and changes then to snèbwèw"""
    NAME = "snèbwèw"
    TIMEOUT = 180
    pronouns = ["le", "la", "un", "une", "du", "son", "sa", "mon", "ce", "ma", "cette", "au", "les", "aux", "à",
                "tu", "je"]

    def process(self, text: str):
        splitted = text.split(' ') # fak ye baudrive
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
        return text


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


class NwwoiwwEffect(ExplicitTextEffect):
    """Donne un accent cwéole"""
    NAME = "nwwoiww"
    TIMEOUT = 150

    def process(self, text: str):
        return re.sub("r", "ww", text, flags=re.I)


class FofoteEffect(ExplicitTextEffect):
    """Fait un peu fofoter"""
    NAME = "fofotage"
    TIMEOUT = 150

    def process(self, text: str):
        return re.sub("(s|ss|c|ç)", "f", text, flags=re.I)


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
    TIMEOUT = 150

    def __init__(self):
        super().__init__()

        def get_sounds(dir : str):
            sounds = []
            for filename in listdir(dir):
                realpath = path.join(dir, filename)
                rate, data = read(realpath)
                sounds.append(data)
            return sounds

        self.issou_sounds = get_sounds(self.issou_dir)
        self.other_sounds = get_sounds(self.other_dir)
        self.pending_issou, self.pending_other = [], []
        self._create_pattern()

    def _create_pattern(self):
        random.shuffle(self.issou_sounds)
        random.shuffle(self.other_sounds)
        self.pending_other = self.other_sounds[:random.randint(4,6)]
        self.pending_issou = self.issou_sounds[:random.randint(2,5)]

    def process(self, wave_data: numpy.ndarray):
        if self.pending_other:
            return self.pending_other.pop()
        elif self.pending_issou:
            return self.pending_issou.pop()
        else:
            self._create_pattern()
            return self.process(None)


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