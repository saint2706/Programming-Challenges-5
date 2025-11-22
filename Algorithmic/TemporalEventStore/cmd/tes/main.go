package main

import (
	"encoding/csv"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"strings"
	"time"

	"temporal-event-store/store"
)

func main() {
	var files string
	var format string
	var startStr string
	var endStr string
	var queryType string

	flag.StringVar(&files, "files", "", "Comma-separated list of JSON or CSV files containing events")
	flag.StringVar(&format, "format", "", "Input format: json or csv (autodetected by extension when empty)")
	flag.StringVar(&startStr, "start", "", "Query interval start time (RFC3339)")
	flag.StringVar(&endStr, "end", "", "Query interval end time (RFC3339)")
	flag.StringVar(&queryType, "query", "overlap", "Query type: overlap or contain")
	flag.Parse()

	if files == "" || startStr == "" || endStr == "" {
		flag.Usage()
		os.Exit(1)
	}

	start, err := time.Parse(time.RFC3339, startStr)
	if err != nil {
		fmt.Fprintf(os.Stderr, "invalid start time: %v\n", err)
		os.Exit(1)
	}
	end, err := time.Parse(time.RFC3339, endStr)
	if err != nil {
		fmt.Fprintf(os.Stderr, "invalid end time: %v\n", err)
		os.Exit(1)
	}

	tree := store.NewIntervalTree()
	for _, f := range strings.Split(files, ",") {
		file := strings.TrimSpace(f)
		if file == "" {
			continue
		}
		err := ingestFile(tree, file, format)
		if err != nil {
			fmt.Fprintf(os.Stderr, "failed to ingest %s: %v\n", file, err)
			os.Exit(1)
		}
	}

	switch strings.ToLower(queryType) {
	case "overlap":
		results := tree.QueryOverlap(start, end)
		emitJSON(results)
	case "contain", "contains":
		results := tree.QueryContaining(start, end)
		emitJSON(results)
	default:
		fmt.Fprintf(os.Stderr, "unknown query type %s\n", queryType)
		os.Exit(1)
	}
}

func ingestFile(tree *store.IntervalTree, path, formatOverride string) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()

	format := strings.ToLower(formatOverride)
	if format == "" {
		if strings.HasSuffix(strings.ToLower(path), ".json") {
			format = "json"
		} else if strings.HasSuffix(strings.ToLower(path), ".csv") {
			format = "csv"
		}
	}

	switch format {
	case "json":
		decoder := json.NewDecoder(f)
		var events []store.Event
		if err := decoder.Decode(&events); err != nil {
			return err
		}
		for _, ev := range events {
			ev.Normalize()
			tree.Insert(ev)
		}
	case "csv":
		reader := csv.NewReader(f)
		headers, err := reader.Read()
		if err != nil {
			return err
		}
		headerIndex := map[string]int{}
		for i, h := range headers {
			headerIndex[strings.ToLower(strings.TrimSpace(h))] = i
		}
		required := []string{"id", "start", "end"}
		for _, key := range required {
			if _, ok := headerIndex[key]; !ok {
				return fmt.Errorf("missing required column %s", key)
			}
		}
		for {
			record, err := reader.Read()
			if err == io.EOF {
				break
			}
			if err != nil {
				return err
			}
			ev := store.Event{ID: record[headerIndex["id"]], Data: map[string]string{}}
			ev.Start, err = time.Parse(time.RFC3339, record[headerIndex["start"]])
			if err != nil {
				return fmt.Errorf("invalid start time: %w", err)
			}
			ev.End, err = time.Parse(time.RFC3339, record[headerIndex["end"]])
			if err != nil {
				return fmt.Errorf("invalid end time: %w", err)
			}
			for i, val := range record {
				key := strings.ToLower(headers[i])
				if key == "id" || key == "start" || key == "end" {
					continue
				}
				ev.Data[key] = val
			}
			ev.Normalize()
			tree.Insert(ev)
		}
	default:
		return fmt.Errorf("unsupported format: %s", format)
	}

	return nil
}

func emitJSON(events []store.Event) {
	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	_ = encoder.Encode(events)
}
