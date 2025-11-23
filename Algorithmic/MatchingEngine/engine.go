package main

import (
	"container/heap"
)

// OrderType represents Buy or Sell.
type OrderType int

const (
	Buy OrderType = iota
	Sell
)

// Order represents a limit order.
type Order struct {
	ID        int
	Type      OrderType
	Price     float64
	Quantity  float64
	Timestamp int64 // Priority for FIFO
}

// OrderBook manages bids and asks.
type OrderBook struct {
	Bids *OrderHeap // Buy orders (Max Heap)
	Asks *OrderHeap // Sell orders (Min Heap)
}

// NewOrderBook creates a new order book.
func NewOrderBook() *OrderBook {
	bids := &OrderHeap{orders: []*Order{}, isMin: false}
	asks := &OrderHeap{orders: []*Order{}, isMin: true}
	heap.Init(bids)
	heap.Init(asks)
	return &OrderBook{
		Bids: bids,
		Asks: asks,
	}
}

// AddOrder adds an order and attempts to match.
func (ob *OrderBook) AddOrder(o *Order) []Trade {
	trades := []Trade{}

	if o.Quantity <= 0 {
		return trades
	}

	if o.Type == Buy {
		// Try to match with Asks (Sell orders)
		for ob.Asks.Len() > 0 && o.Quantity > 0 {
			bestAsk := ob.Asks.Peek()
			if o.Price >= bestAsk.Price {
				// Match
				tradeQty := min(o.Quantity, bestAsk.Quantity)
				trades = append(trades, Trade{
					BuyID:    o.ID,
					SellID:   bestAsk.ID,
					Price:    bestAsk.Price, // Buyer pays seller's ask price
					Quantity: tradeQty,
				})

				o.Quantity -= tradeQty
				bestAsk.Quantity -= tradeQty

				if bestAsk.Quantity <= 0 {
					heap.Pop(ob.Asks)
				}
			} else {
				break
			}
		}
		if o.Quantity > 0 {
			heap.Push(ob.Bids, o)
		}
	} else {
		// Try to match with Bids (Buy orders)
		for ob.Bids.Len() > 0 && o.Quantity > 0 {
			bestBid := ob.Bids.Peek()
			if o.Price <= bestBid.Price {
				// Match
				tradeQty := min(o.Quantity, bestBid.Quantity)
				trades = append(trades, Trade{
					BuyID:    bestBid.ID,
					SellID:   o.ID,
					Price:    bestBid.Price, // Seller accepts buyer's bid price
					Quantity: tradeQty,
				})

				o.Quantity -= tradeQty
				bestBid.Quantity -= tradeQty

				if bestBid.Quantity <= 0 {
					heap.Pop(ob.Bids)
				}
			} else {
				break
			}
		}
		if o.Quantity > 0 {
			heap.Push(ob.Asks, o)
		}
	}
	return trades
}

// Trade represents a successful match.
type Trade struct {
	BuyID    int     `json:"buy_id"`
	SellID   int     `json:"sell_id"`
	Price    float64 `json:"price"`
	Quantity float64 `json:"quantity"`
}

// Heap Implementation

type OrderHeap struct {
	orders []*Order
	isMin  bool // true for Asks (lowest price first), false for Bids (highest price first)
}

func (h OrderHeap) Len() int { return len(h.orders) }

func (h OrderHeap) Less(i, j int) bool {
	p1 := h.orders[i].Price
	p2 := h.orders[j].Price
	if p1 == p2 {
		return h.orders[i].Timestamp < h.orders[j].Timestamp // FIFO
	}
	if h.isMin {
		return p1 < p2
	}
	return p1 > p2
}

func (h OrderHeap) Swap(i, j int) {
	h.orders[i], h.orders[j] = h.orders[j], h.orders[i]
}

func (h *OrderHeap) Push(x interface{}) {
	h.orders = append(h.orders, x.(*Order))
}

func (h *OrderHeap) Pop() interface{} {
	old := h.orders
	n := len(old)
	x := old[n-1]
	h.orders = old[0 : n-1]
	return x
}

func (h *OrderHeap) Peek() *Order {
	return h.orders[0]
}

func min(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}
