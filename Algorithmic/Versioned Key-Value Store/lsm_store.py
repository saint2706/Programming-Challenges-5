import glob
import json
import os
import time
from typing import List, Optional


class MemTable:
    def __init__(self, limit_bytes: int = 1024):
        self.data = {}
        self.size_bytes = 0
        self.limit_bytes = limit_bytes

    def put(self, key: str, value: str):
        # Calculate size diff (approx)
        old_val = self.data.get(key)
        new_entry_size = len(key) + len(value)

        if old_val:
            self.size_bytes -= len(key) + len(old_val)

        self.data[key] = value
        self.size_bytes += new_entry_size

    def get(self, key: str) -> Optional[str]:
        return self.data.get(key)

    def is_full(self) -> bool:
        return self.size_bytes >= self.limit_bytes

    def clear(self):
        self.data = {}
        self.size_bytes = 0


class SSTable:
    def __init__(self, filepath: str):
        self.filepath = filepath
        # We could load a sparse index here for speed

    def get(self, key: str) -> Optional[str]:
        """
        Search for key in the SSTable file.
        Uses binary search if the file is in the new fixed-width format (header starts with FMT1).
        Otherwise falls back to linear scan.
        """
        if not os.path.exists(self.filepath):
            return None

        try:
            with open(self.filepath, "rb") as f:
                # Check for header
                header_snippet = f.read(21) # "FMT1 " + 16 chars + "\n"

                is_fixed_width = False
                record_len = 0
                header_size = 0

                try:
                    if header_snippet.startswith(b"FMT1 "):
                        # Parse length
                        # Format: FMT1 <16 hex chars>\n
                        hex_len = header_snippet[5:21]
                        max_len = int(hex_len, 16)
                        record_len = max_len + 1 # +1 for newline
                        header_size = 22 # FMT1 + space + 16 hex + \n = 4 + 1 + 16 + 1 = 22
                        is_fixed_width = True
                except ValueError:
                    # Not a valid header, fallback
                    pass

                if is_fixed_width:
                    # Binary Search
                    f.seek(0, 2)
                    file_size = f.tell()
                    data_size = file_size - header_size
                    if data_size <= 0:
                        return None

                    num_records = data_size // record_len

                    low = 0
                    high = num_records - 1

                    while low <= high:
                        mid = (low + high) // 2
                        offset = header_size + mid * record_len
                        f.seek(offset)
                        line_bytes = f.read(record_len)
                        if not line_bytes:
                            break

                        try:
                            line_str = line_bytes.decode('utf-8').strip()
                            entry = json.loads(line_str)
                            k = entry["k"]

                            if k == key:
                                return entry["v"]
                            elif k < key:
                                low = mid + 1
                            else:
                                high = mid - 1
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            # Should not happen in a valid file
                            break
                    return None

                else:
                    # Fallback to linear scan for legacy files
                    f.seek(0)
                    # We need to read line by line. Since we opened in binary, use wrapper or manual read.
                    # Or close and reopen in text mode. Reopening is simpler.
                    pass

        except FileNotFoundError:
            return None

        # Fallback linear scan
        try:
            with open(self.filepath, "r", encoding='utf-8') as f:
                for line in f:
                    # Skip header if it exists but wasn't handled (shouldn't happen with above logic but safe)
                    if line.startswith("FMT1 "):
                        continue
                    try:
                        entry = json.loads(line)
                        k = entry["k"]
                        if k == key:
                            return entry["v"]
                        if k > key:
                            return None
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            return None
        return None

    def __iter__(self):
        """Iterates over all entries in the SSTable."""
        if not os.path.exists(self.filepath):
            return

        with open(self.filepath, "rb") as f:
            header_snippet = f.read(22)
            is_fixed_width = header_snippet.startswith(b"FMT1 ")

            if is_fixed_width:
                # We are at offset 22
                pass
            else:
                f.seek(0)

            # Read rest of file
            # Since we might have padded lines, we can read line by line.
            # Python's binary file iterator yields lines ending in \n.
            for line in f:
                try:
                    line_str = line.decode('utf-8').strip()
                    if not line_str:
                        continue
                    entry = json.loads(line_str)
                    yield entry
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue

    @staticmethod
    def create(filepath: str, data: dict):
        # Sort keys
        sorted_keys = sorted(data.keys())

        # Determine max length for fixed-width records
        max_len = 0
        serialized_entries = []
        for k in sorted_keys:
            entry = {"k": k, "v": data[k]}
            # Ensure no newlines in JSON output to keep it on one line per record
            s = json.dumps(entry)
            max_len = max(max_len, len(s))
            serialized_entries.append(s)

        # We will write a header: "FMT1 <16-byte-hex-len>\n"
        # FMT1 indicates Format 1.
        # The length is the fixed size of each record line (including newline).
        # We'll pad each JSON to max_len, then add '\n'.
        # Total line size = max_len + 1 (assuming '\n' is 1 byte, we'll force binary write or similar).

        header_fmt = "FMT1 {:016x}\n"
        # max_len must accommodate the JSON + padding.
        # Record size = max_len + 1.

        with open(filepath, "wb") as f:
            # Write header
            header_str = header_fmt.format(max_len)
            f.write(header_str.encode('utf-8'))

            for s in serialized_entries:
                # Pad with spaces
                padded = s.ljust(max_len) + "\n"
                f.write(padded.encode('utf-8'))


