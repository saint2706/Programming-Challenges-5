package compression

import (
	"bytes"
	"encoding/binary"
	"fmt"
)

// LZ78Token represents a dictionary index and the next literal byte.
type LZ78Token struct {
	Index uint64
	Next  byte
}

// LZ78Compress compresses data using the LZ78 algorithm. The format stores the
// original length as a uvarint followed by tokens of [index][next byte].
func LZ78Compress(data []byte) ([]byte, error) {
	var buf bytes.Buffer
	tmp := make([]byte, binary.MaxVarintLen64)
	n := binary.PutUvarint(tmp, uint64(len(data)))
	buf.Write(tmp[:n])

	dict := map[string]uint64{"": 0}
	sequence := make([]byte, 0)
	nextIndex := uint64(1)

	for i := 0; i < len(data); {
		sequence = sequence[:0]
		index := uint64(0)
		for i < len(data) {
			candidate := append(sequence, data[i])
			if idx, ok := dict[string(candidate)]; ok {
				sequence = append(sequence, data[i])
				index = idx
				i++
				continue
			}
			next := data[i]
			writeLZ78Token(&buf, index, next)
			dict[string(candidate)] = nextIndex
			nextIndex++
			i++
			goto nextIteration
		}
		// All remaining data already in dictionary; emit terminal token.
		writeLZ78Token(&buf, index, 0)
	nextIteration:
	}

	return buf.Bytes(), nil
}

func writeLZ78Token(buf *bytes.Buffer, index uint64, next byte) {
	tmp := make([]byte, binary.MaxVarintLen64)
	n := binary.PutUvarint(tmp, index)
	buf.Write(tmp[:n])
	buf.WriteByte(next)
}

// LZ78Decompress restores data compressed with LZ78Compress.
func LZ78Decompress(data []byte) ([]byte, error) {
	reader := bytes.NewBuffer(data)
	origLen, err := binary.ReadUvarint(reader)
	if err != nil {
		return nil, fmt.Errorf("read original length: %w", err)
	}
	output := make([]byte, 0, origLen)
	dict := [][]byte{nil}

	for uint64(len(output)) < origLen {
		index, err := binary.ReadUvarint(reader)
		if err != nil {
			return nil, fmt.Errorf("read index: %w", err)
		}
		nextByte, err := reader.ReadByte()
		if err != nil {
			return nil, fmt.Errorf("read next byte: %w", err)
		}
		if int(index) >= len(dict) {
			return nil, fmt.Errorf("invalid index %d", index)
		}
		entry := append([]byte{}, dict[index]...)
		if uint64(len(output)+len(entry)) > origLen {
			entry = entry[:int(origLen)-len(output)]
		}
		output = append(output, entry...)
		if uint64(len(output)) < origLen {
			output = append(output, nextByte)
			dict = append(dict, append(entry, nextByte))
		}
	}

	return output, nil
}
