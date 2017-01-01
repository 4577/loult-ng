import io
import random
import wave
from hashlib import md5

import numpy
import pyaudio
from pysndfx import AudioEffectsChain
from scipy.io.wavfile import read, write

from effects.effects import ReversedEffect, AudioEffect, TouretteEffect, \
    SnebwewEffect, GhostEffect, SpeechMasterEffect, NwwoiwwEffect, FofoteEffect, IssouEffect, AmbianceEffect
from effects.tools import mix_tracks
from poke import User
from salt import SALT


class TestEffect(AudioEffect):
    NAME = "test"
    TIMEOUT = 30

    def process(self, wave_data: numpy.ndarray):
        apply_audio_effects = AudioEffectsChain().reverb(reverberance=100, hf_damping=100)
        return apply_audio_effects(wave_data)

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
        with open("effects/data/ambiance/war_mood.wav", "rb") as sndfile:
            rate, track_data = read(sndfile)
        # rnd_pos = random.randint(0,len(track_data) - len(wave_data))
        print(len(track_data))
        return mix_tracks(track_data[rate*3:len(wave_data) + rate*5] * 0.4, wave_data, align="center")


fake_cookie = md5(("622526c6b02ec00669802b3193b39466" + SALT).encode('utf8')).digest()
user = User(fake_cookie, "wesh", None)
user.active_audio_effects += [AmbianceEffect()]
#user.active_text_effects += [FofoteEffect()]

text, wav = user.render_message("Est-ce que ça changerait quelques chose si tu avais la réponse?", "fr")
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