from voxpopuli import Voice
from typing import Union, Dict, List


class TreeNode:

    def __init__(self):
        self.children = dict() # type:Dict[str,TreeNode]
        self.leaves = list() # type:List[Leaf]

    def insert(self, leaf: 'Leaf', current_pho_index):
        try:
            leaf_current_pho = leaf.phonems[-current_pho_index].name
        except IndexError: # if this leaf has "no more" phonems to unstack, it's stored on this node's leaves
            self.leaves.append(leaf)
            return

        if leaf_current_pho not in self.children:
            self.children[leaf_current_pho] = leaf
        else:
            current_child = self.children[leaf_current_pho]
            if isinstance(current_child, Leaf):
                new_node = TreeNode()
                new_node.insert(current_child, current_pho_index + 1)
                new_node.insert(leaf, current_pho_index + 1)
                self.children[leaf_current_pho] = new_node
            elif isinstance(current_child, TreeNode):
                current_child.insert(leaf, current_pho_index + 1)


class RootNode(TreeNode):

    def __init__(self, rhyming_lang="fr"):
        super().__init__()
        self.voice = Voice(lang=rhyming_lang)
        self.children = dict() # type:Dict[str,Union[TreeNode, Leaf]]

    def insert_rhyme(self, rhyme_string):
        new_leaf = Leaf.from_string(rhyme_string.strip(), self.voice)
        self.insert(new_leaf, 1)

    def find_rhyme(self, string):
        pass


class Leaf:

    def __init__(self, string, phonemic_form):
        self.text = string
        self.phonems = phonemic_form

    @classmethod
    def from_string(cls, string, voxpopuli_voice):
        return cls(string, voxpopuli_voice.to_phonemes(string))