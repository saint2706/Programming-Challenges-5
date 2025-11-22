package main

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func TestContainsSequence(t *testing.T) {
	seq := Sequence{Itemset{"a", "b"}, Itemset{"c"}}
	pattern := Sequence{Itemset{"a"}, Itemset{"c"}}
	if !ContainsSequence(seq, pattern) {
		t.Fatalf("expected sequence to contain pattern")
	}
}

func TestMinePrefixSpan(t *testing.T) {
	db := []Sequence{
		{Itemset{"a"}, Itemset{"b"}, Itemset{"c"}},
		{Itemset{"a"}, Itemset{"c"}},
		{Itemset{"a"}, Itemset{"b"}, Itemset{"a", "c"}},
	}

	patterns, err := MinePrefixSpan(db, 2)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	expected := map[string]int{
		"<a>":       3,
		"<b>":       2,
		"<c>":       3,
		"<a><b>":    2,
		"<a><c>":    3,
		"<b><c>":    2,
		"<a><b><c>": 2,
	}

	got := make(map[string]int)
	for _, p := range patterns {
		key := FormatPattern(p.Sequence)
		got[key] = p.Support
	}

	for k, v := range expected {
		if got[k] != v {
			t.Fatalf("missing expected pattern %s with support %d (got %d)", k, v, got[k])
		}
	}
}

func TestCLIIntegration(t *testing.T) {
	db := [][][]string{
		{{"milk", "bread"}, {"eggs"}},
		{{"bread"}, {"eggs"}},
		{{"milk"}, {"bread"}, {"cereal"}},
	}
	tmp := t.TempDir()
	input := filepath.Join(tmp, "sequences.json")
	data, err := json.Marshal(db)
	if err != nil {
		t.Fatalf("failed to marshal input: %v", err)
	}
	if err := os.WriteFile(input, data, 0644); err != nil {
		t.Fatalf("failed to write input: %v", err)
	}

	cmd := exec.Command("go", "run", "./", "-input", input, "-minsup", "0.66")
	cmd.Dir = "./"
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("cli failed: %v output: %s", err, string(output))
	}

	lines := filterNonEmpty(splitLines(string(output)))
	if len(lines) == 0 {
		t.Fatalf("expected output from CLI")
	}
}

func splitLines(s string) []string {
	normalized := strings.ReplaceAll(s, "\r\n", "\n")
	return strings.Split(normalized, "\n")
}

func filterNonEmpty(lines []string) []string {
	var res []string
	for _, l := range lines {
		if l != "" {
			res = append(res, l)
		}
	}
	return res
}
