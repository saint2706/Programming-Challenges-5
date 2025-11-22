package compression

import (
	"bytes"
	"encoding/binary"
	"fmt"
)

// LZ77Options controls window and lookahead sizes for compression.
type LZ77Options struct {
	WindowSize    int
	LookaheadSize int
}

// LZ77Compress compresses data using the LZ77 algorithm with the provided options.
// The encoded format stores the original length as a uvarint followed by tokens of
// [offset][length][next byte], where offset and length are uvarints.
func LZ77Compress(data []byte, opts LZ77Options) ([]byte, error) {
	if opts.WindowSize <= 0 {
		opts.WindowSize = 4096
	}
	if opts.LookaheadSize <= 0 {
		opts.LookaheadSize = 32
	}
	var buf bytes.Buffer
	tmp := make([]byte, binary.MaxVarintLen64)
	n := binary.PutUvarint(tmp, uint64(len(data)))
	buf.Write(tmp[:n])

	i := 0
	for i < len(data) {
		// Ensure there is always one byte left for the next literal.
		if i == len(data)-1 {
			writeLZ77Token(&buf, 0, 0, data[i])
			break
		}
		windowStart := i - opts.WindowSize
		if windowStart < 0 {
			windowStart = 0
		}
		lookaheadLimit := opts.LookaheadSize
		remaining := len(data) - i - 1 // leave space for next literal
		if remaining < lookaheadLimit {
			lookaheadLimit = remaining
		}
		offset, length := longestMatch(data[windowStart:i], data[i:i+lookaheadLimit])
		nextByte := data[i+length]
		writeLZ77Token(&buf, offset, length, nextByte)
		i += length + 1
	}

	return buf.Bytes(), nil
}

func writeLZ77Token(buf *bytes.Buffer, offset, length int, next byte) {
	tmp := make([]byte, binary.MaxVarintLen64)
	n := binary.PutUvarint(tmp, uint64(offset))
	buf.Write(tmp[:n])
	n = binary.PutUvarint(tmp, uint64(length))
	buf.Write(tmp[:n])
	buf.WriteByte(next)
}

func longestMatch(window, lookahead []byte) (int, int) {
	if len(window) == 0 || len(lookahead) == 0 {
		return 0, 0
	}
	maxLen := 0
	bestOffset := 0
	for i := 0; i < len(window); i++ {
		matchLen := 0
		for matchLen < len(lookahead) && window[i+matchLen] == lookahead[matchLen] {
			matchLen++
			if i+matchLen >= len(window) {
				break
			}
		}
		if matchLen > maxLen {
			maxLen = matchLen
			bestOffset = len(window) - i
		}
	}
	return bestOffset, maxLen
}

// LZ77Decompress restores the original data from an LZ77 encoded byte slice.
func LZ77Decompress(data []byte) ([]byte, error) {
	reader := bytes.NewBuffer(data)
	origLen, err := binary.ReadUvarint(reader)
	if err != nil {
		return nil, fmt.Errorf("read original length: %w", err)
	}
	output := make([]byte, 0, origLen)
	for uint64(len(output)) < origLen {
		offset, err := binary.ReadUvarint(reader)
		if err != nil {
			return nil, fmt.Errorf("read offset: %w", err)
		}
		length, err := binary.ReadUvarint(reader)
		if err != nil {
			return nil, fmt.Errorf("read length: %w", err)
		}
		nextByte, err := reader.ReadByte()
		if err != nil {
			return nil, fmt.Errorf("read next byte: %w", err)
		}
		if offset > 0 {
			if int(offset) > len(output) {
				return nil, fmt.Errorf("invalid offset %d greater than output size %d", offset, len(output))
			}
			start := len(output) - int(offset)
			for i := 0; i < int(length) && uint64(len(output)) < origLen; i++ {
				output = append(output, output[start+i])
			}
		}
		if uint64(len(output)) < origLen {
			output = append(output, nextByte)
		}
	}
	return output, nil
}
