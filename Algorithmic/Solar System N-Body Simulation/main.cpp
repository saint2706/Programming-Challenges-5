#include <cmath>
#include <iostream>
#include <string>
#include <vector>
#include <stdexcept>

struct Vec3 {
    double x, y, z;
    Vec3 operator+(const Vec3 &other) const { return {x + other.x, y + other.y, z + other.z}; }
    Vec3 operator-(const Vec3 &other) const { return {x - other.x, y - other.y, z - other.z}; }
    Vec3 operator*(double s) const { return {x * s, y * s, z * s}; }
    Vec3 &operator+=(const Vec3 &other) {
        x += other.x;
        y += other.y;
        z += other.z;
        return *this;
    }
};

struct Body {
    std::string name;
    double mass;
    Vec3 position;
    Vec3 velocity;
};

class NBodySimulation {
  public:
    explicit NBodySimulation(double g = 6.67430e-11) : G(g) {}

    void add_body(const Body &body) {
        if (body.mass <= 0)
            throw std::invalid_argument("mass must be positive");
        bodies.push_back(body);
    }

    // Leapfrog integrator for better energy conservation than simple Euler.
    void step(double dt) {
        if (dt <= 0)
            throw std::invalid_argument("dt must be positive");
        std::vector<Vec3> accelerations = compute_accelerations();
        for (size_t i = 0; i < bodies.size(); ++i) {
            bodies[i].velocity += accelerations[i] * (dt / 2.0);
            bodies[i].position += bodies[i].velocity * dt;
        }
        auto accel_after = compute_accelerations();
        for (size_t i = 0; i < bodies.size(); ++i) {
            bodies[i].velocity += accel_after[i] * (dt / 2.0);
        }
    }

    double total_energy() const {
        double kinetic = 0.0;
        double potential = 0.0;
        for (size_t i = 0; i < bodies.size(); ++i) {
            const auto &bi = bodies[i];
            kinetic += 0.5 * bi.mass * (bi.velocity.x * bi.velocity.x + bi.velocity.y * bi.velocity.y +
                                        bi.velocity.z * bi.velocity.z);
            for (size_t j = i + 1; j < bodies.size(); ++j) {
                const auto &bj = bodies[j];
                Vec3 diff = bj.position - bi.position;
                double dist = std::sqrt(diff.x * diff.x + diff.y * diff.y + diff.z * diff.z + softening);
                potential -= G * bi.mass * bj.mass / dist;
            }
        }
        return kinetic + potential;
    }

    const std::vector<Body> &state() const { return bodies; }

  private:
    double G;
    double softening = 1e-6; // prevents singularities
    std::vector<Body> bodies;

    std::vector<Vec3> compute_accelerations() const {
        std::vector<Vec3> accelerations(bodies.size(), {0, 0, 0});
        for (size_t i = 0; i < bodies.size(); ++i) {
            for (size_t j = i + 1; j < bodies.size(); ++j) {
                Vec3 diff = bodies[j].position - bodies[i].position;
                double dist_sq = diff.x * diff.x + diff.y * diff.y + diff.z * diff.z + softening;
                double inv_dist = 1.0 / std::sqrt(dist_sq);
                double inv_dist3 = inv_dist * inv_dist * inv_dist;
                Vec3 force = diff * (G * bodies[i].mass * bodies[j].mass * inv_dist3);
                accelerations[i] += force * (1.0 / bodies[i].mass);
                accelerations[j] += force * (-1.0 / bodies[j].mass);
            }
        }
        return accelerations;
    }
};

#ifdef NBODY_DEMO
int main() {
    NBodySimulation sim(1.0); // scaled gravitational constant for demo
    sim.add_body({"Sun", 1000, {0, 0, 0}, {0, 0, 0}});
    sim.add_body({"Earth", 1, {1, 0, 0}, {0, 10, 0}});

    for (int i = 0; i < 5; ++i) {
        sim.step(0.01);
        std::cout << "Energy: " << sim.total_energy() << "\n";
        for (const auto &body : sim.state()) {
            std::cout << body.name << " pos: " << body.position.x << ", " << body.position.y << "\n";
        }
        std::cout << "---\n";
    }
}
#endif
