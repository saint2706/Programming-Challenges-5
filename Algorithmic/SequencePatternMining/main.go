package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"math"
	"sort"
)

func main() {
	inputPath := flag.String("input", "", "Path to JSON file containing sequences ([][][]string)")
	minSupportFlag := flag.Float64("minsup", 0.5, "Minimum support threshold. Values in (0,1] are treated as a fraction; values >=1 are treated as absolute counts")
	flag.Parse()

	if *inputPath == "" {
		log.Fatalf("input path is required")
	}

	raw, err := ioutil.ReadFile(*inputPath)
	if err != nil {
		log.Fatalf("failed to read input: %v", err)
	}

	var rawSeqs [][][]string
	if err := json.Unmarshal(raw, &rawSeqs); err != nil {
		log.Fatalf("failed to parse JSON input: %v", err)
	}

	db := make([]Sequence, len(rawSeqs))
	for i, seq := range rawSeqs {
		converted := make(Sequence, len(seq))
		for j, set := range seq {
			items := make(Itemset, len(set))
			for k, val := range set {
				items[k] = Item(val)
			}
			converted[j] = items
		}
		db[i] = converted
	}

	minSupport := computeSupportThreshold(*minSupportFlag, len(db))
	patterns, err := MinePrefixSpan(db, minSupport)
	if err != nil {
		log.Fatalf("mining failed: %v", err)
	}

	sort.Slice(patterns, func(i, j int) bool {
		if len(patterns[i].Sequence) == len(patterns[j].Sequence) {
			return FormatPattern(patterns[i].Sequence) < FormatPattern(patterns[j].Sequence)
		}
		return len(patterns[i].Sequence) < len(patterns[j].Sequence)
	})

	fmt.Printf("Minimum support: %d\n", minSupport)
	for _, p := range patterns {
		fmt.Printf("%s : %d\n", FormatPattern(p.Sequence), p.Support)
	}
}

func computeSupportThreshold(flagVal float64, total int) int {
	if flagVal <= 0 {
		log.Fatalf("minsup must be positive")
	}
	if flagVal < 1 {
		return int(math.Ceil(flagVal * float64(total)))
	}
	return int(flagVal)
}
