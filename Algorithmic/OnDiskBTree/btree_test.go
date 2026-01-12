package main

import (
	"os"
	"testing"
)

func TestBTree(t *testing.T) {
	tmpFile, err := os.CreateTemp("", "btree_test.db")
	if err != nil {
		t.Fatal(err)
	}
	dbName := tmpFile.Name()
	tmpFile.Close()
	defer os.Remove(dbName)

	bt, err := NewBTree(dbName)
	if err != nil {
		t.Fatal(err)
	}
	defer bt.Close()

	// 1. Insert fewer than split
	bt.Insert(10, 100)
	bt.Insert(20, 200)
	bt.Insert(5, 50)

	val, found := bt.Search(10)
	if !found || val != 100 {
		t.Errorf("Search(10) = %d, found=%v; want 100", val, found)
	}

	// 2. Insert to trigger split
	// Order = 6. Max keys = 5.
	// Currently 3 keys: 5, 10, 20.
	// Add 30, 40, 50.
	bt.Insert(30, 300)
	bt.Insert(40, 400) // 5 keys. Full.
	bt.Insert(50, 500) // Trigger split.

	// Check all
	keys := []int64{5, 10, 20, 30, 40, 50}
	for _, k := range keys {
		v, ok := bt.Search(k)
		if !ok || v != k*10 {
			t.Errorf("Post-split Search(%d) failed", k)
		}
	}

	// 3. More splits (depth increase)
	for i := 60; i <= 100; i += 10 {
		bt.Insert(int64(i), int64(i*10))
	}

	v, ok := bt.Search(100)
	if !ok || v != 1000 {
		t.Errorf("Search(100) failed")
	}
}
