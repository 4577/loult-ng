from .effects import Effect, SnebwewEffect, ReversedEffect, ReverbManEffect, TouretteEffect, \
    GhostEffect, SpeechMasterEffect, NwwoiwwEffect
import random
AVAILABLE_EFFECTS = [GhostEffect, SnebwewEffect, ReversedEffect, ReverbManEffect, TouretteEffect,
                     SpeechMasterEffect, NwwoiwwEffect]
# AVAILABLE_EFFECTS = [SpeechMasterEffect] # single effect list used when testing


def get_random_effect() -> Effect:
    return random.choice(AVAILABLE_EFFECTS)()