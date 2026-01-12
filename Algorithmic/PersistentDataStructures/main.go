package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

type Command struct {
	Type  string `json:"type"`  // "new", "set", "get", "append"
	Value int    `json:"value"` // for set/append
	Index int    `json:"index"` // for set/get
	Ver   int    `json:"ver"`   // version index to operate on (0-based)
}

type Output struct {
	Version int    `json:"version,omitempty"` // ID of the new version created
	Value   int    `json:"value,omitempty"`   // Result of get
	Error   string `json:"error,omitempty"`
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
			// Allow running without input for verification/testing manually if needed,
			// but strictly we expect JSON commands.
			fmt.Fprintf(os.Stderr, "failed to parse input JSON: %v\n", err)
			os.Exit(1)
		}
	}

	// Store versions. index 0 is initial empty? Or user creates it.
	// Let's assume an implicit empty version 0 exists or user calls "new".
	// To be flexible, let's just start with an empty list of versions.
	// But usually challenge solvers expect a specific structure.
	// I'll assume the first command creates a structure or we start with one empty vector.

	versions := []*PersistentArray{NewPersistentArray()} // Version 0 is empty

	results := []Output{}

	for _, cmd := range commands {
		var out Output

		if cmd.Ver < 0 || cmd.Ver >= len(versions) {
			out.Error = fmt.Sprintf("version %d does not exist", cmd.Ver)
			results = append(results, out)
			continue
		}

		current := versions[cmd.Ver]

		switch cmd.Type {
		case "get":
			val, err := current.Get(cmd.Index)
			if err != nil {
				out.Error = err.Error()
			} else {
				out.Value = val
			}
		case "set":
			newPa, err := current.Set(cmd.Index, cmd.Value)
			if err != nil {
				out.Error = err.Error()
			} else {
				versions = append(versions, newPa)
				out.Version = len(versions) - 1
			}
		case "append":
			newPa := current.Push(cmd.Value)
			versions = append(versions, newPa)
			out.Version = len(versions) - 1
		default:
			out.Error = "unknown command"
		}
		results = append(results, out)
	}

	outBytes, _ := json.MarshalIndent(results, "", "  ")
	fmt.Println(string(outBytes))
}
