Description du système d'attaque

# La phase de tirate des dés
Quand user1 attaque user2, chacun des utilisateurs renvoie 2 valeurs: 
le dé qu'il a tiré, et le bonus appliqué. Le bonus dépend de plusieurs
(et pourra dépendre de bien plus de) facteurs.

 * bonus d'attaque : bonus de temps d'inaction + bonus de niveau
 * bonus de défense : bonus de niveau

(on favorise quand même l'attaque, sinon personne prend jamais d'effets,
et c'est pas golri)

A la fin de cette phrase, on a donc, avec les deux dés de valeurs 
aléatoires tirées entre 0 et 100 inclus:

 * `BONUS_ATK`, `DICE_ATK`
 * `BONUS_DEF`, `DICE_DEF`

# Détermination de l'action suivant l'attaque
Le résultat de l'attaque est déterminée selon la suite conditionnelle
de cas suivant:

`if DICE_ATK == 100:
    -> effet global
elif DICE_ATK == 0 or DICE_DEF == 100:
    -> fumble sur l'attaquant
elif DICE_DEF == 0:
    -> fumble sur le défenseur
elif DICE_ATK + BONUS_ATK < DICE_DEF + BONUS_DEF:
    if random(0,1) == 1:
        -> rebond de l'attaque sur un joueur aléatoire (sans jet de défense)
elif DICE_ATK + BONUS_ATK > DICE_DEF + BONUS_DEF:
    -> l'attaque passe normalement`

# Description des effets spéciaux (fumble, global, rebond)

## Effet global
Tout le monde prend le même effet, lequel est choisi au hasard.
Typiquement c'est un effet un peu marrant qui fait pas trop de 
cacophonie, genre Tourette ou Crapwe

## Fumble
S'applique à un utilisateur. Il prend 4 effets aléatoires d'un coup, 
et c'est tout.

## Rebond
Un utilisateur aléatoire dans le salon se prend un effet au hasard 
(résultat classique d'une attaque mais sur un clanpin aléatoire)