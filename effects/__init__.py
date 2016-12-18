from .effects import Effect, SnebwewEffect, ReversedEffect, ReverbManEffect, TouretteEffect, GhostEffect
import random
AVAILABLE_EFFECTS = [GhostEffect, SnebwewEffect, ReversedEffect, ReverbManEffect, TouretteEffect]


def get_random_effect() -> Effect:
    return random.choice(AVAILABLE_EFFECTS)()