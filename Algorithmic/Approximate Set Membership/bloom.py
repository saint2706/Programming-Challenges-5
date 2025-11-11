import mmh3
import math
import random
import string
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Any, Callable
from collections import defaultdict
import seaborn as sns

class BloomFilter:
    """
    A space-efficient probabilistic data structure for approximate set membership testing.
    Supports false positive rate analysis and visualization.
    """
    
    def __init__(self, capacity: int, false_positive_rate: float = 0.01):
        """
        Initialize Bloom Filter with optimal parameters.
        
        Args:
            capacity: Expected number of elements to store
            false_positive_rate: Desired maximum false positive probability
        """
        self.capacity = capacity
        self.false_positive_rate = false_positive_rate
        
        # Calculate optimal parameters
        self.size = self._optimal_size(capacity, false_positive_rate)
        self.hash_count = self._optimal_hash_count(self.size, capacity)
        
        # Initialize bit array
        self.bit_array = [0] * self.size
        self.element_count = 0
        
        # Generate unique seeds for hash functions
        self.hash_seeds = [random.randint(0, 2**32 - 1) for _ in range(self.hash_count)]
        
        print(f"Bloom Filter initialized:")
        print(f"  Capacity: {capacity} elements")
        print(f"  Bit array size: {self.size} bits")
        print(f"  Hash functions: {self.hash_count}")
        print(f"  Expected false positive rate: {false_positive_rate:.4f}")
    
    def _optimal_size(self, n: int, p: float) -> int:
        """Calculate optimal bit array size for given capacity and false positive rate."""
        size = - (n * math.log(p)) / (math.log(2) ** 2)
        return int(math.ceil(size))
    
    def _optimal_hash_count(self, m: int, n: int) -> int:
        """Calculate optimal number of hash functions."""
        k = (m / n) * math.log(2)
        return max(1, int(math.ceil(k)))
    
    def _get_hash_positions(self, item: Any) -> List[int]:
        """
        Generate multiple hash positions using MurmurHash3 with different seeds.
        Returns list of bit positions for the given item.
        """
        positions = []
        for seed in self.hash_seeds:
            # Hash the item and map to bit array position
            hash_val = mmh3.hash(str(item), seed) 
            position = hash_val % self.size
            positions.append(abs(position))  # Ensure positive position
        return positions
    
    def add(self, item: Any) -> None:
        """
        Add an element to the Bloom Filter.
        """
        positions = self._get_hash_positions(item)
        for pos in positions:
            self.bit_array[pos] = 1
        self.element_count += 1
    
    def contains(self, item: Any) -> bool:
        """
        Check if an element is probably in the Bloom Filter.
        Returns True if the element might be present (with possibility of false positive),
        False if the element is definitely not present.
        """
        positions = self._get_hash_positions(item)
        return all(self.bit_array[pos] == 1 for pos in positions)
    
    def actual_false_positive_rate(self) -> float:
        """
        Calculate the theoretical false positive rate based on current load.
        """
        if self.element_count == 0:
            return 0.0
        
        load_factor = self.element_count / self.capacity
        return (1 - math.exp(-self.hash_count * load_factor)) ** self.hash_count
    
    def bit_array_density(self) -> float:
        """Calculate what percentage of bits are set to 1."""
        set_bits = sum(self.bit_array)
        return set_bits / self.size
    
    def reset(self) -> None:
        """Reset the Bloom Filter to empty state."""
        self.bit_array = [0] * self.size
        self.element_count = 0

