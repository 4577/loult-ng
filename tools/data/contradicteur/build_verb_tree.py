from os import path

VERBS_FILEPATH =path.join(path.dirname(path.realpath(__file__)), "liste_verbes.txt")
VERBS_TREE_FILEPATH =path.join(path.dirname(path.realpath(__file__)), "liste_verbes.txt")

with open(VERBS_FILEPATH) as verbs_file:
    for verb in verbs_file:
        pass