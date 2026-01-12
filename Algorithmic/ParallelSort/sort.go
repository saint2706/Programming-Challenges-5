package parallelsort

import (
	"sort"
	"sync"
)

// ParallelMergeSort performs an in-place merge sort using goroutines when the input size
// exceeds the given threshold. A non-positive threshold disables parallelization.
func ParallelMergeSort(nums []int, threshold int) {
	if len(nums) < 2 {
		return
	}
	if threshold <= 0 {
		threshold = len(nums) + 1 // effectively disable goroutines
	}

	sorted := mergeSortRecursive(nums, threshold)
	copy(nums, sorted)
}

func mergeSortRecursive(nums []int, threshold int) []int {
	if len(nums) <= 1 {
		return append([]int(nil), nums...)
	}

	mid := len(nums) / 2
	var left, right []int

	if mid >= threshold {
		result := make(chan []int, 1)
		go func() {
			result <- mergeSortRecursive(nums[:mid], threshold)
		}()
		right = mergeSortRecursive(nums[mid:], threshold)
		left = <-result
	} else {
		left = mergeSortRecursive(nums[:mid], threshold)
		right = mergeSortRecursive(nums[mid:], threshold)
	}

	return mergeSlices(left, right)
}

func mergeSlices(left, right []int) []int {
	merged := make([]int, 0, len(left)+len(right))
	i, j := 0, 0
	for i < len(left) && j < len(right) {
		if left[i] <= right[j] {
			merged = append(merged, left[i])
			i++
		} else {
			merged = append(merged, right[j])
			j++
		}
	}
	merged = append(merged, left[i:]...)
	merged = append(merged, right[j:]...)
	return merged
}

// ParallelQuickSort performs an in-place quicksort using goroutines when the input size
// exceeds the given threshold. A non-positive threshold disables parallelization.
func ParallelQuickSort(nums []int, threshold int) {
	if len(nums) < 2 {
		return
	}
	if threshold <= 0 {
		threshold = len(nums) + 1
	}
	quickSort(nums, threshold)
}

func quickSort(nums []int, threshold int) {
	if len(nums) < 2 {
		return
	}

	pivotIdx := len(nums) / 2
	pivot := nums[pivotIdx]
	i, j := 0, len(nums)-1
	for i <= j {
		for nums[i] < pivot {
			i++
		}
		for nums[j] > pivot {
			j--
		}
		if i <= j {
			nums[i], nums[j] = nums[j], nums[i]
			i++
			j--
		}
	}

	var wg sync.WaitGroup
	if j+1 >= threshold {
		wg.Add(1)
		left := nums[:j+1]
		go func() {
			quickSort(left, threshold)
			wg.Done()
		}()
	} else {
		quickSort(nums[:j+1], threshold)
	}

	if len(nums)-i >= threshold {
		wg.Add(1)
		right := nums[i:]
		go func() {
			quickSort(right, threshold)
			wg.Done()
		}()
	} else {
		quickSort(nums[i:], threshold)
	}

	wg.Wait()
}

// IsSorted reports whether the slice is sorted in non-decreasing order.
// This helper is shared by tests and the CLI.
func IsSorted(nums []int) bool {
	return sort.SliceIsSorted(nums, func(i, j int) bool {
		return nums[i] < nums[j]
	})
}
