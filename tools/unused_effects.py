
"""This is where effects go to die"""
import random
from os import path

import numpy
from .phonems import PhonemList
from .effects import PhonemicEffect, AudioEffect
from tools.audio_tools import get_sounds, mix_tracks


class PhonemicShuffleEffect(PhonemicEffect):
    NAME = "interprète kiglon"
    TIMEOUT = 120

    def process(self, phonems : PhonemList):
        random.shuffle(phonems)
        return phonems


class ReversedEffect(AudioEffect):
    """?sdef vlop sdaganliup uirt vlad"""
    NAME = "inversion"
    TIMEOUT = 120

    def process(self, wave_data: numpy.ndarray):
        return wave_data[::-1]


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


class SitcomEffect(AudioEffect):
    main_dir = path.join(path.dirname(path.realpath(__file__)), "data/sitcom")
    _subfolders = ["laugh_track", "boo", "applaud"]
    NAME = "sitcom"
    TIMEOUT = 150

    def __init__(self):
        super().__init__()
        self.tracks = dict()
        for subfolder in self._subfolders:
            self.tracks[subfolder] = get_sounds(path.join(self.main_dir, subfolder))
            # sorting by length
            self.tracks[subfolder].sort(key = lambda s: len(s))

    def find_nearest(self, track_list, value):
        nearest_bigger_index = next((i for i, x in enumerate(track_list) if len(x) > value), None)
        return nearest_bigger_index - 1 if nearest_bigger_index > 0 else 0

    def process(self, wave_data: numpy.ndarray):
        if random.randint(0,1):
            randoum = random.randint(1, 3)
            if randoum == 1:
                wave_data = numpy.concatenate((wave_data, random.choice(self.tracks["laugh_track"])))
            elif randoum == 2:
                wave_data = numpy.concatenate((wave_data, random.choice(self.tracks["applaud"])))
            elif randoum == 3:
                boo_track_id = self.find_nearest(self.tracks["boo"], len(wave_data))
                wave_data = mix_tracks(wave_data, self.tracks["boo"][boo_track_id], align="right")

        return wave_data