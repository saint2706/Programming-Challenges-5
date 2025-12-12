from Algorithmic.AdvancedIntervalScheduler import AdvancedIntervalScheduler, Interval


def test_finds_optimal_weight_and_schedule():
    intervals = [
        (1, 3, 5),
        (2, 5, 6),
        (4, 6, 5),
        (6, 7, 8),
    ]

    scheduler = AdvancedIntervalScheduler(intervals)
    max_weight, schedule = scheduler.find_optimal_schedule()

    assert max_weight == 18
    assert schedule == [
        Interval(start=1, end=3, weight=5),
        Interval(start=4, end=6, weight=5),
        Interval(start=6, end=7, weight=8),
    ]


def test_predecessors_and_overlapping_intervals():
    intervals = [
        (0, 5, 10),
        (1, 6, 9),
        (5, 7, 5),
    ]

    scheduler = AdvancedIntervalScheduler(intervals)
    sorted_intervals = sorted(scheduler.intervals)
    end_times = [interval.end for interval in sorted_intervals]
    predecessors = scheduler._compute_predecessors(sorted_intervals, end_times)

    assert predecessors == [-1, -1, 0]

    max_weight, schedule = scheduler.find_optimal_schedule()
    assert max_weight == 15
    assert schedule == [
        Interval(start=0, end=5, weight=10),
        Interval(start=5, end=7, weight=5),
    ]


def test_zero_length_and_tied_intervals():
    intervals = [
        (1, 1, 4),  # zero-length, should be compatible with all that start at 1
        (1, 3, 2),
        (3, 3, 6),  # zero-length at end of previous interval
        (2, 4, 6),
        (4, 6, 6),  # ties on weight and non-overlapping boundary with previous
    ]

    scheduler = AdvancedIntervalScheduler(intervals)
    max_weight, schedule = scheduler.find_optimal_schedule()

    assert max_weight == 18
    assert schedule == [
        Interval(start=1, end=1, weight=4),
        Interval(start=1, end=3, weight=2),
        Interval(start=3, end=3, weight=6),
        Interval(start=4, end=6, weight=6),
    ]
