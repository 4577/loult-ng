from .effects.effects import (Effect, SnebwewEffect, ReverbManEffect, TouretteEffect, RobotVoiceEffect,
                      GhostEffect, SpeechMasterEffect, PoiloEffect, PitchRandomizerEffect,
                      PhonemicNwwoiwwEffect, PhonemicFofoteEffect, AccentMarseillaisEffect, AngryRobotVoiceEffect,
                      VocalDyslexia, AccentAllemandEffect, CrapweEffect, TurboHangoul, MwfeEffect, VieuxPortEffect, GodSpeakingEffect, WpseEffect, SpoinkEffect, AutotuneEffect, VoiceSpeedupEffect,
                      StutterEffect, GrandSpeechMasterEffect, VowelExchangeEffect, SkyblogEffect)
from .effects.effects import PhonemicEffect, VoiceEffect, AudioEffect, ExplicitTextEffect, HiddenTextEffect
from .phonems import PhonemList


import random
# the multiplier for each tools list sets the "probability" of the effect
AVAILABLE_EFFECTS = 1 * [GodSpeakingEffect, SnebwewEffect, VoiceSpeedupEffect,
                         PhonemicFofoteEffect, VieuxPortEffect, MwfeEffect,
                         SpoinkEffect, TurboHangoul, GhostEffect, TurboHangoul,
                         SkyblogEffect] + \
                    3 * [WpseEffect, SpeechMasterEffect, CrapweEffect,
                         VocalDyslexia, ReverbManEffect, PhonemicNwwoiwwEffect,
                         StutterEffect, GrandSpeechMasterEffect, TouretteEffect,
                         VowelExchangeEffect] + \
                    6 * [AutotuneEffect, PitchRandomizerEffect,
                         RobotVoiceEffect, PoiloEffect, AngryRobotVoiceEffect]
# AVAILABLE_EFFECTS = [BeatsEffect] # single tools list used when testing


def get_random_effect() -> Effect:
    return random.choice(AVAILABLE_EFFECTS)()
