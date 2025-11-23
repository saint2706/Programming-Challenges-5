from regex_engine import RegexEngine

def main():
    patterns = [
        ("a*b", ["b", "ab", "aab", "aaab", "ac"]),
        ("a|b", ["a", "b", "c"]),
        ("(ab)*", ["", "ab", "abab", "aba"]),
        ("a(b|c)*d", ["ad", "abd", "acd", "abbcd", "axd"])
    ]

    for pat, tests in patterns:
        print(f"Pattern: {pat}")
        engine = RegexEngine(pat)
        for t in tests:
            result = engine.match(t)
            print(f"  Match '{t}': {result}")

if __name__ == "__main__":
    main()
