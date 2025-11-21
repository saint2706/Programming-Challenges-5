use std::cmp::min;

/// Justifies text into a list of lines with a maximum width.
/// Uses a dynamic programming approach to minimize "badness" (sum of squares of extra spaces).
pub struct TextJustifier {
    width: usize,
}

impl TextJustifier {
    pub fn new(width: usize) -> Self {
        TextJustifier { width }
    }

    pub fn justify(&self, text: &str) -> Vec<String> {
        let words: Vec<&str> = text.split_whitespace().collect();
        let n = words.len();
        if n == 0 {
            return vec![];
        }

        // dp[i] = min badness cost for words[i..]
        let mut dp = vec![f64::MAX; n + 1];
        // split[i] = index of the first word of the NEXT line
        let mut split = vec![0; n + 1];

        dp[n] = 0.0;

        for i in (0..n).rev() {
            let mut length = 0; // char count
            for j in i..n {
                // Add length of words[j]
                if j > i {
                    length += 1; // Space between words
                }
                length += words[j].len();

                if length > self.width {
                    break;
                }

                // Cost calculation
                // Badness = (width - length)^2
                // Last line exception: usually we don't penalize the last line if it's short?
                // Or standard Knuth-Plass uses cubed or squared.
                // If j == n-1 (last word included), cost is usually 0.
                let cost = if j == n - 1 {
                    0.0
                } else {
                    let gaps = (self.width - length) as f64;
                    gaps.powi(2)
                };

                if dp[j + 1] != f64::MAX {
                    let total_cost = cost + dp[j + 1];
                    if total_cost < dp[i] {
                        dp[i] = total_cost;
                        split[i] = j + 1;
                    }
                }
            }
        }

        // Reconstruct lines
        let mut lines = Vec::new();
        let mut i = 0;
        while i < n {
            let next_i = split[i];
            let line_words = &words[i..next_i];

            // If it's the last line, left justify
            if next_i == n {
                let mut line = line_words.join(" ");
                // Optional: pad with spaces to width? Usually last line is not fully justified.
                // But "justified" usually means block. However, standard rule is last line left-aligned.
                lines.push(line);
            } else {
                // Fully justify
                lines.push(self.format_line(line_words, self.width));
            }
            i = next_i;
        }

        lines
    }

    fn format_line(&self, words: &[&str], width: usize) -> String {
        if words.len() == 1 {
            let mut s = words[0].to_string();
            s.push_str(&" ".repeat(width - s.len()));
            return s;
        }

        let total_chars: usize = words.iter().map(|w| w.len()).sum();
        let total_spaces = width - total_chars;
        let gaps = words.len() - 1;

        let space_per_gap = total_spaces / gaps;
        let extra_spaces = total_spaces % gaps;

        let mut s = String::new();
        for (i, word) in words.iter().enumerate() {
            s.push_str(word);
            if i < gaps {
                let spaces = space_per_gap + if i < extra_spaces { 1 } else { 0 };
                s.push_str(&" ".repeat(spaces));
            }
        }
        s
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simple_justification() {
        let justifier = TextJustifier::new(10);
        let text = "This is a test.";
        let lines = justifier.justify(text);

        // "This is a" -> 9 chars
        // "test." -> 5 chars
        assert_eq!(lines.len(), 2);
        assert_eq!(lines[0], "This  is a"); // 4+2+2+1+1 = 10?
        // "This"(4) + " "(1) + "is"(2) + " "(1) + "a"(1) = 9.
        // Width 10. 1 extra space.
        // 2 gaps ("This_is_a"). Gaps=2. Spaces=1.
        // Actually logic: 3 words -> 2 gaps.
        // total_chars = 4+2+1 = 7.
        // total_spaces = 10 - 7 = 3.
        // space_per_gap = 3/2 = 1.
        // extra = 1.
        // Gap 0: 1+1 = 2 spaces. Gap 1: 1 space.
        // "This  is a" -> 4+2+2+1+1 = 10. Correct.
        assert_eq!(lines[1], "test."); // Last line left aligned
    }

    #[test]
    fn test_greedy_vs_dp() {
        // Example where greedy fails but DP works well?
        // Text: "aaa bb cc ddddd" Width: 6
        // Greedy:
        // "aaa bb" (6)
        // "cc" (2)
        // "ddddd" (5)
        // Costs: 0^2 + 4^2 + 0 (last) = 16.

        // DP might choose:
        // "aaa" (3) -> cost 3^2 = 9
        // "bb cc" (5) -> cost 1^2 = 1
        // "ddddd" (5) -> cost 0
        // Total 10.
        // So DP should prefer "aaa \n bb cc \n ddddd"

        let justifier = TextJustifier::new(6);
        let text = "aaa bb cc ddddd";
        let lines = justifier.justify(text);

        assert_eq!(lines[0].trim(), "aaa"); // Should put aaa alone?
        // Wait, let's trace format logic.
        // "aaa" padded to 6 is "aaa   ".
        // "bb cc" padded to 6 is "bb  cc". (2+2+2 = 6) or (2+1+2 = 5)?
        // total chars 4. spaces 2. gap 1. 2 spaces.

        assert_eq!(lines.len(), 3);
        assert_eq!(lines[0].trim(), "aaa");
        assert_eq!(lines[1], "bb  cc");
    }
}
