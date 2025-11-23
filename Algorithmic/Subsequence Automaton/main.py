from automaton import SubsequenceAutomaton

def main():
    text = "banana"
    print(f"Text: '{text}'")

    automaton = SubsequenceAutomaton(text)

    queries = ["ban", "ana", "nana", "band", "bnn", "aaa", "xyz"]

    for q in queries:
        is_sub = automaton.is_subsequence(q)
        indices = automaton.find_first_subsequence_indices(q)
        print(f"Query '{q}': {is_sub} {indices if indices else ''}")

if __name__ == "__main__":
    main()
