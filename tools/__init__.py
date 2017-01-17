from tools.effects import WpseEffect, SpoinkEffect
from .effects import Effect, SnebwewEffect, ReverbManEffect, TouretteEffect, \
    GhostEffect, SpeechMasterEffect, AmbianceEffect, SitcomEffect, \
    PhonemicNwwoiwwEffect, PhonemicFofoteEffect, AccentMarseillaisEffect, \
    VocalDyslexia, AccentAllemandEffect, CrapweEffect, TurboHangoul, MwfeEffect, BeatsEffect, VenerEffect ,\
    VieuxPortEffect, GodSpeakingEffect
from .effects import PhonemicEffect, VoiceEffect, AudioEffect, ExplicitTextEffect, HiddenTextEffect
from .phonems import PhonemList


import random
# the multiplier for each tools list sets the "probability" of the effect
AVAILABLE_EFFECTS = 1 * [] + \
                    2 * [GhostEffect, SnebwewEffect, ReverbManEffect, TouretteEffect, VenerEffect,
                         SpeechMasterEffect, PhonemicNwwoiwwEffect, VocalDyslexia, SitcomEffect,
                         PhonemicFofoteEffect, VieuxPortEffect, AccentAllemandEffect, MwfeEffect,
                         CrapweEffect, AmbianceEffect, SpoinkEffect] + \
                    3 * [TurboHangoul, BeatsEffect, GodSpeakingEffect] + \
                    4 * [WpseEffect]
# AVAILABLE_EFFECTS = [MwfeEffect, TurboHangoul, CrapweEffect, SitcomEffect, WpseEffect, SpoinkEffect, GodSpeakingEffect] # single tools list used when testing


def get_random_effect() -> Effect:
    return random.choice(AVAILABLE_EFFECTS)()