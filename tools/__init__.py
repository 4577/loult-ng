from .effects import Effect, SnebwewEffect, ReversedEffect, ReverbManEffect, TouretteEffect, \
    GhostEffect, SpeechMasterEffect, IssouEffect, AmbianceEffect, \
    PhonemicShuffleEffect, PhonemicNwwoiwwEffect, PhonemicFofoteEffect, AccentMarseillaisEffect, \
    VocalDyslexia, AccentAllemandEffect, CrapweEffect, TurboHangoul, MwfeEffect, BeatsEffect, VenerEffect
from .phonems import PhonemList

import random
# the multiplier for each tools list sets the "probability" of the effect
AVAILABLE_EFFECTS = 1 * [IssouEffect, PhonemicShuffleEffect] + \
                    2 * [GhostEffect, ReversedEffect, SnebwewEffect, ReverbManEffect, TouretteEffect, VenerEffect,
                         SpeechMasterEffect, PhonemicNwwoiwwEffect, VocalDyslexia,
                         PhonemicFofoteEffect, AccentMarseillaisEffect, AccentAllemandEffect, MwfeEffect,
                         CrapweEffect] + \
                    3 * [AmbianceEffect, TurboHangoul] + \
                    4 * [BeatsEffect]
AVAILABLE_EFFECTS = [BeatsEffect] # single tools list used when testing


def get_random_effect() -> Effect:
    return random.choice(AVAILABLE_EFFECTS)()