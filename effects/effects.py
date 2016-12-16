import random
from datetime import datetime
from pysndfx import AudioEffectsChain

import numpy


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

class BiteDePingouinEffect(TextEffect):
    """Changes the text to a random number of bitedepingouin"""
    NAME = "bite de pingouin"
    TIMEOUT = 60

    def process(self, displayed_text: str, rendered_text: str):
        new_text = "BITEDEPINGOUIN? " * random.randint(1,6)
        return new_text, new_text


class TouretteEffect(TextEffect):
    """Randomly inserts insults in between words"""
    NAME = "syndrome de tourette"
    TIMEOUT = 120
    available_swears = ["pute", "salope", "chier", "kk", "chienne", "merde", "cul", "bite", "chatte"]

    def process(self, displayed_text : str, rendered_text : str):
        space_splitted = [word for word in rendered_text.split(" ") if word != ""]
        reconstructed = ""
        for word in space_splitted:
            reconstructed += " " + word + " "
            if random.randint(1,6) == 1:
                reconstructed += " ".join([random.choice(self.available_swears)
                                           for i in range(random.randint(1,4))])
        return displayed_text, reconstructed

#### Here are the audio effects ####


class ReversedEffect(AudioEffect):
    NAME = "inversion"
    TIMEOUT = 120

    def process(self, wave_data: numpy.ndarray):
        return wave_data[::-1]


class ReverbManEffect(AudioEffect):
    NAME = "reverbman"
    TIMEOUT = 180

    def process(self, wave_data: numpy.ndarray):
        apply_audio_effects = AudioEffectsChain().reverb(reverberance=100, hf_damping=100)
        return apply_audio_effects(wave_data)