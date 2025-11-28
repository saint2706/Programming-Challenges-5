"""
Implementation of the algorithm.
"""

from typing import List, Dict, Set, Optional, Tuple

class State:
    """
    Docstring for State.
    """
    def __init__(self, label=None, is_final=False):
        """
        Docstring for __init__.
        """
        self.label = label
        self.is_final = is_final
        # transitions: input_char -> list of next states
        # None key represents epsilon transition
        self.transitions: Dict[Optional[str], List['State']] = {}

    def add_transition(self, char: Optional[str], state: 'State'):
        """
        Docstring for add_transition.
        """
        if char not in self.transitions:
            self.transitions[char] = []
        self.transitions[char].append(state)

class NFA:
    """
    Docstring for NFA.
    """
    def __init__(self, start: State, end: State):
        """
        Docstring for __init__.
        """
        self.start = start
        self.end = end

class RegexEngine:
    """
    A basic regex engine supporting concatenation, union (|), closure (*), and grouping (()).
    Compiles to NFA using Thompson's Construction.
    """

    def __init__(self, pattern: str):
        """
        Docstring for __init__.
        """
        self.pattern = pattern
        self.nfa = self._compile_to_nfa(pattern)

    def _compile_to_nfa(self, pattern: str) -> NFA:
        """Parses the pattern and builds an NFA."""
        # This requires a parser (Shunting-yard or recursive descent) to handle precedence.
        # Precedence: * (highest), concatenation, | (lowest).

        # 1. Preprocess: Insert explicit concatenation markers ('.')
        postfix = self._to_postfix(pattern)

        # 2. Evaluate postfix to build NFA
        stack: List[NFA] = []

        for char in postfix:
            if char == '.':
                right = stack.pop()
                left = stack.pop()
                stack.append(self._concat(left, right))
            elif char == '|':
                right = stack.pop()
                left = stack.pop()
                stack.append(self._union(left, right))
            elif char == '*':
                nfa = stack.pop()
                stack.append(self._star(nfa))
            else:
                # Literal
                stack.append(self._literal(char))

        if not stack:
             # Empty pattern matches empty string
             s = State(is_final=True)
             return NFA(s, s)

        return stack.pop()

    def _to_postfix(self, pattern: str) -> str:
        """Converts regex to postfix notation with explicit concatenation '.'."""
        output = []
        operator_stack = []

        # Preprocess to add explicit concatenation
        # e.g., "ab" -> "a.b", "a(b)" -> "a.(b)", "a|b" -> "a|b"
        processed = []
        for i, char in enumerate(pattern):
            processed.append(char)
            if i + 1 < len(pattern):
                next_char = pattern[i+1]
                is_curr_literal = char not in '(|'
                is_next_literal = next_char not in ')|*'

                # Add concat if:
                # Literal followed by Literal (a b)
                # Literal followed by ( (a (b))
                # * followed by Literal (* a)
                # * followed by ( (* (b))
                # ) followed by Literal
                # ) followed by (

                if (char not in '(|') and (next_char not in ')|*'):
                     processed.append('.')
                elif (char == '*') and (next_char == '('):
                     processed.append('.')
                elif (char == ')') and (next_char == '('):
                     processed.append('.')
                elif (char == ')') and (next_char not in ')|*'):
                     processed.append('.')

        # Now classic Shunting-yard
        precedence = {'*': 3, '.': 2, '|': 1, '(': 0}

        for char in processed:
            if char not in '.*|()':
                output.append(char)
            elif char == '(':
                operator_stack.append(char)
            elif char == ')':
                while operator_stack and operator_stack[-1] != '(':
                    output.append(operator_stack.pop())
                operator_stack.pop() # Pop '('
            else:
                while (operator_stack and
                       precedence.get(operator_stack[-1], 0) >= precedence.get(char, 0)):
                    output.append(operator_stack.pop())
                operator_stack.append(char)

        while operator_stack:
            output.append(operator_stack.pop())

        return "".join(output)

    # Thompson's Constructions
    def _literal(self, char: str) -> NFA:
        """
        Docstring for _literal.
        """
        start = State()
        end = State(is_final=True)
        start.add_transition(char, end)
        return NFA(start, end)

    def _concat(self, first: NFA, second: NFA) -> NFA:
        # first.end -> second.start (epsilon)
        """
        Docstring for _concat.
        """
        first.end.is_final = False
        first.end.add_transition(None, second.start)
        return NFA(first.start, second.end)

    def _union(self, first: NFA, second: NFA) -> NFA:
        """
        Docstring for _union.
        """
        start = State()
        end = State(is_final=True)

        # start -> first.start
        # start -> second.start
        start.add_transition(None, first.start)
        start.add_transition(None, second.start)

        first.end.is_final = False
        second.end.is_final = False

        first.end.add_transition(None, end)
        second.end.add_transition(None, end)

        return NFA(start, end)

    def _star(self, nfa: NFA) -> NFA:
        """
        Docstring for _star.
        """
        start = State()
        end = State(is_final=True)

        # start -> nfa.start
        start.add_transition(None, nfa.start)
        # start -> end (match zero times)
        start.add_transition(None, end)

        nfa.end.is_final = False
        # nfa.end -> nfa.start (loop)
        nfa.end.add_transition(None, nfa.start)
        # nfa.end -> end (finish)
        nfa.end.add_transition(None, end)

        return NFA(start, end)

    def match(self, text: str) -> bool:
        """Simulates the NFA to check for a match."""
        # Current set of states (epsilon closure)
        current_states = self._epsilon_closure({self.nfa.start})

        for char in text:
            next_states = set()
            for state in current_states:
                if char in state.transitions:
                    for next_state in state.transitions[char]:
                        next_states.add(next_state)

            # Update with epsilon closure
            current_states = self._epsilon_closure(next_states)

            if not current_states:
                return False

        # Check if any current state is final
        return any(s.is_final for s in current_states)

    def _epsilon_closure(self, states: Set[State]) -> Set[State]:
        """
        Docstring for _epsilon_closure.
        """
        stack = list(states)
        closure = set(states)

        while stack:
            state = stack.pop()
            if None in state.transitions:
                for next_state in state.transitions[None]:
                    if next_state not in closure:
                        closure.add(next_state)
                        stack.append(next_state)
        return closure
