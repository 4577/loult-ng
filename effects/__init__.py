from .effects import Effect, SnebwewEffect, ReversedEffect, ReverbManEffect, TouretteEffect, \
    GhostEffect, SpeechMasterEffect, NwwoiwwEffect, FofoteEffect, IssouEffect
import random
# AVAILABLE_EFFECTS = [GhostEffect, SnebwewEffect, ReversedEffect, ReverbManEffect, TouretteEffect,
#                      SpeechMasterEffect, NwwoiwwEffect, FofoteEffect]
AVAILABLE_EFFECTS = [IssouEffect] # single effect list used when testing


def get_random_effect() -> Effect:
    return random.choice(AVAILABLE_EFFECTS)()