from typing import Tuple
import random

from tools import get_random_effect
from tools.effects import TouretteEffect, VenerEffect, CrapweEffect, TurboHangoul


class CombatSimulator:

    _global_effects = [TouretteEffect, VenerEffect, CrapweEffect, TurboHangoul]

    def __init__(self):
        self._affected_users = []

    def _fumble(self, user):
        for effect in [get_random_effect() for i in range(4)]:
            user.add_effect(effect)
            self._affected_users.append((user, effect))

    def run_attack(self, attacker, defender, channel):
        self.atk_dice, self.atk_bonus = attacker.throw_dice("attack")# type:Tuple[int,int]
        self.def_dice, self.def_bonus = defender.throw_dice("defend")# type:Tuple[int,int]

        if self.atk_dice == 100: # global effect
            effect_type = random.choice(self._global_effects)
            for userid, user in channel.users.items():
                if userid != attacker.user_id:
                    effect_obj = effect_type()
                    user.add_effect(effect_obj)
                    self._affected_users.append((user,effect_obj))

        elif self.atk_dice == 1 or self.def_dice == 100: # attack fumble
            self._fumble(attacker)

        elif self.def_dice == 1: # def fumble
            self._fumble(defender)

        elif self.atk_dice + self.atk_bonus < self.def_dice + self.def_bonus: # rebound or bounceback
            randoum = random.randint(1,3)
            effect = get_random_effect()
            if randoum == 1: # bounceback
                attacker.add_effect(effect)
                self._affected_users = [(attacker, effect)]
            elif randoum == 2:
                random_other_user = random.choice(list(channel.users.values()))
                random_other_user.add_effect(effect)
                self._affected_users = [(random_other_user, effect)]

        elif self.atk_dice + self.atk_bonus > self.def_dice + self.def_bonus:# regular atck pass
            effect = get_random_effect()
            defender.add_effect(effect)
            self._affected_users = [(defender, effect)]

    @property
    def affected_users(self):
        return self._affected_users