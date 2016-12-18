import random
import re
from datetime import datetime
from pysndfx import AudioEffectsChain

import numpy

# TODO : effet théatre, effet speech par adolf, effet beat, effet voix robot

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

    def process(self, displayed_text : str, rendered_text : str):
        """The displayed text is the text sent to the chat, the rendered_text goes through mbrola"""
        pass


class AudioEffect(Effect):

    def process(self, wave_data: numpy.ndarray):
        pass



#### Here are the text effects ####

class SnebwewEffect(TextEffect):
    """Finds, using a simple heuristic, radom nouns and changes then to snèbwèw"""
    NAME = "snèbwèw"
    TIMEOUT = 180
    pronouns = ["le", "la", "un", "une", "du", "son", "sa", "mon", "ce", "ma", "cette", "au", "les", "aux", "à"]

    def process(self, displayed_text: str, rendered_text: str):
        splitted = rendered_text.split(' ') # fak ye baudrive
        reconstructed = ''
        it = iter(splitted)
        endswith_sneb = False
        for word in it:
            if word:
                reconstructed += word + ' '
                if word in self.pronouns and random.randint(1,2) == 1:
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

        return reconstructed, reconstructed


class TouretteEffect(TextEffect):
    """Randomly inserts insults in between words"""
    NAME = "syndrome de tourette"
    TIMEOUT = 120
    available_swears = ["pute", "salope", "chier", "kk", "chienne", "merde", "cul", "bite", "chatte"]

    def process(self, displayed_text : str, rendered_text : str):
        # the variable is called splitted because it pisses off this australian cunt that mboevink is
        space_splitted = [word for word in rendered_text.split(" ") if word != ""]
        reconstructed = ""
        for word in space_splitted:
            reconstructed += " " + word + " "
            if random.randint(1,6) == 1:
                reconstructed += " ".join([random.choice(self.available_swears)
                                           for i in range(random.randint(1,4))])
        return displayed_text, reconstructed

class SpeechMasterEffect(TextEffect):
    """Increases your speech abilities by 76%"""
    NAME = "maître de l'élocution"
    TIMEOUT = 120
    available_punctuation = "?,!.:'"

    def process(self, displayed_text: str, rendered_text: str):
        space_splitted = [word for word in rendered_text.split(" ") if word != ""]
        reconstructed = " ".join([word + random.choice(self.available_punctuation)
                                  for word in space_splitted])
        return displayed_text, reconstructed

class NwwoiwwEffect(TextEffect):
    NAME = "nwwoiww"
    TIMEOUT = 150

    def process(self, displayed_text : str, rendered_text : str):
        replaced = re.sub("r", "ww", rendered_text)
        return replaced, replaced

#### Here are the audio effects ####


class ReversedEffect(AudioEffect):
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