package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

type Command struct {
	Type  string `json:"type"` // "new", "insert", "delete", "concat", "split", "index", "print"
	Value string `json:"value,omitempty"`
	Index int    `json:"index,omitempty"`
	Start int    `json:"start,omitempty"`
	End   int    `json:"end,omitempty"`
}

type Output struct {
	Result string `json:"result,omitempty"`
	Error  string `json:"error,omitempty"`
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

	var currentRope *Rope = NewRope("")
	results := []Output{}

	for _, cmd := range commands {
		var out Output
		switch cmd.Type {
		case "new":
			currentRope = NewRope(cmd.Value)
			out.Result = "created"
		case "insert":
			currentRope = currentRope.Insert(cmd.Index, cmd.Value)
			out.Result = "inserted"
		case "delete":
			currentRope = currentRope.Delete(cmd.Start, cmd.End)
			out.Result = "deleted"
		case "print":
			out.Result = currentRope.String()
		case "index":
			b, err := currentRope.Index(cmd.Index)
			if err != nil {
				out.Error = err.Error()
			} else {
				out.Result = string(b)
			}
		default:
			out.Error = "unknown command"
		}
		results = append(results, out)
	}

	outBytes, _ := json.MarshalIndent(results, "", "  ")
	fmt.Println(string(outBytes))
}
