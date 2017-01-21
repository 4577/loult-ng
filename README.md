La partie client est en HTML/CSS/JS statique et la partie serveur en Python.

# Mise en place

* Installer nginx, python3-scipy, mbrola (avec voix fr/es/us/de), 
espeak, sox (sur gestionnaire de paquet debian):
`sudo apt-get install nginx python3-scipy python3-autobahn mbrola espeak sox \
mbrola-fr1 mbrola-us1 mbrola-es1 mbrola-de4 python3-venv`

mkdir -p loult/venv
cd loult
git clone https://github.com/4577/loult-ng.git
python3 -m venv venv
source venv/bin/activate

* Installer, via pip3, `pysndfx` et `autobahn`
pip3 install -r requirements.txt
* Créer un fichier `salt.py` contenant `SALT = 'valeur arbitraire'`
* Configurer nginx avec `loult.conf`, adapter le chemin de $static
mv loult.conf /etc/nginx/site-available/
ln -s /etc/nginx/site-available/ /etc/nginx/site-enabled
* Lancer `poke.py`

# Détails sur le fonctionnement

* Les joueurs peuvent s'attaquer les uns les autres en lançant la commande
`/attack Taupiqueur`
S'il y a plusieurs pokémons à ce nom dans le chat, on peut rajouter son numéro dans la liste
`/attack Taupiqueur 3`
Ce qui attaquera le 3ème Taupiqueur dans la liste
* On peut paramétrer le "temps de récupération" entre les attaques dans config.py (en seconde)


D'après une œuvre de *@DrEmixam*.

