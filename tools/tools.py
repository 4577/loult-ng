import logging
import re
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
        padded_short_t = pad(short_t, (offset, diff - offset), "constant", constant_values=0.0)
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

    def __init__(self, cookie_hash):
        self.speed = (cookie_hash[5] % 80) + 90
        self.pitch = cookie_hash[0] % 100
        self.voice_id = cookie_hash[1]


class AudioRenderer:
    lang_voices_mapping = {"fr": ("fr", (1, 2, 3, 4, 5, 6, 7)),
                           "en": ("us", (1, 2, 3)),
                           "es": ("es", (1, 2)),
                           "de": ("de", (4, 5, 6, 7))}


    volumes_presets = {'fr1': 1.17138, 'fr2': 1.60851, 'fr3': 1.01283, 'fr4': 1.0964, 'fr5': 2.64384, 'fr6': 1.35412,
                       'fr7': 1.96092, 'us1': 1.658, 'us2': 1.7486, 'us3': 3.48104, 'es1': 3.26885, 'es2': 1.84053}

    def __init__(self, cookie_hash : str):
        self.voice_params = VoiceParameters(cookie_hash)

    def _get_additional_params(self, lang):
        lang, voices = self.lang_voices_mapping.get(lang, self.lang_voices_mapping["fr"])
        voice = voices[self.voice_params.voice_id % len(voices)]

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

    def string_to_audio(self, text : str, lang : str) ->bytes:
        lang, voice, sex, volume = self._get_additional_params(lang)
        synth_string = 'MALLOC_CHECK_=0 espeak -s %d -p %d --pho -q -v mb/mb-%s%d %s ' \
                       '| MALLOC_CHECK_=0 mbrola -v %g -e /usr/share/mbrola/%s%d/%s%d - -.wav' \
                       % (self.voice_params.speed, self.voice_params.pitch, lang, sex, text, volume, lang, voice, lang, voice)
        logging.debug("Running synth command %s" % synth_string)
        wav = run(synth_string, shell=True, stdout=PIPE, stderr=PIPE).stdout
        return self._wav_format(wav)

    def phonemes_to_audio(self, phonemes : PhonemList, lang : str) -> bytes:
        lang, voice, sex, volume = self._get_additional_params(lang)
        audio_synth_string = 'MALLOC_CHECK_=0 mbrola -v %g -e /usr/share/mbrola/%s%d/%s%d - -.wav' \
                             % (volume, lang, voice, lang, voice)
        logging.debug("Running mbrola command %s" % audio_synth_string)
        wav = run(audio_synth_string, shell=True, stdout=PIPE,
                  stderr=PIPE, input=str(phonemes).encode("utf-8")).stdout
        return self._wav_format(wav)

    def string_to_phonemes(self, text : str, lang : str) -> PhonemList:
        lang, voice, sex, volume = self._get_additional_params(lang)
        phonem_synth_string = 'MALLOC_CHECK_=0 espeak -s %d -p %d --pho -q -v mb/mb-%s%d %s ' \
                              % (self.voice_params.speed, self.voice_params.pitch, lang, sex, text)
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
    def __init__(self, renderer : AudioRenderer):
        super().__init__()
        self.renderer = renderer

    def _gen_beep(self, duration : int):
        return PhonemList(PhonemList([Phonem("b", 103),
                                      Phonem("i", duration, [(0, 103 * 3), (80, 103 * 3), (100, 103 * 3)]),
                                      Phonem("p", 228)]))

    def process(self, text: str, lang : str) -> Union[str, PhonemList]:
        # TODO : comment some stuff here
        occ_list = re.findall(r"\*\*.+?\*\*", text)
        if occ_list:
            tagged_occ_list = [" king %s gink " % occ.strip("*") for occ in occ_list]
            for occ, tagged_occ in zip(occ_list, tagged_occ_list):
                text = text.replace(occ, tagged_occ)

            phonems = self.renderer.string_to_phonemes(text, lang)
            in_beep = False
            output, buffer = PhonemList([]), PhonemList([])
            while phonems:
                if PhonemList(phonems[:3]).phonemes_str == "kiN" and not in_beep:
                    in_beep, buffer = True, PhonemList([])
                    phonems = PhonemList(phonems[3:])
                elif PhonemList(phonems[:4]).phonemes_str == "ZiNk" and in_beep:
                    in_beep = False
                    # creating a beep of the buffer's duration
                    if buffer:
                        output += self._gen_beep(sum([pho.duration for pho in buffer]))
                    phonems = phonems[4:]
                elif not in_beep:
                    output.append(phonems.pop(0))
                elif in_beep:
                    buffer.append(phonems.pop(0))
            return output
        else:
            return text


