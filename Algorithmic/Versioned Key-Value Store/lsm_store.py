import os
import json
import time
import glob
from typing import Optional, List, Tuple

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
            self.size_bytes -= (len(key) + len(old_val))

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
        Since it's sorted, we could binary search if we had fixed offsets.
        For simplicity, we scan.
        Note: Real SSTables use sparse indexes.
        """
        if not os.path.exists(self.filepath):
            return None

        # Optimization: Only read if file exists
        # We assume file content is line-delimited JSON: {"k": "key", "v": "value"}
        # And it's sorted by key.

        # We can optimize by binary search on lines if fixed width,
        # or reading fully if small.
        # Let's assume we read line by line.
        try:
            with open(self.filepath, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        k = entry['k']
                        if k == key:
                            return entry['v']
                        if k > key:
                            # Since sorted, if we pass it, it's not there
                            return None
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            return None
        return None

    @staticmethod
    def create(filepath: str, data: dict):
        # Sort keys
        sorted_keys = sorted(data.keys())
        with open(filepath, 'w') as f:
            for k in sorted_keys:
                entry = {'k': k, 'v': data[k]}
                f.write(json.dumps(entry) + "\n")

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
        timestamp = int(time.time() * 1000000) # Microseconds
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
        files = self._get_sstable_files() # Newest first
        files.reverse() # Oldest first

        merged = {}
        for fpath in files:
            with open(fpath, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        merged[entry['k']] = entry['v']
                    except json.JSONDecodeError:
                        continue

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
