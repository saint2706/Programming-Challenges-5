package main

import (
	"bufio"
	"errors"
	"flag"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"

	"parallelsort"
)

func main() {
	algorithm := flag.String("algorithm", "merge", "sorting algorithm to use: merge or quick")
	threshold := flag.Int("threshold", 2048, "minimum slice length before spawning goroutines")
	inFile := flag.String("input", "", "path to input file containing one number per line")
	flag.Parse()

	if *inFile == "" {
		log.Fatal("input file is required")
	}

	numbers, err := readNumbers(*inFile)
	if err != nil {
		log.Fatalf("failed to read numbers: %v", err)
	}

	switch strings.ToLower(*algorithm) {
	case "merge":
		parallelsort.ParallelMergeSort(numbers, *threshold)
	case "quick", "quicksort":
		parallelsort.ParallelQuickSort(numbers, *threshold)
	default:
		log.Fatalf("unknown algorithm %q (use merge or quick)", *algorithm)
	}

	if !parallelsort.IsSorted(numbers) {
		log.Fatal("sorted output failed verification")
	}

	writer := bufio.NewWriter(os.Stdout)
	for _, n := range numbers {
		fmt.Fprintln(writer, n)
	}
	_ = writer.Flush()
}

func readNumbers(path string) ([]int, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var nums []int
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		n, convErr := strconv.Atoi(line)
		if convErr != nil {
			return nil, fmt.Errorf("line %d: %w", len(nums)+1, convErr)
		}
		nums = append(nums, n)
	}

	if err := scanner.Err(); err != nil {
		return nil, err
	}

	if len(nums) == 0 {
		return nil, errors.New("no numbers found in file")
	}

	return nums, nil
}
