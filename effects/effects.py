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

    def process(self, text : str):
        pass


class AudioEffect(Effect):

    def process(self, wave_data: numpy.ndarray):
        pass


#### Here are the text effects ####

class BiteDePingouinEffect(TextEffect):
    """Changes the text to a random number of bitedepingouin"""
    NAME = "bite de pingouin"
    TIMEOUT = 60

    def process(self, text : str):
        return "BITEDEPINGOUIN? " * random.randint(1,6)


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