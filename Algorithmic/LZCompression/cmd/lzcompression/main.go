package main

import (
	"flag"
	"fmt"
	"io/ioutil"
	"os"

	"lzcompression/compression"
)

func main() {
	mode := flag.String("mode", "compress", "operation mode: compress or decompress")
	algo := flag.String("algo", "lz77", "compression algorithm: lz77 or lz78")
	inputPath := flag.String("input", "", "path to input file")
	outputPath := flag.String("output", "", "path to output file")
	window := flag.Int("window", 4096, "window size for lz77")
	lookahead := flag.Int("lookahead", 32, "lookahead size for lz77")

	flag.Parse()

	if *inputPath == "" || *outputPath == "" {
		fmt.Fprintln(os.Stderr, "input and output paths are required")
		os.Exit(1)
	}

	inputData, err := ioutil.ReadFile(*inputPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to read input: %v\n", err)
		os.Exit(1)
	}

	switch *mode {
	case "compress":
		compress(*algo, inputData, *outputPath, *window, *lookahead)
	case "decompress":
		decompress(*algo, inputData, *outputPath)
	default:
		fmt.Fprintf(os.Stderr, "unknown mode %s\n", *mode)
		os.Exit(1)
	}
}

func compress(algo string, input []byte, outPath string, window, lookahead int) {
	var (
		output []byte
		err    error
	)
	switch algo {
	case "lz77":
		output, err = compression.LZ77Compress(input, compression.LZ77Options{WindowSize: window, LookaheadSize: lookahead})
	case "lz78":
		output, err = compression.LZ78Compress(input)
	default:
		fmt.Fprintf(os.Stderr, "unknown algorithm %s\n", algo)
		os.Exit(1)
	}
	if err != nil {
		fmt.Fprintf(os.Stderr, "compression failed: %v\n", err)
		os.Exit(1)
	}
	if err := os.WriteFile(outPath, output, 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "failed to write output: %v\n", err)
		os.Exit(1)
	}
}

func decompress(algo string, input []byte, outPath string) {
	var (
		output []byte
		err    error
	)
	switch algo {
	case "lz77":
		output, err = compression.LZ77Decompress(input)
	case "lz78":
		output, err = compression.LZ78Decompress(input)
	default:
		fmt.Fprintf(os.Stderr, "unknown algorithm %s\n", algo)
		os.Exit(1)
	}
	if err != nil {
		fmt.Fprintf(os.Stderr, "decompression failed: %v\n", err)
		os.Exit(1)
	}
	if err := os.WriteFile(outPath, output, 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "failed to write output: %v\n", err)
		os.Exit(1)
	}
}
