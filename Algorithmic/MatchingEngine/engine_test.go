package main

import (
	"reflect"
	"testing"
)

func TestMatchingEngine(t *testing.T) {
	ob := NewOrderBook()

	// 1. Add Sell Limit 100 @ 10
	s1 := &Order{ID: 1, Type: Sell, Price: 10.0, Quantity: 100, Timestamp: 1}
	t1 := ob.AddOrder(s1)
	if len(t1) != 0 {
		t.Errorf("Expected 0 trades, got %d", len(t1))
	}
	if ob.Asks.Len() != 1 {
		t.Errorf("Asks len should be 1")
	}

	// 2. Add Buy Limit 50 @ 9 (No match)
	b1 := &Order{ID: 2, Type: Buy, Price: 9.0, Quantity: 50, Timestamp: 2}
	t2 := ob.AddOrder(b1)
	if len(t2) != 0 {
		t.Errorf("Expected 0 trades, got %d", len(t2))
	}
	if ob.Bids.Len() != 1 {
		t.Errorf("Bids len should be 1")
	}

	// 3. Add Buy Limit 50 @ 10 (Match full)
	b2 := &Order{ID: 3, Type: Buy, Price: 10.0, Quantity: 50, Timestamp: 3}
	t3 := ob.AddOrder(b2)
	if len(t3) != 1 {
		t.Fatalf("Expected 1 trade, got %d", len(t3))
	}
	wantTrade := Trade{BuyID: 3, SellID: 1, Price: 10.0, Quantity: 50}
	if !reflect.DeepEqual(t3[0], wantTrade) {
		t.Errorf("Trade mismatch: got %v, want %v", t3[0], wantTrade)
	}

	// Check remaining qty
	// Sell 1 has 50 left.
	if ob.Asks.Peek().Quantity != 50 {
		t.Errorf("Remaining ask qty should be 50, got %f", ob.Asks.Peek().Quantity)
	}

	// 4. Add Buy Limit 100 @ 11 (Match partial remaining + stay in book?)
	// Matches remaining 50 @ 10 (best ask).
	// Remainder 50 @ 11 sits in book.
	b3 := &Order{ID: 4, Type: Buy, Price: 11.0, Quantity: 100, Timestamp: 4}
	t4 := ob.AddOrder(b3)
	if len(t4) != 1 {
		t.Fatalf("Expected 1 trade, got %d", len(t4))
	}
	wantTrade2 := Trade{BuyID: 4, SellID: 1, Price: 10.0, Quantity: 50}
	if !reflect.DeepEqual(t4[0], wantTrade2) {
		t.Errorf("Trade mismatch: got %v, want %v", t4[0], wantTrade2)
	}

	if ob.Asks.Len() != 0 {
		t.Errorf("Asks should be empty")
	}
	if ob.Bids.Len() != 2 { // b1 (9.0) and b3 (rem 11.0)
		t.Errorf("Bids should have 2 orders")
	}
	if ob.Bids.Peek().Price != 11.0 { // Highest bid
		t.Errorf("Top bid should be 11.0")
	}
}
