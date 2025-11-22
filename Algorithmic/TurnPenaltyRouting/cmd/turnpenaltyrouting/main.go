package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"os"
	"strconv"
	"strings"

	routing "github.com/example/turnpenaltyrouting"
)

func main() {
	edgesPath := flag.String("edges", "", "CSV file containing edges: id,from,to,cost or from,to,cost")
	turnsPath := flag.String("turns", "", "Optional CSV file with turn penalties: incoming_id,outgoing_id,penalty|forbid")
	start := flag.String("start", "", "Start node")
	goal := flag.String("goal", "", "Goal node")
	flag.Parse()

	if *edgesPath == "" || *start == "" || *goal == "" {
		fmt.Println("edges, start, and goal flags are required")
		os.Exit(1)
	}

	edges, err := loadEdges(*edgesPath)
	if err != nil {
		fmt.Printf("failed to load edges: %v\n", err)
		os.Exit(1)
	}

	graph, err := routing.NewGraph(edges)
	if err != nil {
		fmt.Printf("invalid graph: %v\n", err)
		os.Exit(1)
	}

	penalties := routing.NewTurnPenalties()
	if *turnsPath != "" {
		if err := loadTurnPenalties(*turnsPath, penalties); err != nil {
			fmt.Printf("failed to load turn penalties: %v\n", err)
			os.Exit(1)
		}
	}

	result, err := routing.ShortestPath(graph, penalties, *start, *goal, nil)
	if err != nil {
		fmt.Printf("search failed: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Cost: %.3f\n", result.Cost)
	fmt.Printf("Steps expanded: %d\n", result.Steps)
	fmt.Printf("Path edges:\n")
	for _, e := range result.Path {
		fmt.Printf("  %s: %s -> %s (%.3f)\n", e.ID, e.From, e.To, e.Cost)
	}
}

func loadEdges(path string) ([]routing.Edge, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	reader := csv.NewReader(f)
	rows, err := reader.ReadAll()
	if err != nil {
		return nil, err
	}
	var edges []routing.Edge
	autoID := 0
	for i, row := range rows {
		if len(row) == 0 {
			continue
		}
		if len(row) != 3 && len(row) != 4 {
			return nil, fmt.Errorf("row %d must have 3 or 4 columns", i+1)
		}
		var id, from, to, costStr string
		if len(row) == 4 {
			id, from, to, costStr = strings.TrimSpace(row[0]), strings.TrimSpace(row[1]), strings.TrimSpace(row[2]), strings.TrimSpace(row[3])
		} else {
			id = fmt.Sprintf("e%d", autoID)
			autoID++
			from, to, costStr = strings.TrimSpace(row[0]), strings.TrimSpace(row[1]), strings.TrimSpace(row[2])
		}
		cost, err := strconv.ParseFloat(costStr, 64)
		if err != nil {
			return nil, fmt.Errorf("row %d cost: %w", i+1, err)
		}
		edges = append(edges, routing.Edge{ID: id, From: from, To: to, Cost: cost})
	}
	return edges, nil
}

func loadTurnPenalties(path string, penalties *routing.TurnPenalties) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()

	reader := csv.NewReader(f)
	rows, err := reader.ReadAll()
	if err != nil {
		return err
	}

	for i, row := range rows {
		if len(row) == 0 {
			continue
		}
		if len(row) != 3 {
			return fmt.Errorf("row %d must have 3 columns", i+1)
		}
		incoming := strings.TrimSpace(row[0])
		outgoing := strings.TrimSpace(row[1])
		penaltyStr := strings.TrimSpace(row[2])
		if strings.EqualFold(penaltyStr, "forbid") {
			penalties.ForbidTurn(incoming, outgoing)
			continue
		}
		val, err := strconv.ParseFloat(penaltyStr, 64)
		if err != nil {
			return fmt.Errorf("row %d penalty: %w", i+1, err)
		}
		penalties.SetPenalty(incoming, outgoing, val)
	}
	return nil
}
