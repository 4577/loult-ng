from .effects import Effect, BiteDePingouinEffect, ReversedEffect, ReverbManEffect
import random
AVAILABLE_EFFECTS = [BiteDePingouinEffect, ReversedEffect, ReverbManEffect]


def get_random_effect() -> Effect:
    return random.choice(AVAILABLE_EFFECTS)()