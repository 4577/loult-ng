import random
from datetime import datetime


class Effect:
    TIMEOUT = 0
    def __init__(self):
        self.creation = datetime.now()

    def is_expired(self):
        return (datetime.now() - self.creation).seconds > self.TIMEOUT

    def process(self, **kwargs):
        pass


class TextEffect(Effect):

    def process(self, text : str):
        pass


class SoundEffect(Effect):

    def process(self, wav):
        pass


#### Here are the text effects ####

class BiteDePingouinEffect(TextEffect):
    """Changes the text to a random number of bitedepingouin"""

    TIMEOUT = 60

    def process(self, text : str):
        return "BITEDEPINGOUIN? " * random.randint(1,6)