class LSMStore:
    def __init__(self, data_dir: str, memtable_limit: int = 100):
        self.data_dir = data_dir
        self.memtable = MemTable(limit_bytes=memtable_limit)
        self.memtable_limit = memtable_limit

        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

    def _get_sstable_files(self) -> List[str]:
        # Get all .sst files, sort by timestamp (name) reverse (newest first)
        files = glob.glob(os.path.join(self.data_dir, "sstable_*.sst"))
        # Filename format: sstable_{timestamp}.sst
        # Sort reverse
        files.sort(key=lambda x: x, reverse=True)
        return files

    def put(self, key: str, value: str):
        self.memtable.put(key, value)
        if self.memtable.is_full():
            self.flush()

    def get(self, key: str) -> Optional[str]:
        # 1. Check MemTable
        val = self.memtable.get(key)
        if val is not None:
            if val == "__TOMBSTONE__":
                return None
            return val

        # 2. Check SSTables (Newest to Oldest)
        sst_files = self._get_sstable_files()
        for sst_file in sst_files:
            sst = SSTable(sst_file)
            val = sst.get(key)
            if val is not None:
                if val == "__TOMBSTONE__":
                    return None
                return val

        return None

    def delete(self, key: str):
        # Write tombstone
        self.put(key, "__TOMBSTONE__")

    def flush(self):
        if not self.memtable.data:
            return

        # Ensure unique timestamp
        timestamp = int(time.time() * 1000000)  # Microseconds
        filename = f"sstable_{timestamp}.sst"
        filepath = os.path.join(self.data_dir, filename)

        # Safety check if file exists (unlikely with microseconds but possible)
        while os.path.exists(filepath):
            timestamp += 1
            filename = f"sstable_{timestamp}.sst"
            filepath = os.path.join(self.data_dir, filename)

        SSTable.create(filepath, self.memtable.data)
        self.memtable.clear()

    def compact_all(self):
        self.flush()
        files = self._get_sstable_files()  # Newest first
        files.reverse()  # Oldest first

        merged = {}
        for fpath in files:
            sst = SSTable(fpath)
            for entry in sst:
                merged[entry["k"]] = entry["v"]

        # Remove tombstones in the final merge
        final_data = {k: v for k, v in merged.items() if v != "__TOMBSTONE__"}

        # Write to new file
        timestamp = int(time.time() * 1000000)
        new_filename = f"sstable_{timestamp}_compacted.sst"
        new_filepath = os.path.join(self.data_dir, new_filename)

        SSTable.create(new_filepath, final_data)

        # Delete old files
        for fpath in files:
            os.remove(fpath)
