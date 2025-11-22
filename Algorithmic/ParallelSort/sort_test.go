package parallelsort

import (
	"math/rand"
	"sort"
	"sync"
	"testing"
	"time"
)

func TestParallelMergeSortMatchesStd(t *testing.T) {
	for _, size := range []int{0, 1, 10, 1024} {
		nums := randomSlice(size)
		expected := append([]int(nil), nums...)
		sort.Ints(expected)

		ParallelMergeSort(nums, 64)
		if !slicesEqual(nums, expected) {
			t.Fatalf("merge sort mismatch for size %d", size)
		}
	}
}

func TestParallelQuickSortMatchesStd(t *testing.T) {
	for _, size := range []int{0, 1, 10, 2048} {
		nums := randomSlice(size)
		expected := append([]int(nil), nums...)
		sort.Ints(expected)

		ParallelQuickSort(nums, 64)
		if !slicesEqual(nums, expected) {
			t.Fatalf("quick sort mismatch for size %d", size)
		}
	}
}

func TestAlreadySortedInput(t *testing.T) {
	sorted := make([]int, 4096)
	for i := range sorted {
		sorted[i] = i
	}
	mergeInput := append([]int(nil), sorted...)
	quickInput := append([]int(nil), sorted...)

	ParallelMergeSort(mergeInput, 32)
	ParallelQuickSort(quickInput, 32)

	if !slicesEqual(sorted, mergeInput) {
		t.Fatalf("merge sort altered sorted input")
	}
	if !slicesEqual(sorted, quickInput) {
		t.Fatalf("quick sort altered sorted input")
	}
}

func TestConcurrentInvocations(t *testing.T) {
	// Run both algorithms concurrently to exercise synchronization paths for race detection.
	data := randomSlice(4096)
	copyA := append([]int(nil), data...)
	copyB := append([]int(nil), data...)

	var wg sync.WaitGroup
	wg.Add(2)
	go func() {
		defer wg.Done()
		ParallelMergeSort(copyA, 64)
	}()
	go func() {
		defer wg.Done()
		ParallelQuickSort(copyB, 64)
	}()
	wg.Wait()

	if !IsSorted(copyA) {
		t.Fatal("merge sort output not sorted in concurrent run")
	}
	if !IsSorted(copyB) {
		t.Fatal("quick sort output not sorted in concurrent run")
	}
}

func slicesEqual(a, b []int) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

func randomSlice(n int) []int {
	rng := rand.New(rand.NewSource(time.Now().UnixNano()))
	out := make([]int, n)
	for i := range out {
		out[i] = rng.Intn(1000000) - 500000
	}
	return out
}

func BenchmarkParallelMergeSort(b *testing.B) {
	benchmarkSorter(b, ParallelMergeSort, 64)
}

func BenchmarkParallelQuickSort(b *testing.B) {
	benchmarkSorter(b, ParallelQuickSort, 64)
}

func benchmarkSorter(b *testing.B, sorter func([]int, int), threshold int) {
	rng := rand.New(rand.NewSource(99))
	for i := 0; i < b.N; i++ {
		data := make([]int, 1<<12)
		for i := range data {
			data[i] = rng.Intn(1 << 24)
		}
		b.StartTimer()
		sorter(data, threshold)
		b.StopTimer()
		if !IsSorted(data) {
			b.Fatalf("output not sorted")
		}
	}
}
