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

struct Packet {
    std::string id;
    std::string payload;
};

struct ScheduledPacket {
    double delivery_time; // seconds since simulation start
    Packet packet;

    bool operator<(const ScheduledPacket &other) const {
        // priority_queue is max-first; invert to deliver earliest first
        return delivery_time > other.delivery_time;
    }
};

class LagSimulator {
  public:
    LagSimulator(double base_latency_ms, double jitter_ms, double drop_rate)
        : base_latency(base_latency_ms / 1000.0), jitter(jitter_ms / 1000.0),
          drop_probability(drop_rate), current_time(0.0), rng(std::random_device{}()),
          jitter_dist(-this->jitter, this->jitter), drop_dist(0.0, 1.0) {}

    void tick(double dt_seconds) { current_time += dt_seconds; }

    void send(const Packet &packet) {
        if (drop_dist(rng) < drop_probability) {
            dropped.push_back(packet);
            return;
        }

        double latency = base_latency + jitter_dist(rng);
        latency = std::max(0.0, latency);
        scheduled.push(ScheduledPacket{current_time + latency, packet});
    }

    std::vector<Packet> receive_ready() {
        std::vector<Packet> delivered;
        while (!scheduled.empty() && scheduled.top().delivery_time <= current_time) {
            delivered.push_back(scheduled.top().packet);
            scheduled.pop();
        }
        return delivered;
    }

    const std::vector<Packet> &dropped_packets() const { return dropped; }

  private:
    double base_latency;
    double jitter;
    double drop_probability;
    double current_time;

    std::priority_queue<ScheduledPacket> scheduled;
    std::vector<Packet> dropped;

    std::mt19937 rng;
    std::uniform_real_distribution<double> jitter_dist;
    std::uniform_real_distribution<double> drop_dist;
};

#ifdef LAG_SIMULATOR_DEMO
int main() {
    LagSimulator simulator(80, 20, 0.1);
    simulator.send({"p1", "hello"});
    simulator.tick(0.05);
    simulator.send({"p2", "world"});

    for (int i = 0; i < 10; ++i) {
        simulator.tick(0.02);
        for (const auto &pkt : simulator.receive_ready()) {
            std::cout << "Delivered " << pkt.id << " -> " << pkt.payload << "\n";
        }
    }

    std::cout << "Dropped: " << simulator.dropped_packets().size() << " packets\n";
    return 0;
}
#endif
