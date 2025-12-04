"""Matching Engine (Order Book).

Implements a limit order book using two heaps (buy/sell).
"""

import heapq
from typing import List, Tuple

class MatchingEngine:
    def __init__(self):
        # Bids (Buy): Max-heap (-price, counter, quantity, id)
        self.bids: List[Tuple[float, int, int, int]] = []
        # Asks (Sell): Min-heap (price, counter, quantity, id)
        self.asks: List[Tuple[float, int, int, int]] = []
        self.id_counter = 0

    def place_limit_order(self, side: str, price: float, quantity: int):
        self.id_counter += 1
        oid = self.id_counter

        if side == 'buy':
            # Check asks (lowest sell price first)
            while quantity > 0 and self.asks and self.asks[0][0] <= price:
                ask_price, _, ask_qty, ask_id = self.asks[0]
                matched = min(quantity, ask_qty)
                quantity -= matched
                # Update ask
                if matched == ask_qty:
                    heapq.heappop(self.asks)
                else:
                    # Partial match: update quantity in heap
                    # Tuples are immutable, so we replace the root
                    new_ask = (ask_price, self.asks[0][1], ask_qty - matched, ask_id)
                    heapq.heapreplace(self.asks, new_ask)

            if quantity > 0:
                # Push to bids (-price for max-heap)
                heapq.heappush(self.bids, (-price, oid, quantity, oid))

        else: # Sell
            # Check bids (highest buy price first, which is smallest negative)
            while quantity > 0 and self.bids and -self.bids[0][0] >= price:
                bid_neg_price, _, bid_qty, bid_id = self.bids[0]
                matched = min(quantity, bid_qty)
                quantity -= matched

                if matched == bid_qty:
                    heapq.heappop(self.bids)
                else:
                    new_bid = (bid_neg_price, self.bids[0][1], bid_qty - matched, bid_id)
                    heapq.heapreplace(self.bids, new_bid)

            if quantity > 0:
                heapq.heappush(self.asks, (price, oid, quantity, oid))

        return oid
