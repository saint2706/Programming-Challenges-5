use std::cmp::min;

/// A struct to configure custom costs for edit operations.
pub struct EditCosts {
    pub insertion: usize,
    pub deletion: usize,
    pub substitution: usize,
}

impl Default for EditCosts {
    fn default() -> Self {
        Self {
            insertion: 1,
            deletion: 1,
            substitution: 1,
        }
    }
}

impl EditCosts {
    pub fn new(insertion: usize, deletion: usize, substitution: usize) -> Self {
        Self {
            insertion,
            deletion,
            substitution,
        }
    }
}

/// Calculates the Levenshtein distance between two strings with custom costs.
pub fn edit_distance(s1: &str, s2: &str, costs: &EditCosts) -> usize {
    let chars1: Vec<char> = s1.chars().collect();
    let chars2: Vec<char> = s2.chars().collect();
    let m = chars1.len();
    let n = chars2.len();

    // dp[i][j] = min cost to convert s1[0..i] to s2[0..j]
    let mut dp = vec![vec![0; n + 1]; m + 1];

    // Initialization
    for (i, row) in dp.iter_mut().enumerate() {
        row[0] = i * costs.deletion; // Deleting all chars from s1
    }
    for (j, cell) in dp[0].iter_mut().enumerate() {
        *cell = j * costs.insertion; // Inserting all chars into s1 to match s2
    }

    for i in 1..=m {
        for j in 1..=n {
            let cost_del = dp[i - 1][j] + costs.deletion;
            let cost_ins = dp[i][j - 1] + costs.insertion;

            let sub_cost = if chars1[i - 1] == chars2[j - 1] {
                0
            } else {
                costs.substitution
            };
            let cost_sub = dp[i - 1][j - 1] + sub_cost;

            dp[i][j] = min(cost_del, min(cost_ins, cost_sub));
        }
    }

    dp[m][n]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_standard_distance() {
        let costs = EditCosts::default();
        assert_eq!(edit_distance("kitten", "sitting", &costs), 3);
    }

    #[test]
    fn test_custom_costs() {
        // High substitution cost
        let costs = EditCosts::new(1, 1, 100);
        // "cat" -> "cut"
        // Subst: 1 * 100 = 100
        // Del+Ins: "cat" -> "ct" (1) -> "cut" (1) = 2
        assert_eq!(edit_distance("cat", "cut", &costs), 2);
    }

    #[test]
    fn test_empty_strings() {
        let costs = EditCosts::default();
        assert_eq!(edit_distance("", "", &costs), 0);
        assert_eq!(edit_distance("abc", "", &costs), 3); // 3 deletions
        assert_eq!(edit_distance("", "abc", &costs), 3); // 3 insertions
    }

    #[test]
    fn test_identical_strings() {
        let costs = EditCosts::default();
        assert_eq!(edit_distance("hello", "hello", &costs), 0);
    }
}
