from .effects import Effect, BiteDePingouinEffect, ReversedEffect
import random
AVAILABLE_EFFECTS = [BiteDePingouinEffect, ReversedEffect]


def get_random_effect() -> Effect:
    return random.choice(AVAILABLE_EFFECTS)()