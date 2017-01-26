import logging
import re
from html import escape
from io import BytesIO
from os import listdir, path
from struct import pack
from subprocess import PIPE, run
from typing import List, Union

import numpy
from numpy.lib import pad
from scipy.io import wavfile
from scipy.io.wavfile import read

from tools.phonems import PhonemList, Phonem

import re

class ToolsError(Exception):
    pass


def mix_tracks(track1, track2, offset=None, align=None):
    """Function that mixes two tracks of unequal lengths(represented by numpy arrays) together,
    using an 'align' or an offset. Zero padding is added to the smallest track as to make it fit.

    if offset is defined:
    longest track :  [=============================]
    smallest track : [0000000][================][00]
                      offset
    or
    longest track :  [=============================][00]
    smallest track : [000000000000000][================]
                          offset

    if align is defined:
    left:
    longest track :  [=============================]
    smallest track : [=====================][000000]

    right:
    longest track :  [=============================]
    smallest track : [000000][=====================]

    center:
    longest track :  [=============================]
    smallest track : [000][===================][000]
    """
    short_t, long_t = (track1, track2) if len(track1) < len(track2) else (track2, track1)
    diff = len(long_t) - len(short_t)

    if offset is not None:
        if len(long_t) - (len(short_t) + offset) >= 0:
            padded_short_t = pad(short_t, (offset, diff - offset), "constant", constant_values=0.0)
        else: # if offset + short > long, we have to padd the end of the long one
            padded_short_t = pad(short_t, (offset, 0), "constant", constant_values=0.0)
            long_t = pad(long_t, (0, offset - diff), "constant", constant_values=0.0)

    elif align is not None and align in ["left", "right", "center"]:
        if align == "right":
            padded_short_t = pad(short_t, (diff, 0), "constant", constant_values=0.0)
        elif align == "left":
            padded_short_t = pad(short_t, (0, diff), "constant", constant_values=0.0)
        elif align == "center":
            left = diff // 2
            right = left if diff % 2 == 0 else left + 1
            padded_short_t = pad(short_t, (left, right), "constant", constant_values=0.0)
    else:
        raise ToolsError()

    # the result vector's elements are c_i = a_i + b_i
    return padded_short_t + long_t


def get_sounds(dir: str) -> List[numpy.ndarray]:
    sounds = []
    for filename in listdir(dir):
        realpath = path.join(dir, filename)
        rate, data = read(realpath)
        sounds.append(data)
    return sounds


def resample(wave_data : numpy.ndarray, sample_in, sample_out=16000):
    """Uses sox to resample the wave data array"""
    cmd = "sox -N -V1 -t f32 -r %s -c 1 - -t f32 -r %s -c 1 -" % (sample_in, sample_out)
    output = run(cmd, shell=True, stdout=PIPE, stderr=PIPE, input=wave_data.tobytes(order="f")).stdout
    return numpy.fromstring(output, dtype=numpy.float32)


class VoiceParameters:

    def __init__(self, speed : int, pitch : int, voice_id : int):
        self.speed = speed
        self.pitch = pitch
        self.voice_id = voice_id

    @classmethod
    def from_cookie_hash(cls, cookie_hash):
        return cls((cookie_hash[5] % 80) + 90, # speed
                   cookie_hash[0] % 100, # pitch
                   cookie_hash[1]) # voice_id


