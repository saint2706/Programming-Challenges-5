# Lossless Compression (LZ77/78)

Implementations of LZ77 and LZ78 lossless compression algorithms that form the basis of many modern compression tools.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)

## 🧠 Theory

**LZ compression** algorithms exploit repeated patterns in data by replacing them with references to earlier occurrences.

### LZ77

- **Sliding window** approach
- Encodes as: (offset, length, next_char)
- **Example**: "AABBAABB" → (0,0,'A'), (1,1,'B'), (4,4,'')
- Used in: DEFLATE (ZIP, gzip)

### LZ78

- **Dictionary-based** approach
- Build dictionary of seen patterns
- Encodes as: (dictionary_index, next_char)
- **Example**: "AABBAABB" → (0,'A'), (1,'A'), (0,'B'), (3,'B')
- Used in: GIF, Unix compress

### Key Differences

| Feature          | LZ77                   | LZ78               |
| :--------------- | :--------------------- | :----------------- |
| **Memory**       | Fixed window           | Growing dictionary |
| **Encoding**     | (offset, length, char) | (index, char)      |
| **Adaptability** | Limited to window      | Unlimited patterns |

## 💻 Installation

```bash
go build ./cmd/lzcompression
go test ./compression
```

## 🚀 Usage

### LZ77 Compression

```go
package main

import (
    "lzcompression/compression"
)

func main() {
    data := []byte("AABBAABBAABBAABB")

    // Compress
    compressed := compression.LZ77Compress(data, 4096)  // 4KB window

    // Decompress
    decompressed := compression.LZ77Decompress(compressed)

    ratio := float64(len(compressed)) / float64(len(data))
    fmt.Printf("Compression ratio: %.2f%%\n", ratio * 100)
}
```

### LZ78 Compression

```go
package main

import (
    "lzcompression/compression"
)

func main() {
    data := []byte("TOBEORNOTTOBEORTOBEORNOT")

    compressed := compression.LZ78Compress(data)
    decompressed := compression.LZ78Decompress(compressed)
}
```

## 📊 Complexity Analysis

| Algorithm | Compression Time | Decompression Time | Space  |
| :-------- | :--------------- | :----------------- | :----- |
| **LZ77**  | $O(n \cdot w)$   | $O(n)$             | $O(w)$ |
| **LZ78**  | $O(n)$           | $O(n)$             | $O(d)$ |

Where:

- $n$ = input size
- $w$ = window size (LZ77)
- $d$ = dictionary size (LZ78)
