La partie client est en HTML/CSS/JS statique et la partie serveur en Python.

# Mise en place

* Installer nginx, python3-scipy, le synthésiseur vocal mbrola, 
espeak, sox (sur gestionnaire de paquet debian), ainsi que les voix mbrola:
`sudo apt-get install nginx python3-scipy python3-autobahn mbrola espeak sox mbrola-fr1 mbrola-us1 mbrola-es1 mbrola-de4 python3-venv portaudio19-dev`

* Clonez le lou sur votre propre machine
```bash
mkdir -p loult/venv
cd loult
git clone https://github.com/4577/loult-ng.git
```

* Créez un petit venv installer les dépendances du lou dedans
```bash
python3 -m venv venv
source venv/bin/activate
```

* Installer le reste des dépendances (`autobahn`, `pysndfx`) avec pip3:

`pip3 install -r requirements.txt`

Si vous le souhaitez, installez `uvloop`, une boucle évènementielle
alternative à celle d'`asyncio` et plus rapide:

`pip3 install uvloop`

* Créer un fichier `salt.py` contenant `SALT = 'valeur arbitraire'`
* Configurer nginx avec `loult.conf`, adapter le chemin de $static

```bash
mv loult.conf /etc/nginx/site-available/
ln -s /etc/nginx/site-available/ /etc/nginx/site-enabled
```

* Lancer `poke.py`

# Bans

Le système de ban utilise le pare-feu de Linux pour éviter de faire consommer
des ressources au serveur python. Il faut cependant au préalable configurer
ce pare-feu en y ajoutant quelques règles. Vous pouvez vous inspirer ou utiliser
directement `nftables.conf.sample`.

Supposons que la table `filter` de type `inet` contienne une chaîne nommée
`input` pour le hook `input` et chaîne `output` autre pour le hook `output`.
Les règles à rajouter sont alors :

	nft add set inet input ban "{type ipv4_addr; flags timeout;}"
	nft add set inet ipnut slowban "{type ipv4_addr; flags timeout;}"
	nft add rule inet filter input ip saddr @ban drop
	nft add rule inet filter output ip daddr @slowban flow table slowbanftable { ip saddr limit rate over 10 kbytes/second } drop


Voici un moyen de faire marcher ce système entre chaque redémarrage du serveur :

* installez `nftables` et assurez-vous que la commande `nft` puisse être
  lancée par l'utilisateur lançant loult-ng sans entrer de mot de passe
* copiez `nftables.sample.conf` sur `/etc/nftables.conf`
* lancez `systemctl enable nftables` puis `systemctl restart nftables`

# Détails sur le fonctionnement

* Les joueurs peuvent s'attaquer les uns les autres en lançant la commande
`/attack Taupiqueur`
S'il y a plusieurs pokémons à ce nom dans le chat, on peut rajouter son numéro dans la liste
`/attack Taupiqueur 3`
Ce qui attaquera le 3ème Taupiqueur dans la liste
* On peut paramétrer le "temps de récupération" entre les attaques dans config.py (en seconde)

# Codes d'erreur

L'application définit des codes d'erreurs spéciaux lors de la fermeture forcée d'un websocket :

| code | signification             |
|------|---------------------------|
| 4000 | Erreur inattendue         |
| 4001 | JSON malformé             |
| 4002 | Données binaires refusées |
| 4003 | Type de commande inconnu  |
| 4004 | Banni pour flood          |


D'après une œuvre de *@DrEmixam*.

