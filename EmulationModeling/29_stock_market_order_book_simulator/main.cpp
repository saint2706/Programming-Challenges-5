#include <algorithm>
#include <iostream>
#include <map>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
#include <optional>

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
        validate(order);
        if (order.side == Side::BUY) {
            match_buy(order);
        } else {
            match_sell(order);
        }
    }

    void cancel(int order_id) {
        auto meta = index.find(order_id);
        if (meta == index.end())
            return; // silently ignore unknown ids
        auto [side, price] = meta->second;
        if (side == Side::BUY) {
            auto it = bids.find(price);
            if (it != bids.end()) {
                remove_from_queue(bids, it, order_id);
            }
        } else {
            auto it = asks.find(price);
            if (it != asks.end()) {
                remove_from_queue(asks, it, order_id);
            }
        }
    }

    template <typename MapType, typename IterType>
    void remove_from_queue(MapType &book, IterType it, int order_id) {
        auto &q = it->second;
        std::queue<Order> rebuilt;
        while (!q.empty()) {
            Order o = q.front();
            q.pop();
            if (o.id != order_id)
                rebuilt.push(o);
        }
        if (rebuilt.empty())
            book.erase(it);
        else
            it->second.swap(rebuilt);
        index.erase(order_id);
    }

    const std::vector<Trade> &trades() const { return executed; }

    std::optional<int> best_bid() const {
        if (bids.empty())
            return std::nullopt;
        return bids.begin()->first;
    }

    std::optional<int> best_ask() const {
        if (asks.empty())
            return std::nullopt;
        return asks.begin()->first;
    }

  private:
    // price -> quantity queue preserving time priority
    std::map<int, std::queue<Order>, std::greater<int>> bids;
    std::map<int, std::queue<Order>> asks;
    std::unordered_map<int, std::pair<Side, int>> index;
    std::vector<Trade> executed;

    void validate(const Order &o) {
        if (o.price <= 0 || o.quantity <= 0)
            throw std::invalid_argument("price and quantity must be positive");
    }

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
                index.erase(resting.id);
                queue.pop();
                if (queue.empty())
                    asks.erase(best_ask_it);
            }
        }
        if (incoming.quantity > 0) {
            bids[incoming.price].push(incoming);
            index[incoming.id] = {Side::BUY, incoming.price};
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
                index.erase(resting.id);
                queue.pop();
                if (queue.empty())
                    bids.erase(best_bid_it);
            }
        }
        if (incoming.quantity > 0) {
            asks[incoming.price].push(incoming);
            index[incoming.id] = {Side::SELL, incoming.price};
        }
    }
};

#ifdef ORDER_BOOK_DEMO
int main() {
    OrderBook book;
    book.add_order({1, Side::BUY, 100, 5});
    book.add_order({2, Side::SELL, 99, 2});
    book.add_order({3, Side::SELL, 100, 10});
    book.cancel(3);
    book.add_order({4, Side::SELL, 99, 4});

    for (const auto &trade : book.trades()) {
        std::cout << "Trade at " << trade.price << " qty " << trade.quantity << "\n";
    }
}
#endif
