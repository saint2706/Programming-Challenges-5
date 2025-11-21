use std::collections::{HashMap, HashSet};

/// A literal is a variable ID and a boolean indicating if it's negated.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct Literal {
    pub id: usize,
    pub negated: bool,
}

impl Literal {
    pub fn new(id: usize, negated: bool) -> Self {
        Literal { id, negated }
    }

    pub fn not(&self) -> Self {
        Literal {
            id: self.id,
            negated: !self.negated,
        }
    }
}

/// A clause is a disjunction of literals (L1 OR L2 OR ...).
pub type Clause = Vec<Literal>;

/// A SAT problem instance (CNF formula).
pub struct SatSolver {
    clauses: Vec<Clause>,
    num_vars: usize,
}

#[derive(Clone, Debug, PartialEq)]
pub enum Solution {
    Satisfiable(HashMap<usize, bool>),
    Unsatisfiable,
}

impl SatSolver {
    pub fn new(num_vars: usize) -> Self {
        SatSolver {
            clauses: Vec::new(),
            num_vars,
        }
    }

    pub fn add_clause(&mut self, clause: Clause) {
        self.clauses.push(clause);
    }

    pub fn solve(&self) -> Solution {
        self.dpll_solve(self.clauses.clone(), HashMap::new())
    }

    fn dpll_solve(&self, mut clauses: Vec<Clause>, mut assignment: HashMap<usize, bool>) -> Solution {
        // 1. Unit Propagation
        loop {
            let mut unit_lit = None;
            for clause in &clauses {
                if clause.len() == 1 {
                    unit_lit = Some(clause[0]);
                    break;
                }
            }

            if let Some(lit) = unit_lit {
                let val = !lit.negated;
                // Check for conflict
                if let Some(&existing) = assignment.get(&lit.id) {
                    if existing != val {
                         return Solution::Unsatisfiable;
                    }
                }
                assignment.insert(lit.id, val);

                // Simplify clauses
                if !self.simplify(&mut clauses, lit) {
                    return Solution::Unsatisfiable; // Empty clause generated -> unsat
                }
                if clauses.is_empty() {
                    return Solution::Satisfiable(assignment);
                }
            } else {
                break;
            }
        }

        // 2. Pure Literal Elimination (Optional but good)
        // Skip for simple DPLL or implement?
        // Let's implement minimal branching first.

        // Check if empty clause (unsat)
        if clauses.iter().any(|c| c.is_empty()) {
            return Solution::Unsatisfiable;
        }
        // Check if no clauses (sat)
        if clauses.is_empty() {
            return Solution::Satisfiable(assignment);
        }

        // 3. Branching
        // Pick a variable not in assignment
        // Find first variable appearing in first clause?
        let var = clauses[0][0].id;

        // Try true
        let mut left_clauses = clauses.clone();
        let mut left_assignment = assignment.clone();
        left_assignment.insert(var, true);
        let lit_true = Literal::new(var, false);
        if self.simplify(&mut left_clauses, lit_true) {
             if let Solution::Satisfiable(res) = self.dpll_solve(left_clauses, left_assignment) {
                 return Solution::Satisfiable(res);
             }
        }

        // Try false
        let mut right_clauses = clauses; // move clauses
        let mut right_assignment = assignment;
        right_assignment.insert(var, false);
        let lit_false = Literal::new(var, true);
         if self.simplify(&mut right_clauses, lit_false) {
             return self.dpll_solve(right_clauses, right_assignment);
         }

        Solution::Unsatisfiable
    }

    /// Simplifies clauses given a literal assignment.
    /// Returns false if an empty clause is generated (conflict).
    fn simplify(&self, clauses: &mut Vec<Clause>, lit: Literal) -> bool {
        // Remove clauses containing lit (they are satisfied)
        clauses.retain(|c| !c.contains(&lit));

        // Remove !lit from clauses (it cannot be true)
        let not_lit = lit.not();
        for clause in clauses.iter_mut() {
            if let Some(pos) = clause.iter().position(|&l| l == not_lit) {
                clause.remove(pos);
                if clause.is_empty() {
                    return false;
                }
            }
        }
        true
    }

    // Helper for initial call
    fn dpll(&self, _clauses: &[Clause], _assignments: HashMap<usize, bool>) -> bool {
        // Deprecated, using dpll_solve
        false
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simple_sat() {
        // (x1 or x2) AND (!x1 or x2)
        // Solution: x2 must be true. x1 can be true or false (if x2 is true, both satisfied).
        // Let's trace:
        // Clause 1: x2=true -> sat.
        // Clause 2: x2=true -> sat.
        // So x2=true is needed? No, if x1=true, C1 sat. C2 needs x2=true.
        // If x1=false, C2 sat. C1 needs x2=true.
        // In both cases x2 must be true.

        let mut solver = SatSolver::new(2);
        solver.add_clause(vec![Literal::new(1, false), Literal::new(2, false)]); // x1 or x2
        solver.add_clause(vec![Literal::new(1, true), Literal::new(2, false)]);  // !x1 or x2

        match solver.solve() {
            Solution::Satisfiable(assign) => {
                assert_eq!(assign.get(&2), Some(&true));
            },
            Solution::Unsatisfiable => panic!("Should be satisfiable"),
        }
    }

    #[test]
    fn test_unsat() {
        // x1 AND !x1
        let mut solver = SatSolver::new(1);
        solver.add_clause(vec![Literal::new(1, false)]);
        solver.add_clause(vec![Literal::new(1, true)]);

        match solver.solve() {
            Solution::Satisfiable(_) => panic!("Should be unsatisfiable"),
            Solution::Unsatisfiable => {},
        }
    }
}
