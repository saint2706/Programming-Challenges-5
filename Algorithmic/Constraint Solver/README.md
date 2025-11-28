# Constraint Solver (Mini-SAT)

A SAT solver implementing the DPLL algorithm with unit propagation, pure literal elimination, and clause learning.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**SAT (Boolean Satisfiability)** asks: given a Boolean formula in CNF (Conjunctive Normal Form), is there an assignment of variables that makes it true?

### DPLL Algorithm

1. **Unit Propagation**: If a clause has only one literal, assign it to satisfy the clause
2. **Pure Literal Elimination**: If a variable appears only as positive or only as negative, assign it
3. **Branching**: Pick a variable, try both true and false
4. **Backtracking**: If a branch leads to conflict, backtrack

### Clause Learning (CDCL)

When a conflict occurs:

- Analyze the conflict to find a "learned clause"
- Add the clause to prevent repeating the same mistake
- This dramatically improves performance

## 💻 Installation

```bash
cargo build --release
cargo test
```

## 🚀 Usage

```rust
use constraint_solver::{Solver, Clause};

// Create solver
let mut solver = Solver::new();

// Add variables (returns variable IDs)
let x1 = solver.new_var();
let x2 = solver.new_var();
let x3 = solver.new_var();

// Add clauses: (x1 OR x2) AND (NOT x1 OR x3) AND (NOT x2 OR NOT x3)
solver.add_clause(vec![x1, x2]);
solver.add_clause(vec![-x1, x3]);
solver.add_clause(vec![-x2, -x3]);

// Solve
if solver.solve() {
    println!("SAT");
    println!("x1 = {}", solver.get_value(x1));
    println!("x2 = {}", solver.get_value(x2));
} else {
    println!("UNSAT");
}
```

## 📊 Complexity Analysis

| Operation      | Complexity                  |
| :------------- | :-------------------------- |
| **Worst case** | $O(2^n)$ exponential        |
| **Practical**  | Much faster with heuristics |

Where $n$ is the number of variables. Modern SAT solvers can handle millions of variables.
