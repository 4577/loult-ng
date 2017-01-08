from typing import List

import numpy
from numpy.lib import pad
from os import listdir, path
from scipy.io.wavfile import read

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