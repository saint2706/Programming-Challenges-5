package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

type Edge struct {
	U int `json:"u"`
	V int `json:"v"`
}

type GraphInput struct {
	Nodes int    `json:"nodes"`
	Edges []Edge `json:"edges"`
}

type Command struct {
	Type   string     `json:"type"` // "check"
	Graph1 GraphInput `json:"graph1"`
	Graph2 GraphInput `json:"graph2"`
}

type Output struct {
	Result bool   `json:"result"`
	Error  string `json:"error,omitempty"`
}

func parseGraph(in GraphInput) *Graph {
	g := NewGraph(in.Nodes)
	for _, e := range in.Edges {
		g.AddEdge(e.U, e.V)
	}
	return g
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
		case "check":
			g1 := parseGraph(cmd.Graph1)
			g2 := parseGraph(cmd.Graph2)
			out.Result = IsIsomorphic(g1, g2)
		default:
			out.Error = "unknown command"
		}
		results = append(results, out)
	}

	outBytes, _ := json.MarshalIndent(results, "", "  ")
	fmt.Println(string(outBytes))
}
