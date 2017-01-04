from .effects import Effect, SnebwewEffect, ReversedEffect, ReverbManEffect, TouretteEffect, \
    GhostEffect, SpeechMasterEffect, IssouEffect, AmbianceEffect, \
    PhonemicShuffleEffect, PhonemicNwwoiwwEffect, PhonemicFofoteEffect, AccentMarseillaisEffect
from .phonems import PhonemList

import random
AVAILABLE_EFFECTS = [GhostEffect, SnebwewEffect, ReversedEffect, ReverbManEffect, TouretteEffect,
                     SpeechMasterEffect, PhonemicNwwoiwwEffect, PhonemicShuffleEffect,
                     PhonemicFofoteEffect, AccentMarseillaisEffect, IssouEffect, AmbianceEffect]
# AVAILABLE_EFFECTS = [] single effects list used when testing


def get_random_effect() -> Effect:
    return random.choice(AVAILABLE_EFFECTS)()