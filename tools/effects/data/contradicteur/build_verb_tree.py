from os import path
from tools.effects.tree import Leaf, Node
import pickle

###### WARNING : has to be launched from the root of the project in order for pickle
VERBS_FILEPATH =path.join(path.dirname(path.realpath(__file__)), "liste_verbes.txt")
VERBS_TREE_FILEPATH =path.join(path.dirname(path.realpath(__file__)), "liste_verbes.txt")

tree = Node()

with open(VERBS_FILEPATH) as verbs_file:
    for verb in verbs_file:
        tree.add_leaf(Leaf(verb))

pickle.dump(tree, VERBS_TREE_FILEPATH)