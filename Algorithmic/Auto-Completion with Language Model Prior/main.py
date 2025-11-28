
from autocomplete import AutocompleteEngine


def main():
    engine = AutocompleteEngine(n=2)

    # Simple training corpus
    corpus = [
        "the quick brown fox jumps over the lazy dog",
        "hello world",
        "machine learning is fun",
        "artificial intelligence is the future",
        "i love python programming",
        "python is a great language",
        "the quick red fox",
        "hello there general kenobi",
    ]

    print("Training on corpus...")
    engine.train(corpus)

    print("Ready! Type a phrase ending with a prefix (e.g., 'the qu'). Ctrl+C to exit.")

    try:
        while True:
            text = input("> ")
            results = engine.complete(text)
            print(f"Suggestions: {results}")
    except KeyboardInterrupt:
        print("\nExiting.")


if __name__ == "__main__":
    main()
