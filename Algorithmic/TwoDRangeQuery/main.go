package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

type Command struct {
	Type string `json:"type"` // "init", "update", "query"
	Rows int    `json:"rows,omitempty"`
	Cols int    `json:"cols,omitempty"`
	R    int    `json:"r,omitempty"`
	C    int    `json:"c,omitempty"`
	Val  int    `json:"val,omitempty"`
	R1   int    `json:"r1,omitempty"`
	C1   int    `json:"c1,omitempty"`
	R2   int    `json:"r2,omitempty"`
	C2   int    `json:"c2,omitempty"`
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

	var ft *FenwickTree2D
	results := []Output{}

	for _, cmd := range commands {
		var out Output
		switch cmd.Type {
		case "init":
			ft = NewFenwickTree2D(cmd.Rows, cmd.Cols)
			out.Result = "initialized"
		case "update":
			if ft == nil {
				out.Error = "not initialized"
			} else {
				err := ft.Update(cmd.R, cmd.C, cmd.Val)
				if err != nil {
					out.Error = err.Error()
				} else {
					out.Result = "updated"
				}
			}
		case "query":
			if ft == nil {
				out.Error = "not initialized"
			} else {
				val, err := ft.Query(cmd.R1, cmd.C1, cmd.R2, cmd.C2)
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