class BloomFilterAnalyzer:
    """
    Comprehensive analyzer for testing and visualizing Bloom Filter performance.
    """
    
    def __init__(self):
        self.results = defaultdict(list)
    
    def generate_test_data(self, n: int, string_length: int = 10) -> List[str]:
        """Generate random strings for testing."""
        return [''.join(random.choices(string.ascii_letters + string.digits, k=string_length)) 
                for _ in range(n)]
    
    def test_false_positive_rate(self, bloom_filter: BloomFilter, 
                               inserted_items: List[str], 
                               test_items: List[str]) -> float:
        """
        Test the actual false positive rate of the Bloom Filter.
        """
        # Add inserted items to bloom filter
        for item in inserted_items:
            bloom_filter.add(item)
        
        # Test with items that were definitely not inserted
        false_positives = 0
        for test_item in test_items:
            if test_item not in inserted_items and bloom_filter.contains(test_item):
                false_positives += 1
        
        actual_fpr = false_positives / len(test_items)
        return actual_fpr
    
    def comprehensive_analysis(self, capacities: List[int] = None, 
                             false_positive_rates: List[float] = None):
        """
        Perform comprehensive analysis of Bloom Filter performance across different parameters.
        """
        if capacities is None:
            capacities = [1000, 5000, 10000, 50000]
        if false_positive_rates is None:
            false_positive_rates = [0.01, 0.05, 0.1, 0.2]
        
        print("Starting Comprehensive Bloom Filter Analysis...")
        print("=" * 60)
        
        for capacity in capacities:
            for fpr in false_positive_rates:
                # Generate test data
                inserted_items = self.generate_test_data(capacity)
                test_items = self.generate_test_data(1000)  # 1000 test items
                
                # Create and test Bloom Filter
                bf = BloomFilter(capacity, fpr)
                actual_fpr = self.test_false_positive_rate(bf, inserted_items, test_items)
                density = bf.bit_array_density()
                
                # Store results
                self.results['capacity'].append(capacity)
                self.results['target_fpr'].append(fpr)
                self.results['actual_fpr'].append(actual_fpr)
                self.results['bit_density'].append(density)
                self.results['bit_array_size'].append(bf.size)
                self.results['hash_count'].append(bf.hash_count)
                
                print(f"Capacity: {capacity:6d} | Target FPR: {fpr:5.3f} | "
                      f"Actual FPR: {actual_fpr:6.4f} | Density: {density:6.3f} | "
                      f"Size: {bf.size:7d} bits | Hashes: {bf.hash_count}")

class BloomFilterVisualizer:
    """
    Create comprehensive visualizations for Bloom Filter analysis.
    """
    
    @staticmethod
    def plot_false_positive_analysis(results: dict):
        """Plot false positive rate analysis across different parameters."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Actual vs Target FPR
        capacities = list(set(results['capacity']))
        colors = plt.cm.viridis(np.linspace(0, 1, len(capacities)))
        
        for i, capacity in enumerate(sorted(capacities)):
            mask = [c == capacity for c in results['capacity']]
            target_fpr = [results['target_fpr'][j] for j, m in enumerate(mask) if m]
            actual_fpr = [results['actual_fpr'][j] for j, m in enumerate(mask) if m]
            
            ax1.plot(target_fpr, actual_fpr, 'o-', color=colors[i], 
                    label=f'Capacity: {capacity}', markersize=6)
        
        ax1.plot([0, 0.2], [0, 0.2], 'k--', alpha=0.5, label='Ideal')
        ax1.set_xlabel('Target False Positive Rate')
        ax1.set_ylabel('Actual False Positive Rate')
        ax1.set_title('Actual vs Target False Positive Rate')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Bit array size vs capacity
        unique_capacities = sorted(set(results['capacity']))
        avg_sizes = []
        for cap in unique_capacities:
            sizes = [results['bit_array_size'][i] for i, c in enumerate(results['capacity']) if c == cap]
            avg_sizes.append(np.mean(sizes))
        
        ax2.plot(unique_capacities, avg_sizes, 's-', color='red', linewidth=2, markersize=6)
        ax2.set_xlabel('Capacity')
        ax2.set_ylabel('Bit Array Size')
        ax2.set_title('Bloom Filter Size vs Capacity')
        ax2.grid(True, alpha=0.3)
        ax2.set_xscale('log')
        ax2.set_yscale('log')
        
        # Plot 3: Hash function count analysis
        hash_counts = list(set(results['hash_count']))
        fpr_by_hash = []
        for hc in sorted(hash_counts):
            fprs = [results['actual_fpr'][i] for i, h in enumerate(results['hash_count']) if h == hc]
            fpr_by_hash.append(np.mean(fprs) if fprs else 0)
        
        ax3.bar(range(len(hash_counts)), fpr_by_hash, color='lightgreen', alpha=0.7)
        ax3.set_xlabel('Number of Hash Functions')
        ax3.set_ylabel('Average False Positive Rate')
        ax3.set_title('False Positive Rate vs Hash Function Count')
        ax3.set_xticks(range(len(hash_counts)))
        ax3.set_xticklabels(hash_counts)
        
        # Plot 4: Bit density analysis
        densities = results['bit_density']
        ax4.hist(densities, bins=20, alpha=0.7, color='purple', edgecolor='black')
        ax4.set_xlabel('Bit Array Density')
        ax4.set_ylabel('Frequency')
        ax4.set_title('Distribution of Bit Array Densities')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def visualize_bit_array(bloom_filter: BloomFilter, max_bits: int = 200):
        """Visualize a portion of the Bloom Filter's bit array."""
        bits_to_show = min(max_bits, bloom_filter.size)
        bit_segment = bloom_filter.bit_array[:bits_to_show]
        
        plt.figure(figsize=(15, 2))
        plt.imshow([bit_segment], cmap='RdYlGn', aspect='auto', interpolation='nearest')
        plt.colorbar(label='Bit Value (0/1)')
        plt.title(f'Bloom Filter Bit Array (First {bits_to_show} bits) - '
                 f'Density: {bloom_filter.bit_array_density():.3f}')
        plt.xlabel('Bit Position')
        plt.yticks([])
        
        # Annotate set bits
        set_positions = [i for i, bit in enumerate(bit_segment) if bit == 1]
        for pos in set_positions:
            plt.text(pos, 0, '1', ha='center', va='center', fontweight='bold', fontsize=8)
        
        plt.tight_layout()
        plt.show()

