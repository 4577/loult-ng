La partie client est en HTML/CSS/JS statique et la partie serveur en Python.

# Mise en place

* Installer python3, python3-autobahn
* Créer un fichier `salt.py` contenant `SALT = 'valeur arbitraire'`
* Configurer nginx avec `nginx.conf`, adapter le chemin de $static
* Lancer `poke.py`

D'après une œuvre de @DrEmixam.
