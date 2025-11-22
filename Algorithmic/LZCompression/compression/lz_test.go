package compression

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

func TestLZ77RoundTripStrings(t *testing.T) {
	cases := []string{
		"abracadabra",
		"TOBEORNOTTOBEORTOBEORNOT",
		"ABABABA",
		"the quick brown fox jumps over the lazy dog",
		"aaaaabbbbbcccccdddddeeeeefffff",
	}
	for i, tc := range cases {
		t.Run(fmt.Sprintf("case_%d", i), func(t *testing.T) {
			compressed, err := LZ77Compress([]byte(tc), LZ77Options{WindowSize: 16, LookaheadSize: 8})
			if err != nil {
				t.Fatalf("compress failed: %v", err)
			}
			decompressed, err := LZ77Decompress(compressed)
			if err != nil {
				t.Fatalf("decompress failed: %v", err)
			}
			if string(decompressed) != tc {
				t.Fatalf("expected %q got %q", tc, string(decompressed))
			}
		})
	}
}

func TestLZ78RoundTripStrings(t *testing.T) {
	cases := []string{
		"abracadabra",
		"TOBEORNOTTOBEORTOBEORNOT",
		"mississippi river",
		"bananabananabanana",
	}
	for i, tc := range cases {
		t.Run(fmt.Sprintf("case_%d", i), func(t *testing.T) {
			compressed, err := LZ78Compress([]byte(tc))
			if err != nil {
				t.Fatalf("compress failed: %v", err)
			}
			decompressed, err := LZ78Decompress(compressed)
			if err != nil {
				t.Fatalf("decompress failed: %v", err)
			}
			if string(decompressed) != tc {
				t.Fatalf("expected %q got %q", tc, string(decompressed))
			}
		})
	}
}

func TestRoundTripFiles(t *testing.T) {
	data := []byte("A longish payload with repetition. A longish payload with repetition. Numbers 1234567890 and symbols !@#$%\n")
	tempDir := t.TempDir()
	inputPath := filepath.Join(tempDir, "input.txt")
	if err := os.WriteFile(inputPath, data, 0o644); err != nil {
		t.Fatalf("write input: %v", err)
	}

	compressed, err := LZ77Compress(data, LZ77Options{})
	if err != nil {
		t.Fatalf("lz77 compress: %v", err)
	}
	decompressed, err := LZ77Decompress(compressed)
	if err != nil {
		t.Fatalf("lz77 decompress: %v", err)
	}
	if string(decompressed) != string(data) {
		t.Fatalf("lz77 mismatch: %q", string(decompressed))
	}

	compressed78, err := LZ78Compress(data)
	if err != nil {
		t.Fatalf("lz78 compress: %v", err)
	}
	decompressed78, err := LZ78Decompress(compressed78)
	if err != nil {
		t.Fatalf("lz78 decompress: %v", err)
	}
	if string(decompressed78) != string(data) {
		t.Fatalf("lz78 mismatch: %q", string(decompressed78))
	}

	moduleRoot, err := filepath.Abs("..")
	if err != nil {
		t.Fatalf("determine module root: %v", err)
	}

	compressedPath := filepath.Join(tempDir, "compressed.bin")
	outputPath := filepath.Join(tempDir, "output.txt")

	cmd := exec.Command("go", "run", "./cmd/lzcompression", "-mode", "compress", "-algo", "lz77", "-input", inputPath, "-output", compressedPath)
	cmd.Dir = moduleRoot
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("cli compress failed: %v, output: %s", err, string(out))
	}

	cmd = exec.Command("go", "run", "./cmd/lzcompression", "-mode", "decompress", "-algo", "lz77", "-input", compressedPath, "-output", outputPath)
	cmd.Dir = moduleRoot
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("cli decompress failed: %v, output: %s", err, string(out))
	}

	restored, err := os.ReadFile(outputPath)
	if err != nil {
		t.Fatalf("read restored: %v", err)
	}
	if string(restored) != string(data) {
		t.Fatalf("cli restored mismatch: %q", string(restored))
	}
}
