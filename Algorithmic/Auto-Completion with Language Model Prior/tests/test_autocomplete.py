"""
Implementation of the algorithm.
"""

import unittest
from autocomplete import AutocompleteEngine

class TestAutocomplete(unittest.TestCase):
    """
    Docstring for TestAutocomplete.
    """
    def setUp(self):
        """
        Docstring for setUp.
        """
        self.engine = AutocompleteEngine(n=2)
        corpus = [
            "hello world",
            "hello there",
            "the quick brown fox"
        ]
        self.engine.train(corpus)

    def test_basic_completion(self):
        # "he" should complete to "hello" (part of corpus)
        # Note: "hello" is in the trie.
        """
        Docstring for test_basic_completion.
        """
        results = self.engine.complete("he")
        self.assertIn("hello", results)

    def test_context_ranking(self):
        # "hello" is followed by "world" and "there" equally (1 time each).
        # "the" is followed by "quick".

        # Test "the q" -> "quick"
        """
        Docstring for test_context_ranking.
        """
        results = self.engine.complete("the q")
        self.assertEqual(results[0], "quick")

    def test_frequency_ranking(self):
        # Add "hello world" multiple times to boost "world" frequency
        """
        Docstring for test_frequency_ranking.
        """
        extra_corpus = ["hello world"] * 5
        self.engine.train(extra_corpus)

        # Now "hello w" should strongly suggest "world"
        results = self.engine.complete("hello w")
        self.assertEqual(results[0], "world")

    def test_empty_input(self):
        """
        Docstring for test_empty_input.
        """
        self.assertEqual(self.engine.complete(""), [])

    def test_unknown_prefix(self):
        """
        Docstring for test_unknown_prefix.
        """
        self.assertEqual(self.engine.complete("xyz"), [])

if __name__ == '__main__':
    unittest.main()
