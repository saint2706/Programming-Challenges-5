#include <algorithm>
#include <cstdint>
#include <iostream>
#include <map>
#include <optional>
#include <queue>
#include <random>
#include <set>
#include <string>
#include <unordered_map>
#include <vector>

struct Frame {
    uint32_t seq;
    std::string payload;
};

class ReliableTransport {
  public:
    ReliableTransport(double loss_rate = 0.0)
        : rng(std::random_device{}()), loss_dist(0.0, 1.0), loss_rate(loss_rate),
          next_seq(0), expected_seq(0) {}

    // Simulate sending frames over an unreliable network (loss + reordering).
    std::vector<Frame> send(const std::string &message) {
        Frame frame{next_seq++, message};
        if (loss_dist(rng) < loss_rate) {
            return {};
        }
        outbound.push(frame);
        std::vector<Frame> transmitted;
        while (!outbound.empty()) {
            transmitted.push_back(outbound.front());
            outbound.pop();
        }
        return transmitted;
    }

    // Deliver frames to the receiver and return any newly completed messages.
    std::vector<std::string> receive(const std::vector<Frame> &frames) {
        for (const auto &frame : frames) {
            if (loss_dist(rng) < loss_rate)
                continue;
            if (frame.seq >= expected_seq) {
                buffer[frame.seq] = frame.payload;
            }
        }

        std::vector<std::string> delivered;
        while (true) {
            auto it = buffer.find(expected_seq);
            if (it == buffer.end())
                break;
            delivered.push_back(it->second);
            buffer.erase(it);
            ++expected_seq;
        }
        return delivered;
    }

  private:
    std::mt19937 rng;
    std::uniform_real_distribution<double> loss_dist;
    double loss_rate;

    uint32_t next_seq;
    uint32_t expected_seq;
    std::queue<Frame> outbound;
    std::map<uint32_t, std::string> buffer;
};

#ifdef NETWORK_STACK_DEMO
int main() {
    ReliableTransport client(0.2);
    ReliableTransport server(0.0);

    // Client sends three messages; the simulator may drop some.
    std::vector<Frame> wire;
    for (std::string msg : {"hello", "world", "!"}) {
        auto frames = client.send(msg);
        wire.insert(wire.end(), frames.begin(), frames.end());
    }

    // Shuffle to simulate reordering.
    std::shuffle(wire.begin(), wire.end(), std::mt19937{std::random_device{}()});

    auto delivered = server.receive(wire);
    for (auto &msg : delivered) {
        std::cout << "Delivered: " << msg << "\n";
    }
    return 0;
}
#endif
