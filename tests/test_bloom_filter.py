import math
import pathlib
import sys

# Ensure repository root is on the import path when pytest changes cwd.
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from approximate_set_membership.bloom import (
    BloomFilter,
    BloomFilterAnalyzer,
)


def test_bloom_filter_add_and_contains():
    """Test basic add and contains operations."""
    bf = BloomFilter(capacity=100, false_positive_rate=0.01)
    
    # Add items
    bf.add("apple")
    bf.add("banana")
    bf.add("cherry")
    
    # Check contains
    assert bf.contains("apple") is True
    assert bf.contains("banana") is True
    assert bf.contains("cherry") is True
    # Items not added should return False (no guarantee, but very likely for small sets)
    # Note: We don't test negative cases strongly due to probabilistic nature


def test_bloom_filter_density():
    """Test bit array density calculation."""
    bf = BloomFilter(capacity=100, false_positive_rate=0.1)
    
    # Empty filter should have zero density
    assert bf.bit_array_density() == 0.0
    
    # After adding items, density should increase
    for i in range(50):
        bf.add(f"item_{i}")
    
    density = bf.bit_array_density()
    assert 0 < density < 1.0


def test_false_positive_rate_reasonable():
    """Test that actual false positive rate is within reasonable bounds."""
    capacity = 1000
    target_fpr = 0.05
    
    bf = BloomFilter(capacity=capacity, false_positive_rate=target_fpr)
    
    # Add items
    for i in range(capacity):
        bf.add(f"inserted_item_{i}")
    
    # Test with items that were NOT inserted
    false_positives = 0
    test_count = 1000
    for i in range(test_count):
        if bf.contains(f"not_inserted_{i}"):
            false_positives += 1
    
    actual_fpr = false_positives / test_count
    
    # Allow some margin (actual FPR should be within 3x of target)
    assert actual_fpr < target_fpr * 3


def test_bloom_filter_analyzer():
    """Test that BloomFilterAnalyzer can generate test data and measure FPR."""
    analyzer = BloomFilterAnalyzer()
    
    # Generate test data
    test_data = analyzer.generate_test_data(100, string_length=8)
    assert len(test_data) == 100
    assert all(len(s) == 8 for s in test_data)
    
    # Test false positive rate measurement
    # Note: test_false_positive_rate adds inserted items to the bloom filter
    # so we provide empty bloom filter and let the method populate it
    bf = BloomFilter(capacity=100, false_positive_rate=0.1)
    inserted = analyzer.generate_test_data(50)
    test_items = analyzer.generate_test_data(100)
    
    actual_fpr = analyzer.test_false_positive_rate(bf, inserted, test_items)
    assert 0 <= actual_fpr <= 1.0
