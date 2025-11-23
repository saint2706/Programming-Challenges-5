package main

import (
	"testing"
)

func TestPersistentArray(t *testing.T) {
	// 1. Create empty
	v0 := NewPersistentArray()
	if v0.Size != 0 {
		t.Errorf("Expected size 0, got %d", v0.Size)
	}

	// 2. Append 10, 20, 30
	v1 := v0.Push(10)
	v2 := v1.Push(20)
	v3 := v2.Push(30)

	if v3.Size != 3 {
		t.Errorf("Expected size 3, got %d", v3.Size)
	}

	val, err := v3.Get(0)
	if err != nil || val != 10 {
		t.Errorf("v3[0] = %d, err=%v; want 10", val, err)
	}
	val, err = v3.Get(1)
	if err != nil || val != 20 {
		t.Errorf("v3[1] = %d, err=%v; want 20", val, err)
	}
	val, err = v3.Get(2)
	if err != nil || val != 30 {
		t.Errorf("v3[2] = %d, err=%v; want 30", val, err)
	}

	// 3. Verify persistence (old versions unchanged)
	if v1.Size != 1 {
		t.Errorf("v1 size changed to %d", v1.Size)
	}
	val, _ = v1.Get(0)
	if val != 10 {
		t.Errorf("v1[0] changed to %d", val)
	}
	_, err = v1.Get(1) // should fail
	if err == nil {
		t.Error("v1[1] should error")
	}

	// 4. Set (Update)
	// Modify v3[1] (was 20) -> 99. Create v4.
	v4, err := v3.Set(1, 99)
	if err != nil {
		t.Fatalf("Set failed: %v", err)
	}

	val, _ = v4.Get(1)
	if val != 99 {
		t.Errorf("v4[1] = %d, want 99", val)
	}
	val, _ = v3.Get(1)
	if val != 20 {
		t.Errorf("v3[1] changed to %d, want 20", val)
	}

	// 5. Large Append Test (trigger growth)
	curr := v0
	for i := 0; i < 100; i++ {
		curr = curr.Push(i)
	}
	if curr.Size != 100 {
		t.Errorf("Size is %d, want 100", curr.Size)
	}
	for i := 0; i < 100; i++ {
		val, err := curr.Get(i)
		if err != nil {
			t.Errorf("Get(%d) error: %v", i, err)
		}
		if val != i {
			t.Errorf("Get(%d) = %d, want %d", i, val, i)
		}
	}
}
