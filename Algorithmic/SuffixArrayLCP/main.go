package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

type Command struct {
	Type  string `json:"type"` // "sa", "lcp", "distinct"
	Value string `json:"value,omitempty"`
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

	results := []Output{}

	for _, cmd := range commands {
		var out Output
		switch cmd.Type {
		case "sa":
			sa := SuffixArray(cmd.Value)
			out.Result = sa
		case "lcp":
			sa := SuffixArray(cmd.Value)
			lcp := LCPArray(cmd.Value, sa)
			out.Result = lcp
		case "distinct":
			count := NumberOfDistinctSubstrings(cmd.Value)
			out.Result = count
		default:
			out.Error = "unknown command"
		}
		results = append(results, out)
	}

	outBytes, _ := json.MarshalIndent(results, "", "  ")
	fmt.Println(string(outBytes))
}
