Un chat de pokémons avec synthèse vocale. D'après une œuvre de *@DrEmixam*.

La partie client est en HTML/CSS/JS statique et la partie serveur en Python.

# Installation

* Installez nginx, python3-venv, le synthétiseur vocal mbrola,
espeak, sox, ainsi que les voix mbrola :
`apt install nginx mbrola espeak sox mbrola-fr1 mbrola-us1 mbrola-es1 mbrola-de4 python3 python3-venv`

* Clonez le lou sur votre propre machine :
```bash
git clone https://github.com/4577/loult-ng.git
cd loult-ng
```
* Créez un petit venv :
```bash
python3 -m venv venv
source venv/bin/activate
```
* Installez le reste des dépendances avec pip : `pip install -r requirements.txt`
* Créez un fichier `salt.py` contenant `SALT = '<valeur arbitraire>'`
* Configurez nginx en vous servant de `loult.conf` (notamment adaptez le chemin de `$static`)
```bash
cp loult.conf /etc/nginx/sites-available/
ln -s /etc/nginx/{sites-available,sites-enabled}/loult.conf
systemctl reload nginx
```
* Lancez `python3 poke.py`

# Usage

* Les options de configuration disponibles sont décrites dans `conf.py`.
* Tapez `/aide` dans la zone de texte du chat pour avoir accès à la liste des commandes disponibles.
* Un système d'antiflood automatique est intégré ; il exclut un utilisateur sur la base de son cookie
s'il poste trop vite par deux fois.

## Combat

Les utilisateurs peuvent s'attaquer les uns les autres en lançant la commande `/attack Taupiqueur`.
S'il y a plusieurs pokémons à ce nom dans le chat, on peut rajouter son numéro dans la liste,
comme `/attack Taupiqueur 3`, ce qui attaquera le 3ème Taupiqueur dans la liste.

Il y a un temps minimum entre chaque nouvelle attaque par un utilisateur. Cela peut être configuré.

## Bans manuels

Le système de ban utilise le pare-feu de Linux pour éviter de faire consommer
des ressources au serveur python. Il faut cependant au préalable configurer
ce pare-feu en y ajoutant quelques règles. Vous pouvez vous inspirer ou utiliser
directement `nftables.conf.sample`. À noter qu'aucune interface ni outil n'est fourni
pour placer ces bans manuels, vous devez lire `tools/ban.py` pour un implémenter un.

Supposons que la table `filter` de type `inet` contienne une chaîne nommée
`input` pour le hook `input` et chaîne `output` autre pour le hook `output`.
Les règles à rajouter sont alors :

	nft add set inet input ban "{type ipv4_addr; flags timeout;}"
	nft add set inet ipnut slowban "{type ipv4_addr; flags timeout;}"
	nft add rule inet filter input ip saddr @ban ct state new,established drop
	nft add rule inet filter output ip daddr @slowban ct state new,established flow table slowbanftable { ip saddr limit rate over 10 kbytes/second } drop


Voici un moyen de faire marcher ce système entre chaque redémarrage du serveur :

* installez `nftables` et assurez-vous que la commande `nft` puisse être
  lancée par l'utilisateur lançant loult-ng sans entrer de mot de passe
* copiez `nftables.sample.conf` sur `/etc/nftables.conf`
* lancez `systemctl enable nftables` puis `systemctl restart nftables`

# Développement tiers

## Bots

Pour rendre votre bot plus discret, utilisez les types de message `bot` et `me`.
Le type `bot`, accessible seulement de manière programmatique, est rendu comme un message
en italiques et de la couleur associée au cookie du bot, sans synthèse vocale.

## Fermeture impromptue du websocket

L'application définit des codes d'erreurs spéciaux lors de la fermeture
immédiate par le serveur d'un websocket :

| code | signification             |
|------|---------------------------|
| 4000 | Erreur inattendue         |
| 4001 | JSON malformé             |
| 4002 | Données binaires refusées |
| 4003 | Type de commande inconnu  |
| 4004 | Banni pour flood          |

