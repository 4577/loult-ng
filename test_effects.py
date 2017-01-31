import io
import logging
import random
import wave
from hashlib import md5

import numpy
import pyaudio
from numpy.lib.function_base import average
from pysndfx import AudioEffectsChain
from scipy.io.wavfile import read

from poke import User
from salt import SALT
from tools.effects import AudioEffect, PhonemicEffect, AutotuneEffect, MwfeEffect, GodSpeakingEffect, WpseEffect, \
    SitcomEffect, TurboHangoul, CrapweEffect, TurfuEffect, StutterEffect, VoiceSpeedupEffect
from tools.phonems import PhonemList, FrenchPhonems
from tools.tools import mix_tracks

logging.getLogger().setLevel(logging.DEBUG)


class TestEffect(AudioEffect):
    NAME = "test"
    TIMEOUT = 30

    def process(self, wave_data: numpy.ndarray):
        low_shelf = AudioEffectsChain().bandreject(80, q=10.0)
        high_shelf = AudioEffectsChain().highpass(150)
        return low_shelf(wave_data)


class Louder(AudioEffect):
    NAME = "test"
    TIMEOUT = 30

    def process(self, wave_data: numpy.ndarray):
        return wave_data * 2


class ConvertINT16PCM(AudioEffect):
    NAME = "convert"
    TIMEOUT = 30

    def process(self, wave_data: numpy.ndarray):
        return (wave_data * (2. ** 15)).astype("int16")


class AddTrackEffect(AudioEffect):
    NAME = "convert"
    TIMEOUT = 30

    def process(self, wave_data: numpy.ndarray):
        with open("tools/data/ambiance/war_mood.wav", "rb") as sndfile:
            rate, track_data = read(sndfile)
        # rnd_pos = random.randint(0,len(track_data) - len(wave_data))
        print(len(track_data))
        return mix_tracks(track_data[rate*3:len(wave_data) + rate*5] * 0.4, wave_data, align="center")


class SpeechDeformation(PhonemicEffect):
    NAME = "un para de trop"
    TIMEOUT = 30

    def process(self, phonems : PhonemList):
        for phonem in phonems:
            if phonem.name in FrenchPhonems.VOWELS and random.randint(1,4) == 1:
                phonem.duration *= 8
                if phonem.pitch_modifiers:
                    orgnl_pitch_avg = average([pitch for pos, pitch in phonem.pitch_modifiers])
                else :
                    orgnl_pitch_avg = 150
                phonem.set_from_pitches_list([orgnl_pitch_avg + ((-1) ** i * 40) for i in range(4)])
        return phonems

fake_cookie = md5(("622526c6b024c0062930283193b39466" + SALT).encode('utf8')).digest()
user = User(fake_cookie, "wesh", None)
for effect in [AutotuneEffect(), VoiceSpeedupEffect()]:
    user.add_effect(effect)

text, wav = user.render_message("Non mais là les mecs faut se détendre si vous voulez sortir moi jme ferais un plaisir de putain de sortir des pédales comme vous parce que putain jreconnais les gars comme vous genre ils sla pètent ouais moi jsais chier debout et tout mais mon gars les mecs qui chient debout arrivent pas a pisser assis et ceux qui pissent assis mon gars c'est des connards qui votent pour daesh aux élections régionales ça c'est avéré jai vécu des trucs dans ma life mon gars tsais meme pas ou ta sexualité se situe", "fr")
# text, wav = user.render_message("ouais ouais ouais on fait les fous ouais on s'enjaille ben poto tu prends à droite direction ta mère moi j'texplique tel que c'est je cherche pas à enrober ma bite de vernis de pute comme certaines pédales du coin là t'as vu ce que tu me racontes ma va chier debout mon gars t'as déjà les chaussures pleinesde merde de ton parcours dans la vie putain tu sais pas à quel point j'ai envie de t'aider frère mais t'es trop con genre tête de con va tu fais le fier mais gars moi je m'en cure le nez", "fr")
print("Text : ", text)

with open("/tmp/effect.wav", "wb") as wavfile:
    wavfile.write(wav)

class AudioFile:
    """A sound player"""
    chunk = 1024

    def __init__(self, file):
        """ Init audio stream """
        self.wf = wave.open(file, 'rb')
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format = self.p.get_format_from_width(self.wf.getsampwidth()),
            channels = self.wf.getnchannels(),
            rate = self.wf.getframerate(),
            output = True
        )

    def play(self):
        """ Play entire file """
        data = self.wf.readframes(self.chunk)
        while data != '':
            self.stream.write(data)
            data = self.wf.readframes(self.chunk)

    def close(self):
        """ Graceful shutdown """
        self.stream.close()
        self.p.terminate()

a = AudioFile(io.BytesIO(wav))
#a = AudioFile("/tmp/effect.wav")
a.play()
a.close()