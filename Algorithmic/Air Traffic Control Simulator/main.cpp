#include <cmath>
#include <iostream>
#include <optional>
#include <string>
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
};

class AirTrafficSimulator {
  public:
    AirTrafficSimulator(double separation_km, double lookahead_min)
        : separation(separation_km), lookahead(lookahead_min) {}

    void add_aircraft(const Aircraft &a) { aircraft.push_back(a); }

    std::vector<Conflict> detect_conflicts() const {
        std::vector<Conflict> conflicts;
        for (size_t i = 0; i < aircraft.size(); ++i) {
            for (size_t j = i + 1; j < aircraft.size(); ++j) {
                auto time = time_to_violation(aircraft[i], aircraft[j]);
                if (time && *time <= lookahead) {
                    conflicts.push_back({aircraft[i].id, aircraft[j].id, *time});
                }
            }
        }
        return conflicts;
    }

  private:
    double separation;
    double lookahead;
    std::vector<Aircraft> aircraft;

    static std::optional<double> time_to_violation(const Aircraft &a, const Aircraft &b) {
        double dx = a.x - b.x;
        double dy = a.y - b.y;
        double dz = a.z - b.z;
        double dvx = a.vx - b.vx;
        double dvy = a.vy - b.vy;
        double dvz = a.vz - b.vz;

        double a_coeff = dvx * dvx + dvy * dvy + dvz * dvz;
        double b_coeff = 2 * (dx * dvx + dy * dvy + dz * dvz);
        double c_coeff = dx * dx + dy * dy + dz * dz - separation * separation;

        if (a_coeff == 0) {
            if (c_coeff <= 0)
                return 0.0;
            return std::nullopt;
        }

        double discriminant = b_coeff * b_coeff - 4 * a_coeff * c_coeff;
        if (discriminant < 0)
            return std::nullopt;

        double sqrt_disc = std::sqrt(discriminant);
        double t1 = (-b_coeff - sqrt_disc) / (2 * a_coeff);
        double t2 = (-b_coeff + sqrt_disc) / (2 * a_coeff);

        if (t2 < 0)
            return std::nullopt;
        double entry = t1 >= 0 ? t1 : 0.0;
        return entry;
    }
};

#ifdef ATC_SIM_DEMO
int main() {
    AirTrafficSimulator sim(5.0, 30.0);
    sim.add_aircraft({"A1", 0, 0, 10, 10, 0, 0});
    sim.add_aircraft({"A2", 50, 0, 10, -8, 0, 0});

    auto conflicts = sim.detect_conflicts();
    for (const auto &c : conflicts) {
        std::cout << "Conflict between " << c.id1 << " and " << c.id2 << " in " << c.time_to_conflict
                  << " minutes\n";
    }
}
#endif
