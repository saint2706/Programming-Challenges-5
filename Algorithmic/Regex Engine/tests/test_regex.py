import unittest
from regex_engine import RegexEngine

class TestRegexEngine(unittest.TestCase):
    def test_literal(self):
        engine = RegexEngine("a")
        self.assertTrue(engine.match("a"))
        self.assertFalse(engine.match("b"))
        self.assertFalse(engine.match("aa"))

    def test_concat(self):
        engine = RegexEngine("ab")
        self.assertTrue(engine.match("ab"))
        self.assertFalse(engine.match("a"))
        self.assertFalse(engine.match("b"))
        self.assertFalse(engine.match("ba"))

    def test_union(self):
        engine = RegexEngine("a|b")
        self.assertTrue(engine.match("a"))
        self.assertTrue(engine.match("b"))
        self.assertFalse(engine.match("c"))
        self.assertFalse(engine.match("ab")) # Matches full string check? Logic assumes full string consumption?
        # My implementation of match loops through text and checks if FINAL state is in active set.
        # But if text has characters left?
        # My current implementation consumes the whole text.
        # "ab" -> after 'a', state is in 'a' final (or epsilon to end). 'b' has no transition.
        # So it returns False. Correct.

    def test_star(self):
        engine = RegexEngine("a*")
        self.assertTrue(engine.match(""))
        self.assertTrue(engine.match("a"))
        self.assertTrue(engine.match("aaaa"))
        self.assertFalse(engine.match("b"))
        self.assertFalse(engine.match("aaab"))

    def test_grouping(self):
        engine = RegexEngine("(ab)*")
        self.assertTrue(engine.match(""))
        self.assertTrue(engine.match("ab"))
        self.assertTrue(engine.match("abab"))
        self.assertFalse(engine.match("aba"))

    def test_complex(self):
        engine = RegexEngine("a(b|c)*d")
        self.assertTrue(engine.match("ad"))
        self.assertTrue(engine.match("abd"))
        self.assertTrue(engine.match("acd"))
        self.assertTrue(engine.match("abbccd"))
        self.assertFalse(engine.match("add"))

if __name__ == '__main__':
    unittest.main()
