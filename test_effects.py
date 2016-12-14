import pyaudio
import io
import wave
from hashlib import md5

from effects.effects import ReversedEffect
from poke import User
from salt import SALT

fake_cookie = md5(("622536c6b02ec00669802b3193b39466" + SALT).encode('utf8')).digest()
user = User(fake_cookie, "wesh")
user.active_sound_effects.append(ReversedEffect())

text, wav = user.render_message("est-ce que ça changerait quelques chose si tu avais la réponse", "fr")

# open the file for reading.
wf = wave.open(io.BytesIO(wav), 'rb')

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
a.play()
a.close()