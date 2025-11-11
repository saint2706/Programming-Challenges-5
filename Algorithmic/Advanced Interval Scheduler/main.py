import bisect
from typing import List, Tuple

class AdvancedIntervalScheduler:
    """
    Efficient solution for Weighted Interval Scheduling using Dynamic Programming.
    Finds the maximum weight subset of non-overlapping intervals.
    """
    
    def __init__(self, intervals: List[Tuple[int, int, int]]):
        """
        Initialize with intervals as (start, end, weight) tuples.
        
        Args:
            intervals: List of (start_time, end_time, weight) tuples
        """
        self.intervals = intervals
        self.n = len(intervals)
        
    def find_optimal_schedule(self) -> Tuple[int, List[Tuple[int, int, int]]]:
        """
        Find the optimal schedule with maximum total weight.
        
        Returns:
            Tuple of (max_weight, selected_intervals)
        """
        if not self.intervals:
            return 0, []
            
        # 1. Sort intervals by end time
        sorted_intervals = sorted(self.intervals, key=lambda x: x[1])
        
        # 2. Extract end times and weights for easier access
        end_times = [interval[1] for interval in sorted_intervals]
        weights = [interval[2] for interval in sorted_intervals]
        
        # 3. Precompute p(j) - the rightmost interval that doesn't overlap with j
        p = self._compute_predecessors(sorted_intervals, end_times)
        
        # 4. Dynamic Programming table
        dp = [0] * (self.n + 1)
        
        # 5. Fill DP table
        for j in range(1, self.n + 1):
            # Option 1: Don't take interval j-1
            skip_weight = dp[j - 1]
            
            # Option 2: Take interval j-1
            take_weight = weights[j - 1]
            if p[j - 1] != -1:
                take_weight += dp[p[j - 1] + 1]  # +1 because dp is 1-indexed
            
            dp[j] = max(skip_weight, take_weight)
        
        # 6. Backtrack to find selected intervals
        selected_intervals = self._backtrack_schedule(dp, p, sorted_intervals)
        
        return dp[self.n], selected_intervals
    
    def _compute_predecessors(self, intervals: List[Tuple[int, int, int]], 
                            end_times: List[int]) -> List[int]:
        """
        Compute p(j) - for each interval j, find the rightmost interval i < j 
        that doesn't overlap with j (i.e., end_i <= start_j).
        Returns -1 if no such interval exists.
        """
        p = [-1] * self.n
        
        for j in range(self.n):
            start_j = intervals[j][0]
            
            # Use binary search to find the rightmost interval ending <= start_j
            # bisect_right finds the position where start_j would be inserted
            # to maintain sorted order of end_times
            i = bisect.bisect_right(end_times, start_j) - 1
            
            if i >= 0 and end_times[i] <= start_j:
                p[j] = i
            else:
                p[j] = -1
                
        return p
    
    def _backtrack_schedule(self, dp: List[int], p: List[int], 
                          intervals: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """
        Backtrack through DP table to find the actual intervals in optimal solution.
        """
        selected = []
        j = self.n - 1
        
        while j >= 0:
            current_weight = intervals[j][2]
            prev_dp = dp[p[j] + 1] if p[j] != -1 else 0
            
            if j == 0:
                if current_weight + prev_dp >= dp[j + 1]:
                    selected.append(intervals[j])
                break
            
            # If we take this interval
            if current_weight + prev_dp >= dp[j]:
                selected.append(intervals[j])
                j = p[j]  # Jump to the next compatible interval
            else:
                j -= 1  # Skip this interval
                
        return selected[::-1]  # Return in chronological order

    def get_schedule_summary(self, selected_intervals: List[Tuple[int, int, int]]) -> dict:
        """
        Generate a summary of the selected schedule.
        """
        total_weight = sum(interval[2] for interval in selected_intervals)
        total_intervals = len(selected_intervals)
        timeline = [(f"Interval {i+1}", f"({start}-{end})", f"weight: {weight}") 
                   for i, (start, end, weight) in enumerate(selected_intervals)]
        
        return {
            'total_weight': total_weight,
            'total_intervals': total_intervals,
            'schedule': timeline
        }