class AudioRenderer:
    lang_voices_mapping = {"fr": ("fr", (1, 2, 3, 4, 5, 6, 7)),
                           "en": ("us", (1, 2, 3)),
                           "es": ("es", (1, 2)),
                           "de": ("de", (4, 5, 6, 7))}

    volumes_presets = {'fr1': 1.17138, 'fr2': 1.60851, 'fr3': 1.01283, 'fr4': 1.0964, 'fr5': 2.64384, 'fr6': 1.35412,
                       'fr7': 1.96092, 'us1': 1.658, 'us2': 1.7486, 'us3': 3.48104, 'es1': 3.26885, 'es2': 1.84053}

    def _get_additional_params(self, lang, voice_params : VoiceParameters):
        """Uses the msg's lang field to figure out the voice, sex, and volume of the synth"""
        lang, voices = self.lang_voices_mapping.get(lang, self.lang_voices_mapping["fr"])
        voice = voices[voice_params.voice_id % len(voices)]

        if lang != 'fr':
            sex = voice
        else:
            sex = 4 if voice in (2, 4) else 1

        volume = 1
        if lang != 'de':
            volume = self.volumes_presets['%s%d' % (lang, voice)] * 0.5

        return lang, voice, sex, volume

    def _wav_format(self, wav : bytes):
        return wav[:4] + pack('<I', len(wav) - 8) + wav[8:40] + pack('<I', len(wav) - 44) + wav[44:]

    def string_to_audio(self, text : str, lang : str, voice_params : VoiceParameters) -> bytes:
        lang, voice, sex, volume = self._get_additional_params(lang, voice_params)
        synth_string = 'MALLOC_CHECK_=0 espeak -s %d -p %d --pho -q -v mb/mb-%s%d %s ' \
                       '| MALLOC_CHECK_=0 mbrola -v %g -e /usr/share/mbrola/%s%d/%s%d - -.wav' \
                       % (voice_params.speed, voice_params.pitch, lang, sex, text, volume, lang, voice, lang, voice)
        logging.debug("Running synth command %s" % synth_string)
        wav = run(synth_string, shell=True, stdout=PIPE, stderr=PIPE).stdout
        return self._wav_format(wav)

    def phonemes_to_audio(self, phonemes : PhonemList, lang : str, voice_params : VoiceParameters) -> bytes:
        lang, voice, sex, volume = self._get_additional_params(lang, voice_params)
        audio_synth_string = 'MALLOC_CHECK_=0 mbrola -v %g -e /usr/share/mbrola/%s%d/%s%d - -.wav' \
                             % (volume, lang, voice, lang, voice)
        logging.debug("Running mbrola command %s" % audio_synth_string)
        wav = run(audio_synth_string, shell=True, stdout=PIPE,
                  stderr=PIPE, input=str(phonemes).encode("utf-8")).stdout
        return self._wav_format(wav)

    def string_to_phonemes(self, text : str, lang : str, voice_params : VoiceParameters) -> PhonemList:
        lang, voice, sex, volume = self._get_additional_params(lang, voice_params)
        phonem_synth_string = 'MALLOC_CHECK_=0 espeak -s %d -p %d --pho -q -v mb/mb-%s%d %s ' \
                              % (voice_params.speed, voice_params.pitch, lang, sex, text)
        logging.debug("Running espeak command %s" % phonem_synth_string)
        return PhonemList(run(phonem_synth_string, shell=True, stdout=PIPE, stderr=PIPE)
                          .stdout
                          .decode("utf-8")
                          .strip())

    @staticmethod
    def to_f32_16k(wav : bytes) -> numpy.ndarray:
        # converting the wav to ndarray, which is much easier to use for DSP
        rate, data = wavfile.read(BytesIO(wav))
        # casting the data array to the right format (float32, for usage by pysndfx)
        data = (data / (2. ** 15)).astype('float32')
        if rate != 16000:
            data = resample(data, rate)
            rate = 16000

        return rate, data

    @staticmethod
    def to_wav_bytes(data : numpy.ndarray, rate : int) -> bytes:
        # casting it back to int16
        data = (data * (2. ** 15)).astype("int16")
        # then, converting it back to binary data
        bytes_obj = bytes()
        bytes_buff = BytesIO(bytes_obj)
        wavfile.write(bytes_buff, rate, data)
        return bytes_buff.read()


class UtilitaryEffect:
    pass


