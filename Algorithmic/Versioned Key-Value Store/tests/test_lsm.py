import unittest
import shutil
import os
import time
from lsm_store import LSMStore

class TestLSMStore(unittest.TestCase):
    def setUp(self):
        self.data_dir = "test_lsm_data"
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)
        self.store = LSMStore(self.data_dir, memtable_limit=50)

    def tearDown(self):
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)

    def test_put_get(self):
        self.store.put("key1", "val1")
        self.assertEqual(self.store.get("key1"), "val1")
        self.assertIsNone(self.store.get("key2"))

    def test_flush(self):
        # Fill memtable to force flush
        # "keyX" + "valueX" is approx 10 bytes. Limit is 50.
        for i in range(10):
            self.store.put(f"key{i}", f"value{i}")

        # Should have flushed at least once. Check for .sst files
        files = os.listdir(self.data_dir)
        sst_files = [f for f in files if f.endswith(".sst")]
        self.assertTrue(len(sst_files) > 0)

        # Verify data persists
        self.assertEqual(self.store.get("key0"), "value0")
        self.assertEqual(self.store.get("key9"), "value9")

    def test_update(self):
        self.store.put("key1", "val1")
        self.store.flush()
        self.store.put("key1", "val2") # Update in memtable (or new sst)

        self.assertEqual(self.store.get("key1"), "val2")

    def test_delete(self):
        self.store.put("key1", "val1")
        self.store.flush()
        self.store.delete("key1")

        self.assertIsNone(self.store.get("key1"))

    def test_compaction(self):
        self.store.put("key1", "val1")
        self.store.flush()
        time.sleep(0.01) # Ensure timestamp diff
        self.store.put("key1", "val2") # Overwrite
        self.store.flush()

        # We have 2 sst files.
        self.store.compact_all()

        # Should have 1 sst file now
        files = [f for f in os.listdir(self.data_dir) if f.endswith(".sst")]
        self.assertEqual(len(files), 1)

        self.assertEqual(self.store.get("key1"), "val2")

if __name__ == '__main__':
    unittest.main()
