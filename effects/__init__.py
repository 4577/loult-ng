from .effects import Effect, SnebwewEffect, ReversedEffect, ReverbManEffect, TouretteEffect
import random
AVAILABLE_EFFECTS = [ReversedEffect, ReverbManEffect, TouretteEffect]


def get_random_effect() -> Effect:
    return random.choice(AVAILABLE_EFFECTS)()