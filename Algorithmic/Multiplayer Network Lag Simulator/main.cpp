#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <functional>
#include <iostream>
#include <optional>
#include <queue>
#include <random>
#include <string>
#include <tuple>
#include <vector>
#include <stdexcept>

struct Packet {
    std::string id;
    std::string payload;
};

struct ScheduledPacket {
    double delivery_time; // seconds since simulation start
    Packet packet;
    bool operator<(const ScheduledPacket &other) const { return delivery_time > other.delivery_time; }
};

class LagSimulator {
  public:
    LagSimulator(double base_latency_ms, double jitter_ms, double drop_rate, double duplicate_rate = 0.0,
                 size_t capacity = 1024, uint64_t seed = std::random_device{}())
        : base_latency(base_latency_ms / 1000.0), jitter(jitter_ms / 1000.0), drop_probability(drop_rate),
          duplicate_probability(duplicate_rate), max_inflight(capacity), current_time(0.0), rng(seed),
          jitter_dist(-this->jitter, this->jitter), drop_dist(0.0, 1.0) {}

    void tick(double dt_seconds) {
        if (dt_seconds < 0)
            throw std::invalid_argument("dt must be non-negative");
        current_time += dt_seconds;
    }

    bool send(const Packet &packet) {
        if (scheduled.size() >= max_inflight)
            return false;

        if (drop_dist(rng) < drop_probability) {
            dropped.push_back(packet);
            return true;
        }

        double latency = base_latency + jitter_dist(rng);
        latency = std::max(0.0, latency);
        scheduled.push(ScheduledPacket{current_time + latency, packet});
        if (drop_dist(rng) < duplicate_probability) {
            scheduled.push(ScheduledPacket{current_time + latency * 1.1, packet});
        }
        return true;
    }

    std::vector<Packet> receive_ready(size_t burst_limit = 32) {
        std::vector<Packet> delivered;
        while (!scheduled.empty() && scheduled.top().delivery_time <= current_time && delivered.size() < burst_limit) {
            delivered.push_back(scheduled.top().packet);
            scheduled.pop();
        }
        return delivered;
    }

    const std::vector<Packet> &dropped_packets() const { return dropped; }
    double now() const { return current_time; }

  private:
    double base_latency;
    double jitter;
    double drop_probability;
    double duplicate_probability;
    size_t max_inflight;
    double current_time;

    std::priority_queue<ScheduledPacket> scheduled;
    std::vector<Packet> dropped;

    std::mt19937 rng;
    std::uniform_real_distribution<double> jitter_dist;
    std::uniform_real_distribution<double> drop_dist;
};

#ifdef LAG_SIMULATOR_DEMO
int main() {
    LagSimulator simulator(80, 20, 0.1, 0.05, 64, 1234);
    simulator.send({"p1", "hello"});
    simulator.tick(0.05);
    simulator.send({"p2", "world"});

    for (int i = 0; i < 20; ++i) {
        simulator.tick(0.02);
        for (const auto &pkt : simulator.receive_ready()) {
            std::cout << "Delivered " << pkt.id << " -> " << pkt.payload << " at t=" << simulator.now() << "\n";
        }
    }

    std::cout << "Dropped: " << simulator.dropped_packets().size() << " packets\n";
    return 0;
}
#endif
