import unittest

from katalixia import RhymeTree


class TestInsertions(unittest.TestCase):

    def test_different_endings(self):
        """Tests mainly the root node's insertions"""
        endpho_word_mapping = {"o~": "camion", "t": "tente", "p": "taupe"}
        tree = RhymeTree.from_word_list(endpho_word_mapping.values())
        dict_form = tree.to_dict()
        self.assertSetEqual(set(tree.children.keys()), set(endpho_word_mapping.keys()))
        for endpho, word in endpho_word_mapping.items():
            with self.subTest(pho=word):
                self.assertEqual(tree.children[endpho].text, word)
                self.assertEqual(dict_form[endpho], word)

    def test_two_phonem_rhyme(self):
        """Tests common roots. Also kinds of tests the dict form"""
        words = ["kiff", "spliff", "taff"]
        tree = RhymeTree.from_word_list(words)
        dict_form = tree.to_dict()
        self.assertEqual(dict_form["f"]["children"]["i"]["children"]["k"], "kiff")
        self.assertEqual(dict_form["f"]["children"]["i"]["children"]["l"], "spliff")
        self.assertEqual(dict_form["f"]["children"]["a"], "taff")

    def test_node_leaf(self):
        words = ["méchant", "chant", "galant"]
        tree = RhymeTree.from_word_list(words)
        self.assertEqual(tree["a~"]["S"].leaves[0].text, "chant")
        self.assertEqual(tree["a~"]["l"].text, "galant")


class TestRhymeSearch(unittest.TestCase):

    def setUp(self):
        wordlist = ["marteau", "bateau", "apollo", "polo", "rire", "avenir", "sourire"]
        self.tree = RhymeTree.from_word_list(wordlist)

    def test_single_rhyme(self):
        single_rhymes_couples = [("gateau", "bateau"), ("pourrir", "sourire")]
        for search_word, target in single_rhymes_couples:
            with self.subTest(search_word=search_word):
                self.assertEqual(self.tree.find_rhyme(search_word), target)

    def test_random_rhyme(self):
        single_rhymes_couples = [("peau", ["marteau", "bateau", "apollo", "polo"]),
                                 ("ire", ["rire", "avenir", "sourire"])]
        for search_word, target in single_rhymes_couples:
            with self.subTest(search_word=search_word):
                self.assertIn(self.tree.find_rhyme(search_word), target)


