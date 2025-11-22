package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
)

// Input describes CLI JSON payload.
type Input struct {
	Items    []Item `json:"items"`
	Capacity []int  `json:"capacity"`
}

func main() {
	flag.Parse()
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to read stdin: %v\n", err)
		os.Exit(1)
	}

	var input Input
	if err := json.Unmarshal(data, &input); err != nil {
		fmt.Fprintf(os.Stderr, "failed to parse input JSON: %v\n", err)
		os.Exit(1)
	}

	solution, err := SolveMultiDimensionalKnapsack(input.Items, input.Capacity)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}

	output, err := json.MarshalIndent(solution, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to marshal output: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(string(output))
}
