import unittest

from automaton import SubsequenceAutomaton


class TestSubsequenceAutomaton(unittest.TestCase):
    def setUp(self):
        self.text = "abracadabra"
        self.automaton = SubsequenceAutomaton(self.text)

    def test_is_subsequence(self):
        # True cases
        self.assertTrue(self.automaton.is_subsequence("abra"))
        self.assertTrue(self.automaton.is_subsequence("brac"))
        self.assertTrue(self.automaton.is_subsequence("aaaa"))
        self.assertTrue(self.automaton.is_subsequence("rada"))
        self.assertTrue(self.automaton.is_subsequence(""))

        # False cases
        self.assertFalse(self.automaton.is_subsequence("zebra"))  # 'z' not in text
        self.assertFalse(self.automaton.is_subsequence("abbb"))  # only 2 b's
        self.assertFalse(self.automaton.is_subsequence("dabrax"))

    def test_indices(self):
        # "ada" -> first 'a' at 0, then 'd' at 6, then 'a' at 7
        # Wait, strictly greedy:
        # 'a' -> index 0
        # 'd' -> search after 0+1=1. First 'd' is at 6.
        # 'a' -> search after 6+1=7. First 'a' is at 7.
        indices = self.automaton.find_first_subsequence_indices("ada")
        self.assertEqual(indices, [0, 6, 7])

    def test_empty_text(self):
        auto = SubsequenceAutomaton("")
        self.assertTrue(auto.is_subsequence(""))
        self.assertFalse(auto.is_subsequence("a"))


if __name__ == "__main__":
    unittest.main()
