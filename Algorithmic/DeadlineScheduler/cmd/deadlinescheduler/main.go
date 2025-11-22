package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"strings"

	ds "deadlinescheduler"
)

func parseJobs(path string) ([]ds.Job, error) {
	var f *os.File
	var err error
	if path == "-" || path == "" {
		f = os.Stdin
	} else {
		f, err = os.Open(path)
		if err != nil {
			return nil, err
		}
		defer f.Close()
	}

	jobs := []ds.Job{}
	scanner := bufio.NewScanner(f)
	lineNo := 0
	for scanner.Scan() {
		lineNo++
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		var deadline, duration, penalty int
		if _, err := fmt.Sscanf(line, "%d %d %d", &deadline, &duration, &penalty); err != nil {
			return nil, fmt.Errorf("line %d: expected 'deadline duration penalty': %w", lineNo, err)
		}
		jobs = append(jobs, ds.Job{ID: len(jobs) + 1, Deadline: deadline, Duration: duration, Penalty: penalty})
	}

	if err := scanner.Err(); err != nil {
		return nil, err
	}
	return jobs, nil
}

func main() {
	file := flag.String("file", "-", "Path to input file (default: stdin). Lines: deadline duration penalty")
	algo := flag.String("algo", "dp", "Scheduling algorithm: dp or greedy")
	flag.Parse()

	jobs, err := parseJobs(*file)
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to read jobs: %v\n", err)
		os.Exit(1)
	}

	var result ds.ScheduleResult
	switch strings.ToLower(*algo) {
	case "dp":
		result, err = ds.DPSchedule(jobs)
	case "greedy":
		result, err = ds.GreedySchedule(jobs)
	default:
		fmt.Fprintf(os.Stderr, "unknown algorithm: %s\n", *algo)
		os.Exit(1)
	}

	if err != nil {
		fmt.Fprintf(os.Stderr, "scheduling failed: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Total penalty: %d\n", result.TotalPenalty)
	fmt.Printf("Schedule order (by input id):\n")
	current := 0
	for _, job := range result.Order {
		fmt.Printf("  Job %d (deadline=%d, duration=%d, penalty=%d) | start=%d end=%d\n",
			job.ID, job.Deadline, job.Duration, job.Penalty, current, current+job.Duration)
		current += job.Duration
	}
}