class SpoilerBipEffect(UtilitaryEffect):
    """If there are ** phonems markers in the text, replaces their phonemic render by
    an equally long beep. If not, just returns the text"""
    _tags_phonems = {
        "en" : ("k_hIN", "dZINk"),
        "fr" : ("kiN", "ZiNk"),
        "de" : ("kIN", "gINk"),
        "es" : ("kin", "xink"),
    }
    def __init__(self, renderer : AudioRenderer, voice_params : VoiceParameters):
        super().__init__()
        self.renderer = renderer
        self.voice_params = voice_params

    def _gen_beep(self, duration : int, lang : str):
        i_phonem = "i:" if lang == "de" else "i" # "i" phonem is not the same i german. Damn krauts
        return PhonemList(PhonemList([Phonem("b", 103),
                                      Phonem(i_phonem, duration, [(0, 103 * 3), (80, 103 * 3), (100, 103 * 3)]),
                                      Phonem("p", 228)]))

    def process(self, text: str, lang : str) -> Union[str, PhonemList]:
        """Beeps out parts of the text that are tagged with double asterisks.
        It basicaly replaces the opening and closig asterisk with two opening and closing 'stop words'
        then finds the phonemic form of these two and replaces the phonems inside with an equivalently long beep"""
        occ_list = re.findall(r"\*\*.+?\*\*", text)
        if occ_list:
            # replace the "**text**" by "king text gink"
            tagged_occ_list = [" king %s gink " % occ.strip("*") for occ in occ_list]
            for occ, tagged_occ in zip(occ_list, tagged_occ_list):
                text = text.replace(occ, tagged_occ)
            # getting the phonemic form of the text
            phonems = self.renderer.string_to_phonemes(text, lang, self.voice_params)
            # then using a simple state machine (in_beep is the state), replaces the phonems between
            # the right phonemic occurence with the phonems of a beep
            in_beep = False
            output, buffer = PhonemList([]), PhonemList([])
            while phonems:
                if PhonemList(phonems[:3]).phonemes_str == self._tags_phonems[lang][0] and not in_beep:
                    in_beep, buffer = True, PhonemList([])
                    phonems = PhonemList(phonems[3:])
                elif PhonemList(phonems[:4]).phonemes_str == self._tags_phonems[lang][1] and in_beep:
                    in_beep = False
                    # creating a beep of the buffer's duration
                    if buffer:
                        output += self._gen_beep(sum([pho.duration for pho in buffer]), lang)
                    phonems = phonems[4:]
                elif not in_beep:
                    output.append(phonems.pop(0))
                elif in_beep:
                    buffer.append(phonems.pop(0))
            return output
        else:
            return text


def add_msg_html_tag(text : str) -> str:
    """Add html tags to the output message, for vocaroos, links or spoilers"""
    text = escape(text)
    if re.search(r'\*\*.*?\*\*', text):
        text = re.sub(r'(\*\*(.*?)\*\*)', r'<span class="spoiler">\2</span>', text)

    if re.search(r'(https?://vocaroo\.com/i/[0-9a-z]+)', text, flags=re.IGNORECASE):
        vocaroo_player_tag= r'''<object width="148" height="44">
            <param name="movie" value="https://loult.family/player.swf?playMediaID=\2&autoplay=0"></param>
            <param name="wmode" value="transparent"></param>
            <embed src="https://loult.family/player.swf?playMediaID=\2&autoplay=0"
            width="148" height="44" wmode="transparent" type="application/x-shockwave-flash">
            </embed></object><a href="\1" target="_blank">Donne mou la vocarookles</a>'''
        text = re.sub(r'(?P<link>https?://vocaroo\.com/i/(?P<id>[0-9a-z]+))', vocaroo_player_tag, text,
                      flags=re.IGNORECASE)
    elif re.search(r'(https?://[^ ]*[^*.,?! :])', text):
        text = re.sub(r'(https?://[^< ]*[^<*.,?! :])', r'<a href="\1" target="_blank">\1</a>', text)

    return text