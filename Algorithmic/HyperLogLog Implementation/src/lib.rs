use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

/// HyperLogLog is a probabilistic data structure for estimating the cardinality of a set.
/// It uses significantly less memory than storing the set itself.
pub struct HyperLogLog {
    b: u8,             // Number of bits used for the register index
    m: usize,          // Number of registers (2^b)
    registers: Vec<u8>, // The registers storing the max leading zeros
    alpha_m: f64,      // Correction constant
}

impl HyperLogLog {
    /// Creates a new HyperLogLog with a specified error rate.
    /// The error rate determines the number of registers used.
    /// Typical error rate is 0.01 (1%).
    ///
    /// # Arguments
    ///
    /// * `error_rate` - The desired standard error (e.g., 0.01). Must be between 0 and 1.
    pub fn new(error_rate: f64) -> Self {
        // Formula: error_rate approx 1.04 / sqrt(m)
        // => m = (1.04 / error_rate)^2
        // m must be a power of 2, so we find the nearest power of 2.
        let m_float = (1.04 / error_rate).powi(2);
        let b = m_float.log2().ceil() as u8;

        // Enforce reasonable bounds for b (e.g., 4..=16)
        let b = b.clamp(4, 16);
        let m = 1 << b;

        let alpha_m = match m {
            16 => 0.673,
            32 => 0.697,
            64 => 0.709,
            _ => 0.7213 / (1.0 + 1.079 / m as f64),
        };

        HyperLogLog {
            b,
            m,
            registers: vec![0; m],
            alpha_m,
        }
    }

    /// Adds an item to the HyperLogLog sketch.
    pub fn add<T: Hash + ?Sized>(&mut self, item: &T) {
        let mut hasher = DefaultHasher::new();
        item.hash(&mut hasher);
        let hash = hasher.finish(); // u64 hash

        // Extract the first b bits to determine the register index
        let j = (hash >> (64 - self.b)) as usize;

        // Use the remaining bits to count leading zeros
        // We mask out the first b bits, then count leading zeros + 1
        // Since we used high bits for index, we look at the lower (64 - b) bits.
        // Or, technically, HLL usually says "w is the number of leading zeros in the binary representation of the rest".
        // Since we used the top b bits, we can shift left by b and count leading zeros of the result.
        // Note: if the remaining bits are all 0, leading_zeros is 64.
        // But the max rank we can store is usually small (e.g., 5 bits for 32 registers, but we have u8).
        // We usually define rank = leading_zeros + 1.

        // Shift hash left by b to remove the index bits from the MSB position.
        // The relevant bits are now at the beginning of the 64-bit word.
        let w = hash << self.b;

        // Count leading zeros on the modified hash.
        // If w is 0, all remaining bits were 0. rank is (64 - b) + 1.
        // However, trailing bits of the original hash are what matters.
        // Let's stick to the standard:
        // x = hash
        // j = <first b bits>
        // w = <remaining bits>
        // rho(w) = position of leftmost 1-bit in w (1-indexed).

        // In our case, we shifted left, so the "remaining bits" are now at the top.
        // So leading_zeros() gives the number of 0s before the first 1.
        // +1 gives the 1-based index.
        let zeros = w.leading_zeros() as u8;
        let rank = zeros + 1;

        if rank > self.registers[j] {
            self.registers[j] = rank;
        }
    }

    /// Estimates the cardinality of the set.
    pub fn count(&self) -> u64 {
        let m = self.m as f64;
        let sum_inverse_powers: f64 = self.registers.iter()
            .map(|&val| 2.0f64.powi(-(val as i32)))
            .sum();

        let raw_estimate = self.alpha_m * m * m / sum_inverse_powers;

        // Corrections
        if raw_estimate <= 2.5 * m {
            // Small range correction
            let v = self.registers.iter().filter(|&&r| r == 0).count();
            if v > 0 {
                (m * (m / v as f64).ln()) as u64
            } else {
                raw_estimate as u64
            }
        } else if raw_estimate > (1.0 / 30.0) * 2.0f64.powi(32) {
            // Large range correction (for 32-bit hashes, but we use 64-bit...
            // actually standard correction is for 32-bit limit.
            // With 64-bit hash, this is rarely hit unless N is huge.
            // We'll leave it as raw_estimate or implement 64-bit logic if needed.
            // The threshold above is ~143 million.
            // For 64-bit, the range is huge. We usually don't need the large range correction
            // unless we approach 2^64 items.
            raw_estimate as u64
        } else {
            raw_estimate as u64
        }
    }

    /// Merges another HyperLogLog into this one.
    /// Both must have the same configuration (b/m).
    pub fn merge(&mut self, other: &HyperLogLog) -> Result<(), String> {
        if self.m != other.m {
            return Err("Cannot merge HyperLogLogs with different precision".to_string());
        }

        for i in 0..self.m {
            if other.registers[i] > self.registers[i] {
                self.registers[i] = other.registers[i];
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::Rng;
    use std::collections::HashSet;

    #[test]
    fn test_initialization() {
        let hll = HyperLogLog::new(0.01);
        assert!(hll.m > 0);
        assert_eq!(hll.registers.len(), hll.m);
    }

    #[test]
    fn test_small_cardinality() {
        let mut hll = HyperLogLog::new(0.05); // Lower precision for test speed if needed
        let items = vec!["apple", "banana", "cherry", "date", "elderberry"];

        for item in &items {
            hll.add(item);
        }

        let count = hll.count();
        // For very small sets, the correction should be quite accurate.
        // But it's probabilistic.
        println!("Estimated: {}, Actual: 5", count);
        // With small sets and correction, it's often exact or close.
        assert!((count as i64 - 5).abs() <= 1);
    }

    #[test]
    fn test_large_cardinality() {
        let mut hll = HyperLogLog::new(0.01);
        let mut true_set = HashSet::new();
        let mut rng = rand::rng();

        let n = 100_000;
        for _ in 0..n {
            let val: u64 = rng.random();
            true_set.insert(val);
            hll.add(&val);
        }

        let estimated = hll.count();
        let actual = true_set.len() as u64;
        let error = (estimated as f64 - actual as f64).abs() / actual as f64;

        println!("Estimated: {}, Actual: {}, Error: {:.4}", estimated, actual, error);

        // Expected error is around 1.04/sqrt(m). With 0.01 target, should be around 1%.
        // We allow a bit of margin (3 sigma is usually safe).
        assert!(error < 0.05);
    }

    #[test]
    fn test_merge() {
        let mut hll1 = HyperLogLog::new(0.05);
        let mut hll2 = HyperLogLog::new(0.05);

        for i in 0..1000 {
            hll1.add(&i);
        }
        for i in 500..1500 {
            hll2.add(&i);
        }

        hll1.merge(&hll2).unwrap();
        let count = hll1.count();

        // Union is 0..1500 -> 1500 items
        let actual = 1500;
        let error = (count as f64 - actual as f64).abs() / actual as f64;
         println!("Merged Estimated: {}, Actual: {}, Error: {:.4}", count, actual, error);
        assert!(error < 0.10); // Loose bound for small m
    }
}
