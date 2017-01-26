from tools.effects import WpseEffect, SpoinkEffect, TurfuEffect, AutotuneEffect, VoiceSpeedupEffect
from .unused_effects import ReversedEffect
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
                    2 * [GhostEffect, SnebwewEffect, ReverbManEffect, TouretteEffect, VenerEffect, VoiceSpeedupEffect,
                         SpeechMasterEffect, PhonemicNwwoiwwEffect, VocalDyslexia, SitcomEffect,
                         PhonemicFofoteEffect, VieuxPortEffect, AccentAllemandEffect, MwfeEffect,
                         CrapweEffect, AmbianceEffect, SpoinkEffect] + \
                    3 * [TurboHangoul, BeatsEffect, GodSpeakingEffect, WpseEffect, TurfuEffect] + \
                    4 * [AutotuneEffect]
# AVAILABLE_EFFECTS = [BeatsEffect] # single tools list used when testing


def get_random_effect() -> Effect:
    return random.choice(AVAILABLE_EFFECTS)()