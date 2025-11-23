package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

type Command struct {
	Type    string  `json:"type"` // "init", "insert", "query"
	Epsilon float64 `json:"epsilon,omitempty"`
	Value   float64 `json:"value,omitempty"`
	Phi     float64 `json:"phi,omitempty"`
}

type Output struct {
	Result interface{} `json:"result,omitempty"`
	Error  string      `json:"error,omitempty"`
}

func main() {
	inputData, err := io.ReadAll(os.Stdin)
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to read stdin: %v\n", err)
		os.Exit(1)
	}

	var commands []Command
	if len(inputData) > 0 {
		if err := json.Unmarshal(inputData, &commands); err != nil {
			fmt.Fprintf(os.Stderr, "failed to parse input JSON: %v\n", err)
			os.Exit(1)
		}
	}

	var qe *QuantileEstimator
	results := []Output{}

	for _, cmd := range commands {
		var out Output
		switch cmd.Type {
		case "init":
			qe = NewQuantileEstimator(cmd.Epsilon)
			out.Result = "initialized"
		case "insert":
			if qe == nil {
				out.Error = "not initialized"
			} else {
				qe.Insert(cmd.Value)
				out.Result = "inserted"
			}
		case "query":
			if qe == nil {
				out.Error = "not initialized"
			} else {
				val, err := qe.Query(cmd.Phi)
				if err != nil {
					out.Error = err.Error()
				} else {
					out.Result = val
				}
			}
		default:
			out.Error = "unknown command"
		}
		results = append(results, out)
	}

	outBytes, _ := json.MarshalIndent(results, "", "  ")
	fmt.Println(string(outBytes))
}
