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

* Créer un fichier `salt.py` contenant `SALT = 'valeur arbitraire'`
* Configurer nginx avec `loult.conf`, adapter le chemin de $static

```bash
mv loult.conf /etc/nginx/site-available/
ln -s /etc/nginx/site-available/ /etc/nginx/site-enabled
```

* Lancer `poke.py`

# Bans

Le système de ban utilise netfilter pour éviter de faire consommer
des ressources au serveur python. Il faut entrer 4 règles avec iptables
et installer `ipset`. Ces règles sont :

	-A INPUT  -m set --match-set ban src -m conntrack --ctstate ESTABLISHED,NEW -j DROP
	-A OUTPUT -m set --match-set ban src -m conntrack --ctstate ESTABLISHED -j DROP
	-A INPUT  -m set --match-set slowban src -m conntrack --ctstate ESTABLISHED,NEW -m statistic --mode random --probability 0.75 -j DROP
	-A OUTPUT -m set --match-set slowban src -m conntrack --ctstate ESTABLISHED,NEW -m statistic --mode random --probability 0.75 -j DROP

Voici un moyen de faire marcher ce système entre chaque redémarrage du serveur :

* installez `ipset` et assurez-vous qu'il est utilisable par l'utilisateur
lançant loult-ng sans entrer de mot de passe
* créez `/etc/iptables/` et copiez-y `os/iptables.rules`
* copiez `os/iptables.sevice` dans `/usr/lib/systemd/system/`
* copiez `os/iptables-reset` dans `/usr/lib/systemd/scripts/`
* lancez `chmod +x /usr/lib/systemd/scripts/iptables-reset`
* copiez `os/ipset.service` dans `/usr/lib/systemd/system/`
* lancez `systemctl daemon-reload`
* `systemctl enable iptables`
* `systemctl restart iptables`
* `systemctl enable ipset`
* `touch /etc/ipset.conf`
* vous pouvez vérifier que tout s'est bien passé en lançant `iptables-save`
* lancez `crontab -e` en tant que root et rajoutez-y

        0 1 * * * /sbin/ipset save -file /etc/ipset.conf

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


D'après une œuvre de *@DrEmixam*.

