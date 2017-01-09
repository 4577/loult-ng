from .effects import Effect, SnebwewEffect, ReversedEffect, ReverbManEffect, TouretteEffect, \
    GhostEffect, SpeechMasterEffect, IssouEffect, AmbianceEffect, \
    PhonemicShuffleEffect, PhonemicNwwoiwwEffect, PhonemicFofoteEffect, AccentMarseillaisEffect, \
    VocalDyslexia, AccentAllemandEffect, CrapweEffect, TurboHangoul, MwfeEffect, BeatsEffect, VenerEffect
from .phonems import PhonemList

import random
# the multiplier for each effects list sets the "probability" of the effect
AVAILABLE_EFFECTS = 1 * [IssouEffect, ReversedEffect, VocalDyslexia] + \
                    2 * [GhostEffect, SnebwewEffect, ReverbManEffect, TouretteEffect, VenerEffect,
                         SpeechMasterEffect, PhonemicNwwoiwwEffect, PhonemicShuffleEffect,
                         PhonemicFofoteEffect, AccentMarseillaisEffect, AccentAllemandEffect, MwfeEffect] + \
                    3 * [AmbianceEffect, CrapweEffect, TurboHangoul] + \
                    4 * [BeatsEffect]
AVAILABLE_EFFECTS = [BeatsEffect] # single effects list used when testing


def get_random_effect() -> Effect:
    return random.choice(AVAILABLE_EFFECTS)()