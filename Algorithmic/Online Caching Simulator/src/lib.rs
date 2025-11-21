use std::collections::{HashMap, VecDeque};
use std::hash::Hash;

/// A trait for cache eviction policies.
pub trait EvictionPolicy<K> {
    /// Called when a key is accessed.
    fn on_access(&mut self, key: &K);
    /// Called when a key is inserted.
    fn on_insert(&mut self, key: K);
    /// Decides which key to evict.
    fn evict(&mut self) -> Option<K>;
    /// Called when a key is removed.
    fn on_remove(&mut self, key: &K);
}

/// Least Recently Used (LRU) policy.
pub struct LRUPolicy<K> {
    // For O(1), we typically need a linked hash map.
    // Rust doesn't have a standard linked hash map.
    // We can approximate with a VecDeque for O(N) removal or use a crate like `lru`.
    // Since this is a "full implementation" challenge without external deps if possible,
    // let's implement a simple version.
    // For true O(1), we'd need unsafe or a slab + double linking.
    // For simulation purposes, O(N) search in list is acceptable if N (capacity) is small,
    // or we maintain timestamps/access counts.
    access_order: VecDeque<K>,
}

impl<K: Clone + PartialEq> LRUPolicy<K> {
    pub fn new() -> Self {
        LRUPolicy {
            access_order: VecDeque::new(),
        }
    }
}

impl<K: Clone + PartialEq> EvictionPolicy<K> for LRUPolicy<K> {
    fn on_access(&mut self, key: &K) {
        // Move to back (most recently used)
        if let Some(pos) = self.access_order.iter().position(|k| k == key) {
            let k = self.access_order.remove(pos).unwrap();
            self.access_order.push_back(k);
        }
    }

    fn on_insert(&mut self, key: K) {
        self.access_order.push_back(key);
    }

    fn evict(&mut self) -> Option<K> {
        // Remove from front (least recently used)
        self.access_order.pop_front()
    }

    fn on_remove(&mut self, key: &K) {
        if let Some(pos) = self.access_order.iter().position(|k| k == key) {
            self.access_order.remove(pos);
        }
    }
}

/// First-In, First-Out (FIFO) policy.
pub struct FIFOPolicy<K> {
    queue: VecDeque<K>,
}

impl<K> FIFOPolicy<K> {
    pub fn new() -> Self {
        FIFOPolicy {
            queue: VecDeque::new(),
        }
    }
}

impl<K: Clone + PartialEq> EvictionPolicy<K> for FIFOPolicy<K> {
    fn on_access(&mut self, _key: &K) {
        // FIFO ignores access
    }

    fn on_insert(&mut self, key: K) {
        self.queue.push_back(key);
    }

    fn evict(&mut self) -> Option<K> {
        self.queue.pop_front()
    }

    fn on_remove(&mut self, key: &K) {
        if let Some(pos) = self.queue.iter().position(|k| k == key) {
            self.queue.remove(pos);
        }
    }
}

/// The Cache Simulator.
pub struct Cache<K, V, P>
where
    K: Hash + Eq + Clone,
    P: EvictionPolicy<K>,
{
    store: HashMap<K, V>,
    policy: P,
    capacity: usize,
}

impl<K, V, P> Cache<K, V, P>
where
    K: Hash + Eq + Clone,
    P: EvictionPolicy<K>,
{
    pub fn new(capacity: usize, policy: P) -> Self {
        Cache {
            store: HashMap::new(),
            policy,
            capacity,
        }
    }

    pub fn get(&mut self, key: &K) -> Option<&V> {
        if self.store.contains_key(key) {
            self.policy.on_access(key);
            self.store.get(key)
        } else {
            None
        }
    }

    pub fn put(&mut self, key: K, value: V) {
        if self.store.contains_key(&key) {
            self.policy.on_access(&key);
            self.store.insert(key, value);
        } else {
            if self.store.len() >= self.capacity {
                if let Some(evicted) = self.policy.evict() {
                    self.store.remove(&evicted);
                }
            }
            self.policy.on_insert(key.clone());
            self.store.insert(key, value);
        }
    }

    pub fn len(&self) -> usize {
        self.store.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lru_cache() {
        let policy = LRUPolicy::new();
        let mut cache = Cache::new(2, policy);

        cache.put("A", 1);
        cache.put("B", 2);

        assert_eq!(cache.get(&"A"), Some(&1)); // A accessed, now MRU. B is LRU.

        cache.put("C", 3); // Evicts B

        assert_eq!(cache.get(&"B"), None);
        assert_eq!(cache.get(&"A"), Some(&1));
        assert_eq!(cache.get(&"C"), Some(&3));
    }

    #[test]
    fn test_fifo_cache() {
        let policy = FIFOPolicy::new();
        let mut cache = Cache::new(2, policy);

        cache.put("A", 1);
        cache.put("B", 2);

        assert_eq!(cache.get(&"A"), Some(&1)); // Access shouldn't change FIFO order

        cache.put("C", 3); // Evicts A (first in)

        assert_eq!(cache.get(&"A"), None);
        assert_eq!(cache.get(&"B"), Some(&2));
        assert_eq!(cache.get(&"C"), Some(&3));
    }
}