# Example usage and demonstration
def demonstration():
    """Comprehensive demonstration of the Bloom Filter implementation."""
    print("🌼 Bloom Filter Implementation Demo")
    print("=" * 50)
    
    # Demo 1: Basic functionality
    print("\n1. BASIC FUNCTIONALITY DEMO")
    print("-" * 30)
    
    bf = BloomFilter(capacity=100, false_positive_rate=0.05)
    
    # Add some items
    items_to_add = ["apple", "banana", "cherry", "date", "elderberry"]
    for item in items_to_add:
        bf.add(item)
        print(f"Added: {item}")
    
    # Test contains
    test_items = ["apple", "banana", "grape", "kiwi", "mango"]
    print("\nTesting membership:")
    for item in test_items:
        result = bf.contains(item)
        status = "Probably Present" if result else "Definitely Not Present"
        certainty = "✓" if item in items_to_add else "✗ (False Positive)" if result else "✓"
        print(f"  {item:12} -> {status:20} {certainty}")
    
    print(f"\nCurrent load: {bf.element_count}/{bf.capacity} elements")
    print(f"Bit array density: {bf.bit_array_density():.3f}")
    print(f"Theoretical false positive rate: {bf.actual_false_positive_rate():.3f}")
    
    # Demo 2: False positive rate testing
    print("\n\n2. FALSE POSITIVE RATE ANALYSIS")
    print("-" * 40)
    
    analyzer = BloomFilterAnalyzer()
    
    # Test with different capacities and FPRs
    test_capacities = [1000, 5000]
    test_fprs = [0.01, 0.05, 0.1]
    
    for capacity in test_capacities:
        for target_fpr in test_fprs:
            # Generate test data
            inserted = analyzer.generate_test_data(capacity)
            test_set = analyzer.generate_test_data(1000)
            
            # Create and test Bloom Filter
            bf_test = BloomFilter(capacity, target_fpr)
            actual_fpr = analyzer.test_false_positive_rate(bf_test, inserted, test_set)
            
            print(f"Capacity: {capacity:5d} | Target FPR: {target_fpr:5.3f} | "
                  f"Actual FPR: {actual_fpr:6.4f} | Density: {bf_test.bit_array_density():6.3f}")
    
    # Demo 3: Comprehensive analysis with visualization
    print("\n\n3. COMPREHENSIVE ANALYSIS & VISUALIZATION")
    print("-" * 45)
    
    # Run comprehensive analysis
    analyzer.comprehensive_analysis(capacities=[1000, 5000, 10000], 
                                  false_positive_rates=[0.01, 0.05, 0.1, 0.2])
    
    # Create visualizations
    visualizer = BloomFilterVisualizer()
    visualizer.plot_false_positive_analysis(analyzer.results)
    
    # Visualize a sample Bloom Filter's bit array
    sample_bf = BloomFilter(100, 0.1)
    sample_items = analyzer.generate_test_data(80)
    for item in sample_items:
        sample_bf.add(item)
    
    visualizer.visualize_bit_array(sample_bf)
    
    # Demo 4: Performance comparison
    print("\n\n4. MEMORY EFFICIENCY COMPARISON")
    print("-" * 35)
    
    capacities = [1000, 10000, 100000]
    fpr = 0.01
    
    for capacity in capacities:
        bf_eff = BloomFilter(capacity, fpr)
        traditional_size = capacity * 20  # Assume 20 bytes per string average
        bloom_size_bytes = bf_eff.size / 8  # bits to bytes
        
        print(f"Capacity: {capacity:6d} elements")
        print(f"  Traditional set: ~{traditional_size:8,d} bytes")
        print(f"  Bloom filter:    ~{bloom_size_bytes:8.0f} bytes")
        print(f"  Memory savings:  {traditional_size/bloom_size_bytes:7.1f}x")
        print()

if __name__ == "__main__":
    demonstration()
