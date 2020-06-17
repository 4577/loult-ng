from itertools import cycle
from pathlib import Path
from time import time as timestamp
from typing import List
from urllib.parse import unquote

from .base import LoultObject, destructible, targeted, for_militia, userlist_dist, cooldown, inert, DATA_FOLDER


@targeted()
@cooldown(5)
class RobinHoodsBow(LoultObject):
    ICON = "robinhoodsbow.gif"
    NAME = "arc de robin des bois"
    BOW_FX = DATA_FOLDER / Path("bow_fire.mp3")

    def use(self, obj_params):
        if self.user is self.targeted_user:
            return self.notify_serv(msg="Impossible d'utiliser l'arc sur soi-même")

        usrs = list(self.channel.users.values())
        usrs.remove(self.targeted_user)
        usrs.remove(self.user)
        target_objs = list(self.targeted_user.state.inventory.objects)

        quivers = self.user_inventory.search_by_class(Quiver)
        if not quivers:
            return self.notify_serv(msg="Il vous faut un carquois avec des flèches pour pouvoir tirer à l'arc!")
        quiver = quivers[0]
        quiver.arrows -= 1

        if usrs:
            usrs.sort(key=lambda x: len(x.state.inventory.objects), reverse=False)
            for usr in cycle(usrs):
                if target_objs:
                    obj = target_objs.pop()
                    self.targeted_user.state.inventory.remove(obj)
                    usr.state.inventory.add(obj)
                else:
                    break
        else:
            for obj in target_objs:
                self.targeted_user.state.inventory.remove(obj)
                self.channel.inventory.add(obj)
        self.notify_channel(
            msg=f"{self.user_fullname} vole à {self.targeted_user.poke_params.fullname} pour donner aux pauvres",
            binary_payload=self._load_byte(self.BOW_FX))


@destructible
@inert
class Quiver(LoultObject):
    ICON = "carquois.gif"
    NAME = "carquois"

    def __init__(self, arrows=3):
        super().__init__()
        self.arrows = arrows

    @property
    def name(self):
        if self.arrows:
            return self.NAME + " (%s)" % ("➹" * self.arrows)
        else:
            return self.NAME

    @property
    def destroy(self):
        return self.arrows <= 0


@for_militia
@targeted()
class MilitiaSniper(LoultObject):
    NAME = "PGM Hecate II"
    SNIPER_FX = DATA_FOLDER / Path("sniper_headshot.mp3")

    def __init__(self):
        super().__init__()
        self.remaining_bullets = 7

    @property
    def name(self):
        if self.remaining_bullets:
            return self.NAME + " (%s)" % ("▮" * self.remaining_bullets)
        else:
            return self.NAME + " (vide)"

    def use(self, obj_params):
        #  TODO : add a "scope" last argument maybe
        if self.remaining_bullets <= 0:
            return self.notify_serv(msg="Plus de munitions!")
        self.remaining_bullets -= 1
        self.notify_channel(
            msg=f"{self.user_fullname} tire au fusil sniper calibre .50 sur {self.targeted_user.poke_params.fullname}",
            binary_payload=self._load_byte(self.SNIPER_FX))
        self.channel.broadcast(type='antiflood', event='banned',
                               flooder_id=self.targeted_userid,
                               date=timestamp() * 1000)
        for client in self.targeted_user.clients:
            self.loult_state.apply_ban(ip=client.ip)
            client.sendClose(code=4006, reason="Reconnect later.")
        splashed_usrs = [usr for usr in self.server.channel_obj.users.values()
                         if userlist_dist(self.channel, self.targeted_userid, usr.user_id) < 2
                         and usr is not self.targeted_user]
        splashed_usrs = ", ".join(usr.poke_params.fullname for usr in splashed_usrs)
        self.notify_channel(
            msg=f"{splashed_usrs} se sont faits éclabousser de sang et de cervelle de {self.targeted_user.poke_params.fullname}")


@for_militia
@destructible
class MilitiaSniperAmmo(LoultObject):
    NAME = "Chargeur PGM"
    RELOADING_FX = DATA_FOLDER / Path("gun/reloading.mp3")

    def use(self, obj_params):
        # searching in the user's inventory for the emptiest gun to be used on
        users_guns = self.user_inventory.search_by_class(MilitiaSniper)
        users_guns = [gun for gun in users_guns if gun.remaining_bullets < 7]
        if not users_guns:
            return self.notify_serv(msg="Pas de PGM à recharger dans votre inventaire")

        users_guns.sort(key=lambda x: x.remaining_bullets, reverse=False)
        emptiest_gun = users_guns[0]
        emptiest_gun.remaining_bullets = 7
        self.notify_serv(msg="PGM Hécate II chargé!")
        self.channel.broadcast(self._load_byte(self.RELOADING_FX))
        self.should_be_destroyed = True


class ClientSidePunitiveObject(LoultObject):
    EVENT = "none"
    MSG = ""

    def use(self, obj_params):
        for client in self.targeted_user.clients:
            self.loult_state.apply_ban(ip=client.ip)
        for client in self.server.user.clients:
            client.send_json(type="notification", msg=self.MSG % self.targeted_user.poke_params.fullname)
        for client in self.targeted_user.clients:
            client.send_json(type="punish", event=self.EVENT)


@for_militia
@targeted()
class Civilisator(ClientSidePunitiveObject):
    NAME = "Civilizator"
    EVENT = "taser"
    MSG = "Civilisation de %s"


@for_militia
@targeted()
class Screamer(ClientSidePunitiveObject):
    NAME = "SCR34-MR"
    EVENT = "cactus"
    MSG = "Redirection vers un site adapté pour %s"


@for_militia
@targeted()
class UserInspector(LoultObject):
    NAME = "Gadget d'inspecteur"

    def use(self, obj_params):
        from ..users import PokeParameters
        last_identities = []
        for client in self.targeted_user.clients:
            for cookie in self.loult_state.id_backlog.get_ip_cookies(client.ip):
                last_identities.append(PokeParameters.from_cookie_hash(cookie).fullname)
        self.notify_serv(f"Dernières identités pour cet utilisateur: {', '.join(last_identities)}")
        last_channels = []

        for channel_name in self.loult_state.id_backlog.get_cookie_channels(self.targeted_user.cookie_hash):
            if channel_name == "":
                last_channels.append("[main]")
            else:
                last_channels.append(unquote(channel_name))
        self.notify_serv(f"Derniers canaux pour cet utilisateur: {', '.join(last_channels)}")


@for_militia
class ChannelSniffer(LoultObject):
    NAME = "Renifleuw de canaux"

    def use(self, obj_params: List):
        if obj_params:
            channel_name = obj_params[0]
            if not channel_name in self.loult_state.chans:
                self.notify_serv(f"Canal {channel_name} inexistant")
                return
            channel = self.loult_state.chans[channel_name]
            users = [user.poke_params.fullname for user in channel.users.values()]
            self.notify_serv(f"Utilisateurs sur le canal {channel_name}: {', '.join(users)}")
        else:
            channels_summary = ", ".join([f"{channel.name} ({len(channel.users)})"
                                          for channel in self.loult_state.chans.values()])
            self.notify_serv(f"Canaux ouverts : {channels_summary}")
