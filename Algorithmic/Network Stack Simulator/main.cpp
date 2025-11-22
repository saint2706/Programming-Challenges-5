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
    bool ack = false;
    std::string payload;
};

struct PendingFrame {
    Frame frame;
    double last_tx_time = 0.0;
    bool acknowledged = false;
};

// Selective-repeat ARQ over an unreliable channel (drops + reordering).
class ReliableTransport {
  public:
    ReliableTransport(double loss_rate = 0.0, double rtt_ms = 100.0, uint32_t window = 4)
        : rng(std::random_device{}()), loss_dist(0.0, 1.0), loss_rate(loss_rate),
          retransmit_timeout(rtt_ms / 1000.0 * 2), window_size(window), now_time(0.0) {}

    // Advance simulation time and emit any pending retransmissions.
    std::vector<Frame> tick(double dt_seconds) {
        now_time += dt_seconds;
        std::vector<Frame> to_send;
        for (auto &kv : in_flight) {
            auto &pending = kv.second;
            if (pending.acknowledged)
                continue;
            if (pending.last_tx_time + retransmit_timeout <= now_time) {
                pending.last_tx_time = now_time;
                to_send.push_back(pending.frame);
            }
        }
        return to_send;
    }

    // Queue a message if the window has space; otherwise return false.
    bool send(const std::string &message) {
        if (send_queue.size() + in_flight.size() >= window_size)
            return false;
        send_queue.push(message);
        return true;
    }

    // Called by application to drain new frames ready for the network.
    std::vector<Frame> flush_new_transmissions() {
        std::vector<Frame> frames;
        while (!send_queue.empty() && in_flight.size() < window_size) {
            Frame f{next_seq++, false, send_queue.front()};
            send_queue.pop();
            in_flight[f.seq] = PendingFrame{f, now_time, false};
            frames.push_back(f);
        }
        return frames;
    }

    // Deliver frames from the network. Produces newly completed messages and ACKs to send.
    std::pair<std::vector<std::string>, std::vector<Frame>> receive(const std::vector<Frame> &frames) {
        std::vector<std::string> delivered;
        std::vector<Frame> outgoing_acks;

        for (const auto &frame : frames) {
            if (loss_dist(rng) < loss_rate)
                continue;

            if (frame.ack) {
                auto it = in_flight.find(frame.seq);
                if (it != in_flight.end()) {
                    it->second.acknowledged = true;
                    completed_seqs.insert(frame.seq);
                }
                continue;
            }

            // Data frame
            if (frame.seq >= recv_base && received_buffer.find(frame.seq) == received_buffer.end()) {
                received_buffer[frame.seq] = frame.payload;
            }
            outgoing_acks.push_back(Frame{frame.seq, true, {}});

            // Deliver in-order messages.
            while (true) {
                auto it = received_buffer.find(recv_base);
                if (it == received_buffer.end())
                    break;
                delivered.push_back(it->second);
                received_buffer.erase(it);
                ++recv_base;
            }
        }

        // Remove acknowledged frames and slide window.
        for (auto it = in_flight.begin(); it != in_flight.end();) {
            if (it->second.acknowledged) {
                it = in_flight.erase(it);
            } else {
                ++it;
            }
        }

        return {delivered, outgoing_acks};
    }

    double now() const { return now_time; }
    uint32_t expected_sequence() const { return recv_base; }

  private:
    std::mt19937 rng;
    std::uniform_real_distribution<double> loss_dist;
    double loss_rate;
    double retransmit_timeout;
    uint32_t window_size;
    double now_time;

    uint32_t next_seq = 0;
    uint32_t recv_base = 0;
    std::queue<std::string> send_queue;
    std::map<uint32_t, PendingFrame> in_flight;
    std::map<uint32_t, std::string> received_buffer;
    std::set<uint32_t> completed_seqs;
};

#ifdef NETWORK_STACK_DEMO
int main() {
    ReliableTransport client(0.2);
    ReliableTransport server(0.0);

    for (const auto &msg : {"hello", "world", "!"}) {
        client.send(msg);
    }

    // Simulate a series of send/receive cycles.
    for (int step = 0; step < 10; ++step) {
        auto new_frames = client.flush_new_transmissions();
        auto retransmissions = client.tick(0.05);
        new_frames.insert(new_frames.end(), retransmissions.begin(), retransmissions.end());

        // shuffle to simulate reordering
        std::shuffle(new_frames.begin(), new_frames.end(), std::mt19937{42u + static_cast<uint32_t>(step)});

        auto [delivered, acks] = server.receive(new_frames);
        auto server_retx = server.tick(0.05);

        auto [client_delivered, client_acks] = client.receive(acks);
        client.flush_new_transmissions();
        if (!delivered.empty()) {
            for (const auto &msg : delivered)
                std::cout << "Server delivered: " << msg << "\n";
        }
        if (!client_delivered.empty()) {
            for (const auto &msg : client_delivered)
                std::cout << "Client delivered: " << msg << "\n";
        }
    }
}
#endif
