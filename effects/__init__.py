from .effects import Effect, SnebwewEffect, ReversedEffect, ReverbManEffect, TouretteEffect, \
    GhostEffect, SpeechMasterEffect, IssouEffect, AmbianceEffect, \
    PhonemicShuffleEffect, PhonemicNwwoiwwEffect, PhonemicFofoteEffect, AccentMarseillaisEffect, \
    VocalDyslexia, AccentAllemandEffect, CrapweEffect, TurboHangoul, MwfeEffect, BeatsEffect
from .phonems import PhonemList

import random
AVAILABLE_EFFECTS = [GhostEffect, SnebwewEffect, ReversedEffect, ReverbManEffect, TouretteEffect,
                     SpeechMasterEffect, PhonemicNwwoiwwEffect, PhonemicShuffleEffect,
                     PhonemicFofoteEffect, AccentMarseillaisEffect, IssouEffect, AmbianceEffect,
                     VocalDyslexia, AccentAllemandEffect, CrapweEffect, TurboHangoul, MwfeEffect]
# AVAILABLE_EFFECTS = [BeatsEffect, TurboHangoul] # single effects list used when testing


def get_random_effect() -> Effect:
    return random.choice(AVAILABLE_EFFECTS)()