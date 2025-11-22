#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

struct Aircraft {
    std::string id;
    double x, y, z;      // position in km
    double vx, vy, vz;   // velocity in km/min
};

struct Conflict {
    std::string id1;
    std::string id2;
    double time_to_conflict; // minutes until predicted conflict
    double predicted_miss;   // km separation at point of closest approach
};

class AirTrafficSimulator {
  public:
    AirTrafficSimulator(double lateral_separation_km, double vertical_separation_km, double lookahead_min)
        : lateral_sep(lateral_separation_km), vertical_sep(vertical_separation_km), lookahead(lookahead_min) {
        if (lateral_sep <= 0 || vertical_sep <= 0 || lookahead <= 0) {
            throw std::invalid_argument("Separation and lookahead must be positive");
        }
    }

    void add_aircraft(const Aircraft &a) { fleet[a.id] = a; }

    void remove_aircraft(const std::string &id) { fleet.erase(id); }

    void step(double minutes) {
        if (minutes < 0)
            throw std::invalid_argument("Simulation step must be non-negative");
        for (auto &[_, a] : fleet) {
            a.x += a.vx * minutes;
            a.y += a.vy * minutes;
            a.z += a.vz * minutes;
        }
    }

    std::vector<Conflict> detect_conflicts() const {
        std::vector<Conflict> conflicts;
        std::vector<std::string> ids;
        ids.reserve(fleet.size());
        for (const auto &[id, _] : fleet)
            ids.push_back(id);

        for (size_t i = 0; i < ids.size(); ++i) {
            for (size_t j = i + 1; j < ids.size(); ++j) {
                const auto &a = fleet.at(ids[i]);
                const auto &b = fleet.at(ids[j]);
                auto entry = time_to_violation(a, b);
                if (entry)
                    conflicts.push_back({a.id, b.id, entry->first, entry->second});
            }
        }
        std::sort(conflicts.begin(), conflicts.end(), [](const Conflict &lhs, const Conflict &rhs) {
            if (lhs.time_to_conflict == rhs.time_to_conflict)
                return lhs.predicted_miss < rhs.predicted_miss;
            return lhs.time_to_conflict < rhs.time_to_conflict;
        });
        return conflicts;
    }

  private:
    double lateral_sep;
    double vertical_sep;
    double lookahead;
    std::unordered_map<std::string, Aircraft> fleet;

    static double horiz_dist(double x1, double y1, double x2, double y2) {
        const double dx = x1 - x2;
        const double dy = y1 - y2;
        return std::sqrt(dx * dx + dy * dy);
    }

    std::optional<std::pair<double, double>> time_to_violation(const Aircraft &a, const Aircraft &b) const {
        // relative vectors
        double dx = a.x - b.x;
        double dy = a.y - b.y;
        double dz = a.z - b.z;
        double dvx = a.vx - b.vx;
        double dvy = a.vy - b.vy;
        double dvz = a.vz - b.vz;

        // Handle the static-relative case early.
        const double horiz_now = horiz_dist(a.x, a.y, b.x, b.y);
        const double vert_now = std::abs(dz);
        if (horiz_now <= lateral_sep && vert_now <= vertical_sep) {
            return std::make_pair(0.0, std::max(horiz_now, vert_now));
        }

        const double a_coeff = dvx * dvx + dvy * dvy + dvz * dvz;
        const double b_coeff = 2.0 * (dx * dvx + dy * dvy + dz * dvz);
        const double c_coeff = dx * dx + dy * dy + dz * dz;

        double t_star = 0.0;
        if (a_coeff > 1e-9) {
            t_star = -b_coeff / (2.0 * a_coeff);
            if (t_star < 0.0)
                t_star = 0.0;
        }

        // Evaluate separation at closest approach within lookahead.
        const double t_eval = std::min(t_star, lookahead);
        const double future_x = dx + dvx * t_eval;
        const double future_y = dy + dvy * t_eval;
        const double future_z = dz + dvz * t_eval;
        const double horiz_future = std::sqrt(future_x * future_x + future_y * future_y);
        const double vert_future = std::abs(future_z);

        const double miss_distance = std::max(horiz_future - lateral_sep, vert_future - vertical_sep);
        if (horiz_future <= lateral_sep && vert_future <= vertical_sep && t_eval <= lookahead) {
            return std::make_pair(t_eval, std::max(0.0, miss_distance));
        }

        // Also consider entry/exit times using quadratic for the horizontal component only.
        const double a_xy = dvx * dvx + dvy * dvy;
        const double b_xy = 2.0 * (dx * dvx + dy * dvy);
        const double c_xy = dx * dx + dy * dy - lateral_sep * lateral_sep;

        double earliest = std::numeric_limits<double>::infinity();
        if (a_xy > 1e-9) {
            const double disc = b_xy * b_xy - 4 * a_xy * c_xy;
            if (disc >= 0) {
                const double sqrt_disc = std::sqrt(disc);
                const double t1 = (-b_xy - sqrt_disc) / (2 * a_xy);
                const double t2 = (-b_xy + sqrt_disc) / (2 * a_xy);
                if (t2 >= 0) {
                    earliest = std::max(0.0, t1);
                }
            }
        }

        if (earliest <= lookahead) {
            // Check vertical separation at the same instant; if already within vertical we keep it.
            const double vz_at = std::abs(dz + dvz * earliest);
            if (vz_at <= vertical_sep) {
                const double horiz_at = horiz_dist(a.x + a.vx * earliest, a.y + a.vy * earliest,
                                                   b.x + b.vx * earliest, b.y + b.vy * earliest);
                if (horiz_at <= lateral_sep)
                    return std::make_pair(earliest, std::max(horiz_at - lateral_sep, vz_at - vertical_sep));
            }
        }
        return std::nullopt;
    }
};

#ifdef ATC_SIM_DEMO
int main() {
    AirTrafficSimulator sim(5.0, 0.3, 45.0);
    sim.add_aircraft({"A1", 0, 0, 10, 12, 0, 0});
    sim.add_aircraft({"A2", 60, 0, 10.2, -10, 0, 0});
    sim.add_aircraft({"A3", 30, 10, 11, -4, -0.1, 0});

    auto conflicts = sim.detect_conflicts();
    for (const auto &c : conflicts) {
        std::cout << "Conflict between " << c.id1 << " and " << c.id2 << " in " << c.time_to_conflict
                  << " minutes (miss: " << c.predicted_miss << " km)\n";
    }
}
#endif
