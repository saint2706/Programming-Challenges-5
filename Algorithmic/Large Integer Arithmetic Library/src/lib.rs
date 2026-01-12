use std::cmp::max;
use std::fmt;
use std::ops::{Add, Mul, Sub};

/// A large integer represented by a vector of digits.
/// Base is 10 for simplicity in string conversion, though 2^32 or 2^64 is better for performance.
/// We will use base 10 to keep it simple and readable as an algorithmic challenge.
#[derive(Clone, Debug, PartialEq)]
pub struct BigInt {
    digits: Vec<u8>, // Stored in reverse order (little endian), so index 0 is units place.
    is_negative: bool,
}

impl BigInt {
    pub fn new(s: &str) -> Self {
        if s.is_empty() {
            return BigInt {
                digits: vec![0],
                is_negative: false,
            };
        }

        let mut chars = s.chars().peekable();
        let is_negative = if *chars.peek().unwrap() == '-' {
            chars.next();
            true
        } else {
            false
        };

        let mut digits = Vec::new();
        for c in chars {
            if let Some(d) = c.to_digit(10) {
                digits.push(d as u8);
            } else {
                // Ignore non-digits or panic? Let's ignore for robustness
            }
        }
        digits.reverse();

        // Normalize (remove trailing zeros in storage -> leading zeros in number)
        // E.g. "007" -> [7, 0, 0] -> [7]
        let mut bigint = BigInt {
            digits,
            is_negative,
        };
        bigint.normalize();
        bigint
    }

    pub fn from_i64(n: i64) -> Self {
        BigInt::new(&n.to_string())
    }

    fn normalize(&mut self) {
        while self.digits.len() > 1 && self.digits.last() == Some(&0) {
            self.digits.pop();
        }
        if self.digits.len() == 1 && self.digits[0] == 0 {
            self.is_negative = false;
        }
    }

    /// Compares absolute values
    fn abs_cmp(&self, other: &Self) -> std::cmp::Ordering {
        if self.digits.len() != other.digits.len() {
            return self.digits.len().cmp(&other.digits.len());
        }
        for (d1, d2) in self.digits.iter().rev().zip(other.digits.iter().rev()) {
            if d1 != d2 {
                return d1.cmp(d2);
            }
        }
        std::cmp::Ordering::Equal
    }

    // helper for adding absolute values
    fn abs_add(&self, other: &Self) -> Vec<u8> {
        let mut result = Vec::new();
        let mut carry = 0;
        let n = max(self.digits.len(), other.digits.len());

        for i in 0..n {
            let d1 = *self.digits.get(i).unwrap_or(&0);
            let d2 = *other.digits.get(i).unwrap_or(&0);
            let sum = d1 + d2 + carry;
            result.push(sum % 10);
            carry = sum / 10;
        }
        if carry > 0 {
            result.push(carry);
        }
        result
    }

    // helper for subtracting smaller abs from larger abs
    // Assumes self.abs() >= other.abs()
    fn abs_sub(&self, other: &Self) -> Vec<u8> {
        let mut result = Vec::new();
        let mut borrow = 0;

        for i in 0..self.digits.len() {
            let d1 = *self.digits.get(i).unwrap_or(&0) as i16;
            let d2 = *other.digits.get(i).unwrap_or(&0) as i16;
            let mut diff = d1 - d2 - borrow;
            if diff < 0 {
                diff += 10;
                borrow = 1;
            } else {
                borrow = 0;
            }
            result.push(diff as u8);
        }
        result
    }

    /// Karatsuba Multiplication
    /// x * y = (x1 * B + x0) * (y1 * B + y0)
    /// where B = 10^m
    /// = z2 * B^2 + z1 * B + z0
    /// z2 = x1 * y1
    /// z0 = x0 * y0
    /// z1 = (x1 + x0) * (y1 + y0) - z2 - z0
    pub fn karatsuba(x: &BigInt, y: &BigInt) -> BigInt {
        // Base case
        if x.digits.len() < 2 || y.digits.len() < 2 {
            // Fallback to simple multiplication
            return BigInt::simple_mul(x, y);
        }

        let n = max(x.digits.len(), y.digits.len());
        let m = n / 2;

        // Split
        let (x1, x0) = x.split_at(m);
        let (y1, y0) = y.split_at(m);

        // Recursion
        let z0 = BigInt::karatsuba(&x0, &y0);
        let z2 = BigInt::karatsuba(&x1, &y1);

        let x_sum = &x0 + &x1;
        let y_sum = &y0 + &y1;
        let z1_raw = BigInt::karatsuba(&x_sum, &y_sum);
        let z1 = &(&z1_raw - &z2) - &z0;

        // Reassemble: z2 * 10^(2m) + z1 * 10^m + z0
        let z2_shifted = z2.shift(2 * m);
        let z1_shifted = z1.shift(m);

        &(&z2_shifted + &z1_shifted) + &z0
    }

