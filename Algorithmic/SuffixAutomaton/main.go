package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

type Command struct {
	Type    string `json:"type"` // "build", "check", "distinct", "lcs"
	Value   string `json:"value,omitempty"`
	Pattern string `json:"pattern,omitempty"`
	Other   string `json:"other,omitempty"`
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

	var sa *SuffixAutomaton
	results := []Output{}

	for _, cmd := range commands {
		var out Output
		switch cmd.Type {
		case "build":
			sa = NewSuffixAutomaton()
			sa.Build(cmd.Value)
			out.Result = "built"
		case "check":
			if sa == nil {
				out.Error = "automaton not built"
			} else {
				out.Result = sa.CheckSubstring(cmd.Pattern)
			}
		case "distinct":
			if sa == nil {
				out.Error = "automaton not built"
			} else {
				out.Result = sa.NumberOfDistinctSubstrings()
			}
		case "lcs":
			if sa == nil {
				out.Error = "automaton not built"
			} else {
				out.Result = sa.LongestCommonSubstring(cmd.Other)
			}
		default:
			out.Error = "unknown command"
		}
		results = append(results, out)
	}

	outBytes, _ := json.MarshalIndent(results, "", "  ")
	fmt.Println(string(outBytes))
}
