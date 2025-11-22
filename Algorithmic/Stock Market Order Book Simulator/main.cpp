#include <algorithm>
#include <iostream>
#include <map>
#include <queue>
#include <string>
#include <vector>

enum class Side { BUY, SELL };

struct Order {
    int id;
    Side side;
    int price;
    int quantity;
};

struct Trade {
    int buy_id;
    int sell_id;
    int price;
    int quantity;
};

class OrderBook {
  public:
    void add_order(const Order &order) {
        if (order.side == Side::BUY) {
            match_buy(order);
        } else {
            match_sell(order);
        }
    }

    const std::vector<Trade> &trades() const { return executed; }

  private:
    // price -> quantity queue preserving time priority
    std::map<int, std::queue<Order>, std::greater<int>> bids;
    std::map<int, std::queue<Order>> asks;
    std::vector<Trade> executed;

    void match_buy(Order incoming) {
        while (incoming.quantity > 0 && !asks.empty()) {
            auto best_ask_it = asks.begin();
            if (best_ask_it->first > incoming.price)
                break;
            auto &queue = best_ask_it->second;
            Order &resting = queue.front();
            int qty = std::min(incoming.quantity, resting.quantity);
            executed.push_back({incoming.id, resting.id, best_ask_it->first, qty});
            incoming.quantity -= qty;
            resting.quantity -= qty;
            if (resting.quantity == 0) {
                queue.pop();
                if (queue.empty())
                    asks.erase(best_ask_it);
            }
        }
        if (incoming.quantity > 0) {
            bids[incoming.price].push(incoming);
        }
    }

    void match_sell(Order incoming) {
        while (incoming.quantity > 0 && !bids.empty()) {
            auto best_bid_it = bids.begin();
            if (best_bid_it->first < incoming.price)
                break;
            auto &queue = best_bid_it->second;
            Order &resting = queue.front();
            int qty = std::min(incoming.quantity, resting.quantity);
            executed.push_back({resting.id, incoming.id, best_bid_it->first, qty});
            incoming.quantity -= qty;
            resting.quantity -= qty;
            if (resting.quantity == 0) {
                queue.pop();
                if (queue.empty())
                    bids.erase(best_bid_it);
            }
        }
        if (incoming.quantity > 0) {
            asks[incoming.price].push(incoming);
        }
    }
};

#ifdef ORDER_BOOK_DEMO
int main() {
    OrderBook book;
    book.add_order({1, Side::BUY, 100, 5});
    book.add_order({2, Side::SELL, 99, 2});
    book.add_order({3, Side::SELL, 100, 10});

    for (const auto &trade : book.trades()) {
        std::cout << "Trade at " << trade.price << " qty " << trade.quantity << "\n";
    }
}
#endif
