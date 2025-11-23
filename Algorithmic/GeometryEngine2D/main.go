package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

type Command struct {
	Type    string  `json:"type"` // "hull", "inside", "area"
	Points  []Point `json:"points,omitempty"`
	Polygon []Point `json:"polygon,omitempty"`
	Point   Point   `json:"point,omitempty"`
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
		case "hull":
			hull := ConvexHull(cmd.Points)
			out.Result = hull
		case "inside":
			res := IsPointInPolygon(cmd.Point, cmd.Polygon)
			out.Result = res
		case "area":
			res := Area(cmd.Polygon)
			out.Result = res
		default:
			out.Error = "unknown command"
		}
		results = append(results, out)
	}

	outBytes, _ := json.MarshalIndent(results, "", "  ")
	fmt.Println(string(outBytes))
}
