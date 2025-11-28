import os
import shutil

from lsm_store import LSMStore


def main():
    data_dir = "lsm_data"
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)  # Clean start

    # Small limit to force flushes
    store = LSMStore(data_dir, memtable_limit=20)

    print("Putting 'user1': 'Alice'")
    store.put("user1", "Alice")

    print("Putting 'user2': 'Bob'")
    store.put("user2", "Bob")

    # Check
    print(f"Get 'user1': {store.get('user1')}")

    # Force flush by adding more data (approx 20 bytes limit)
    print("Putting 'user3': 'Charlie' (triggers flush?)")
    store.put("user3", "Charlie")

    # Force another flush
    store.put("user4", "Dave")
    store.put("user5", "Eve")

    print(f"Get 'user1' (from disk?): {store.get('user1')}")

    # Update user1
    print("Updating 'user1': 'Alice_Updated'")
    store.put("user1", "Alice_Updated")

    print(f"Get 'user1': {store.get('user1')}")

    # Delete
    print("Deleting 'user2'")
    store.delete("user2")

    print(f"Get 'user2': {store.get('user2')}")

    # Compaction
    print("Compacting...")
    store.compact_all()

    print(f"Get 'user1' after compact: {store.get('user1')}")
    print(f"Get 'user2' after compact: {store.get('user2')}")


if __name__ == "__main__":
    main()
