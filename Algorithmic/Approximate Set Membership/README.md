🔬 Advanced Testing and Benchmarking

```python
class AdvancedBloomFilterTests:
    """Advanced testing utilities for Bloom Filter performance analysis."""
    
    @staticmethod
    def stress_test_bloom_filter():
        """Stress test the Bloom Filter with large datasets."""
        print("🚀 STRESS TESTING BLOOM FILTER")
        print("=" * 40)
        
        # Test with 1 million elements
        large_capacity = 1000000
        bf_large = BloomFilter(large_capacity, 0.01)
        
        # Generate large dataset
        print("Generating test data...")
        test_data = [str(i) for i in range(large_capacity)]
        
        # Add elements
        print("Adding elements to Bloom Filter...")
        for i, item in enumerate(test_data):
            bf_large.add(item)
            if i % 100000 == 0 and i > 0:
                print(f"  Added {i} elements...")
        
        # Test false positives
        print("Testing false positive rate...")
        false_positives = 0
        test_size = 10000
        negative_test_data = [f"negative_{i}" for i in range(test_size)]
        
        for item in negative_test_data:
            if bf_large.contains(item):
                false_positives += 1
        
        actual_fpr = false_positives / test_size
        print(f"Results for {large_capacity:,} elements:")
        print(f"  Actual FPR: {actual_fpr:.6f}")
        print(f"  Theoretical FPR: {bf_large.actual_false_positive_rate():.6f}")
        print(f"  Bit density: {bf_large.bit_array_density():.4f}")
        print(f"  Memory used: ~{bf_large.size / 8 / 1024 / 1024:.2f} MB")
    
    @staticmethod
    def hash_function_analysis():
        """Analyze the distribution and collision properties of hash functions."""
        print("\n🔍 HASH FUNCTION ANALYSIS")
        print("=" * 35)
        
        bf = BloomFilter(1000, 0.01)
        test_items = [f"test_item_{i}" for i in range(1000)]
        
        position_distribution = defaultdict(int)
        
        for item in test_items:
            positions = bf._get_hash_positions(item)
            for pos in positions:
                position_distribution[pos] += 1
        
        # Analyze distribution
        positions_used = len(position_distribution)
        avg_hits = sum(position_distribution.values()) / len(position_distribution)
        max_hits = max(position_distribution.values())
        
        print(f"Hash Function Distribution Analysis:")
        print(f"  Total bit positions: {bf.size}")
        print(f"  Positions actually used: {positions_used} ({positions_used/bf.size*100:.1f}%)")
        print(f"  Average hits per position: {avg_hits:.2f}")
        print(f"  Maximum hits to single position: {max_hits}")
        print(f"  Ideal distribution would be ~{len(test_items) * bf.hash_count / bf.size:.2f} hits/position")

# Run advanced tests
if __name__ == "__main__":
    # Run the main demonstration
    demonstration()
    
    # Run advanced tests
    advanced_tests = AdvancedBloomFilterTests()
    advanced_tests.stress_test_bloom_filter()
    advanced_tests.hash_function_analysis()
```

📊 Key Features Implemented

1. Core Bloom Filter

· ✅ Optimal parameter calculation using mathematical formulas

· ✅ Multiple hash functions using MurmurHash3 with different seeds

· ✅ Efficient bit array implementation

· ✅ Add and contains operations

2. False Positive Analysis

· ✅ Theoretical FPR calculation

· ✅ Empirical FPR testing

· ✅ Comprehensive parameter sweeps

· ✅ Statistical analysis

3. Visualization

· ✅ Bit array visualization

· ✅ FPR performance charts

· ✅ Memory efficiency comparisons

· ✅ Hash function distribution analysis

4. Advanced Features

· ✅ Stress testing with large datasets

· ✅ Memory efficiency benchmarking

· ✅ Hash collision analysis

· ✅ Performance profiling

🎯 Expected Output

When you run this implementation, you'll see:

1. Basic functionality demo showing add/contains operations
2. False positive rate analysis across different parameters
3. Beautiful visualizations of performance metrics
4. Memory efficiency comparisons showing 10-100x savings
5. Stress test results with 1 million elements
6. Hash function distribution analysis
