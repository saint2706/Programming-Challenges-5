"""Demonstration script for the Advanced Interval Scheduler."""

import random
import time
from typing import List, Tuple

from main import AdvancedIntervalScheduler


def test_advanced_scheduler() -> None:
    """Comprehensive test cases for the Advanced Interval Scheduler."""
    print("🧪 RUNNING BASIC TESTS")
    print("=" * 40)

    # Test Case 1: Basic example
    intervals1 = [
        (1, 3, 5),  # Interval 1: start=1, end=3, weight=5
        (2, 5, 6),  # Interval 2: start=2, end=5, weight=6
        (4, 6, 5),  # Interval 3: start=4, end=6, weight=5
        (6, 7, 8),  # Interval 4: start=6, end=7, weight=8
    ]

    scheduler1 = AdvancedIntervalScheduler(intervals1)
    max_weight1, schedule1 = scheduler1.find_optimal_schedule()

    print("Test Case 1 (Basic):")
    print(f"  Maximum Weight: {max_weight1}")
    print("  Selected Intervals:")
    for interval in schedule1:
        print(f"    {interval}")
    print()

    # Test Case 2: All intervals overlap
    intervals2 = [
        (1, 4, 10),
        (2, 5, 8),
        (3, 6, 12),
        (4, 7, 9),
    ]

    scheduler2 = AdvancedIntervalScheduler(intervals2)
    max_weight2, schedule2 = scheduler2.find_optimal_schedule()

    print("Test Case 2 (All Overlapping):")
    print(f"  Maximum Weight: {max_weight2}")
    print("  Selected Intervals:")
    for interval in schedule2:
        print(f"    {interval}")
    print()

    # Test Case 3: No overlaps
    intervals3 = [
        (1, 2, 3),
        (3, 4, 5),
        (5, 6, 2),
        (7, 8, 6),
    ]

    scheduler3 = AdvancedIntervalScheduler(intervals3)
    max_weight3, schedule3 = scheduler3.find_optimal_schedule()

    print("Test Case 3 (No Overlaps):")
    print(f"  Maximum Weight: {max_weight3}")
    print("  Selected Intervals:")
    for interval in schedule3:
        print(f"    {interval}")


# Performance test with larger input
def performance_test() -> None:
    """Test with larger dataset to demonstrate efficiency."""
    print("\n🚀 RUNNING PERFORMANCE TEST")
    print("=" * 40)

    # Generate 1000 random intervals
    random_intervals: List[Tuple[int, int, int]] = []
    for _ in range(1000):
        start = random.randint(1, 10000)
        duration = random.randint(1, 100)
        weight = random.randint(1, 100)
        random_intervals.append((start, start + duration, weight))

    scheduler = AdvancedIntervalScheduler(random_intervals)

    start_time = time.time()
    max_weight, schedule = scheduler.find_optimal_schedule()
    end_time = time.time()

    print("Performance Test (1000 intervals):")
    print(f"  Maximum Weight: {max_weight}")
    print(f"  Number of Selected Intervals: {len(schedule)}")
    print(f"  Execution Time: {end_time - start_time:.4f} seconds")


if __name__ == "__main__":
    test_advanced_scheduler()
    performance_test()
