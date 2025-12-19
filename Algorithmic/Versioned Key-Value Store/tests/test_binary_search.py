import os
import shutil
import unittest

from lsm_store import LSMStore, SSTable


class TestBinarySearch(unittest.TestCase):
    def setUp(self):
        self.data_dir = "test_lsm_binary_search"
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)
        self.store = LSMStore(
            self.data_dir, memtable_limit=1024 * 1024
        )  # Large limit to manually control flush

    def tearDown(self):
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)

    def test_large_dataset_binary_search(self):
        # Insert enough data to create a decent sized SSTable
        num_records = 1000
        data = {f"key{i:05d}": f"value{i}" for i in range(num_records)}

        # Manually create SSTable to ensure it's one file
        sstable_path = os.path.join(self.data_dir, "sstable_test.sst")
        SSTable.create(sstable_path, data)

        sst = SSTable(sstable_path)

        # Verify all keys can be found
        for i in range(num_records):
            key = f"key{i:05d}"
            val = sst.get(key)
            self.assertEqual(val, f"value{i}", f"Failed to find {key}")

        # Verify non-existent keys
        self.assertIsNone(sst.get("key99999"))
        self.assertIsNone(sst.get("key00000a"))  # between keys potentially

    def test_mixed_length_keys_and_values(self):
        # To test padding logic
        data = {
            "a": "short",
            "long_key_name": "long_value_content_to_test_padding",
            "medium": "med",
        }
        sstable_path = os.path.join(self.data_dir, "sstable_mixed.sst")
        SSTable.create(sstable_path, data)

        sst = SSTable(sstable_path)
        self.assertEqual(sst.get("a"), "short")
        self.assertEqual(sst.get("long_key_name"), "long_value_content_to_test_padding")
        self.assertEqual(sst.get("medium"), "med")
        self.assertIsNone(sst.get("b"))


if __name__ == "__main__":
    unittest.main()