    fn simple_mul(x: &BigInt, y: &BigInt) -> BigInt {
        // Schoolbook for small numbers
        let mut result = vec![0; x.digits.len() + y.digits.len()];

        for (i, d1) in x.digits.iter().enumerate() {
            let mut carry = 0;
            for (j, d2) in y.digits.iter().enumerate() {
                let prod = (d1 * d2) as u16 + result[i + j] as u16 + carry;
                result[i + j] = (prod % 10) as u8;
                carry = prod / 10;
            }
            if carry > 0 {
                result[i + y.digits.len()] += carry as u8;
            }
        }

        let mut res = BigInt {
            digits: result,
            is_negative: x.is_negative ^ y.is_negative,
        };
        res.normalize();
        res
    }

    fn split_at(&self, m: usize) -> (BigInt, BigInt) {
        // Low part: digits[0..m]
        // High part: digits[m..]
        let m = std::cmp::min(m, self.digits.len());
        let low_digits = self.digits[0..m].to_vec();
        let high_digits = if m < self.digits.len() {
            self.digits[m..].to_vec()
        } else {
            vec![0]
        };

        let mut low = BigInt {
            digits: low_digits,
            is_negative: false,
        }; // Split usually ignores sign logic inside karatsuba
        let mut high = BigInt {
            digits: high_digits,
            is_negative: false,
        };
        low.normalize();
        high.normalize();
        (high, low)
    }

    fn shift(&self, power: usize) -> BigInt {
        if self.digits.len() == 1 && self.digits[0] == 0 {
            return self.clone();
        }
        let mut new_digits = vec![0; power];
        new_digits.extend(&self.digits);
        BigInt {
            digits: new_digits,
            is_negative: self.is_negative,
        }
    }
}

impl fmt::Display for BigInt {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        if self.is_negative {
            write!(f, "-")?;
        }
        for d in self.digits.iter().rev() {
            write!(f, "{}", d)?;
        }
        Ok(())
    }
}

impl Add for &BigInt {
    type Output = BigInt;

    fn add(self, other: Self) -> BigInt {
        if self.is_negative == other.is_negative {
            let digits = self.abs_add(other);
            let mut res = BigInt {
                digits,
                is_negative: self.is_negative,
            };
            res.normalize();
            res
        } else {
            // Signs differ: subtract smaller abs from larger abs
            match self.abs_cmp(other) {
                std::cmp::Ordering::Greater => {
                    let digits = self.abs_sub(other);
                    let mut res = BigInt {
                        digits,
                        is_negative: self.is_negative,
                    };
                    res.normalize();
                    res
                }
                std::cmp::Ordering::Less => {
                    let digits = other.abs_sub(self);
                    let mut res = BigInt {
                        digits,
                        is_negative: other.is_negative,
                    };
                    res.normalize();
                    res
                }
                std::cmp::Ordering::Equal => BigInt::from_i64(0),
            }
        }
    }
}

impl Sub for &BigInt {
    type Output = BigInt;

    fn sub(self, other: Self) -> BigInt {
        let negated_other = BigInt {
            digits: other.digits.clone(),
            is_negative: !other.is_negative,
        };
        self + &negated_other
    }
}

impl Mul for &BigInt {
    type Output = BigInt;

    fn mul(self, other: Self) -> BigInt {
        // To handle signs properly in Karatsuba recursion
        let mut result = BigInt::karatsuba(self, other);
        result.is_negative = self.is_negative ^ other.is_negative;
        if result.digits.len() == 1 && result.digits[0] == 0 {
            result.is_negative = false;
        }
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        let a = BigInt::from_i64(123);
        let b = BigInt::from_i64(456);
        let c = &a + &b;
        assert_eq!(c.to_string(), "579");
    }

    #[test]
    fn test_sub() {
        let a = BigInt::from_i64(100);
        let b = BigInt::from_i64(1);
        let c = &a - &b;
        assert_eq!(c.to_string(), "99");

        let d = &b - &a;
        assert_eq!(d.to_string(), "-99");
    }

    #[test]
    fn test_mul() {
        let a = BigInt::from_i64(12);
        let b = BigInt::from_i64(12);
        let c = &a * &b;
        assert_eq!(c.to_string(), "144");

        let big_a = BigInt::new("123456789");
        let big_b = BigInt::new("987654321");
        // 123456789 * 987654321 = 121932631112635269
        let big_c = &big_a * &big_b;
        assert_eq!(big_c.to_string(), "121932631112635269");
    }
}
