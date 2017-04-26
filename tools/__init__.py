from .unused_effects import ReversedEffect
from .effects import (Effect, SnebwewEffect, ReverbManEffect, TouretteEffect, RobotVoiceEffect,
                      GhostEffect, SpeechMasterEffect, AmbianceEffect, PoiloEffect, PitchRandomizerEffect,
                      PhonemicNwwoiwwEffect, PhonemicFofoteEffect, AccentMarseillaisEffect, GaDoSEffect,
                      VocalDyslexia, AccentAllemandEffect, CrapweEffect, TurboHangoul, MwfeEffect, BeatsEffect,
                      VenerEffect, VieuxPortEffect, GodSpeakingEffect, WpseEffect, SpoinkEffect, TurfuEffect,
                      AutotuneEffect, VoiceSpeedupEffect, StutterEffect, GrandSpeechMasterEffect)
from tools.unused_effects import SitcomEffect
from .effects import PhonemicEffect, VoiceEffect, AudioEffect, ExplicitTextEffect, HiddenTextEffect
from .phonems import PhonemList


import random
# the multiplier for each tools list sets the "probability" of the effect
AVAILABLE_EFFECTS = 1 * [TurfuEffect, AmbianceEffect, VenerEffect] + \
                    2 * [GhostEffect, SnebwewEffect, ReverbManEffect, VoiceSpeedupEffect,
                         SpeechMasterEffect, PhonemicNwwoiwwEffect, VocalDyslexia,
                         PhonemicFofoteEffect, VieuxPortEffect, AccentAllemandEffect, MwfeEffect,
                         CrapweEffect, SpoinkEffect, BeatsEffect] + \
                    3 * [TurboHangoul, GodSpeakingEffect, WpseEffect, StutterEffect, GrandSpeechMasterEffect,
                         TouretteEffect, PitchRandomizerEffect] + \
                    4 * [AutotuneEffect, RobotVoiceEffect, PoiloEffect, GaDoSEffect]
# AVAILABLE_EFFECTS = [BeatsEffect] # single tools list used when testing


def get_random_effect() -> Effect:
    return random.choice(AVAILABLE_EFFECTS)()