from numpy.lib import pad

class ToolsError(Exception):
    pass

def mix_tracks(track1, track2, offset=None, align=None):
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

    return padded_short_t + long_t