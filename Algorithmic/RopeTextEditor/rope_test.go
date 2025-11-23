package main

import (
	"testing"
)

func TestRope(t *testing.T) {
	r := NewRope("Hello")
	if r.String() != "Hello" {
		t.Errorf("Expected Hello, got %s", r.String())
	}

	r = r.Insert(5, " World")
	if r.String() != "Hello World" {
		t.Errorf("Expected Hello World, got %s", r.String())
	}

	r = r.Insert(0, "Say: ")
	if r.String() != "Say: Hello World" {
		t.Errorf("Expected Say: Hello World, got %s", r.String())
	}

	// Say: Hello World -> Length 16
	// Delete "Hello " (indices 5 to 11)
	r = r.Delete(5, 11)
	if r.String() != "Say: World" {
		t.Errorf("Expected Say: World, got %s", r.String())
	}

	// Split test
	left, right := r.Split(4) // "Say:" and " World"
	if left.String() != "Say:" {
		t.Errorf("Left split failed: %s", left.String())
	}
	if right.String() != " World" {
		t.Errorf("Right split failed: %s", right.String())
	}

	// Concat test
	r2 := Concat(left, right)
	if r2.String() != "Say: World" {
		t.Errorf("Concat failed: %s", r2.String())
	}

	// Index test
	c, err := r2.Index(0)
	if err != nil || c != 'S' {
		t.Errorf("Index 0 failed")
	}
	c, err = r2.Index(5) // 'W'
	if err != nil || c != 'W' {
		t.Errorf("Index 5 failed, got %c", c)
	}
}
