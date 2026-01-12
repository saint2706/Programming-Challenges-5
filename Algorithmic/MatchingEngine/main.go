package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

type Command struct {
	Type     string  `json:"type"` // "limit"
	Side     string  `json:"side"` // "buy", "sell"
	Price    float64 `json:"price"`
	Quantity float64 `json:"quantity"`
	OrderID  int     `json:"id"`
}

type Output struct {
	Trades []Trade `json:"trades"`
}

func main() {
	inputData, err := io.ReadAll(os.Stdin)
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to read stdin: %v\n", err)
		os.Exit(1)
	}

	var commands []Command
	if len(inputData) > 0 {
		if err := json.Unmarshal(inputData, &commands); err != nil {
			fmt.Fprintf(os.Stderr, "failed to parse input JSON: %v\n", err)
			os.Exit(1)
		}
	}

	ob := NewOrderBook()
	results := []Output{}

	// Simulated clock counter
	var counter int64 = 0

	for _, cmd := range commands {
		counter++
		var oType OrderType
		if cmd.Side == "buy" {
			oType = Buy
		} else {
			oType = Sell
		}

		order := &Order{
			ID:        cmd.OrderID,
			Type:      oType,
			Price:     cmd.Price,
			Quantity:  cmd.Quantity,
			Timestamp: counter,
		}

		trades := ob.AddOrder(order)
		results = append(results, Output{Trades: trades})
	}

	outBytes, _ := json.MarshalIndent(results, "", "  ")
	fmt.Println(string(outBytes))
}
