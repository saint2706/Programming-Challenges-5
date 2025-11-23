package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

type Command struct {
	Type  string `json:"type"` // "insert", "search"
	Key   int64  `json:"key"`
	Value int64  `json:"value,omitempty"`
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

	// Create a temp file for the BTree
	tmpFile, err := os.CreateTemp("", "btree.db")
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to create temp file: %v\n", err)
		os.Exit(1)
	}
	defer os.Remove(tmpFile.Name())
	tmpFile.Close()

	bt, err := NewBTree(tmpFile.Name())
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to open btree: %v\n", err)
		os.Exit(1)
	}
	defer bt.Close()

	results := []Output{}

	for _, cmd := range commands {
		var out Output
		switch cmd.Type {
		case "insert":
			err := bt.Insert(cmd.Key, cmd.Value)
			if err != nil {
				out.Error = err.Error()
			} else {
				out.Result = "inserted"
			}
		case "search":
			val, found := bt.Search(cmd.Key)
			if found {
				out.Result = val
			} else {
				out.Result = nil
			}
		default:
			out.Error = "unknown command"
		}
		results = append(results, out)
	}

	outBytes, _ := json.MarshalIndent(results, "", "  ")
	fmt.Println(string(outBytes))
}
