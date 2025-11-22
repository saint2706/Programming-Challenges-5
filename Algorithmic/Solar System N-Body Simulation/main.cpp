#include <cmath>
#include <iostream>
#include <string>
#include <vector>

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

    void add_body(const Body &body) { bodies.push_back(body); }

    void step(double dt) {
        std::vector<Vec3> accelerations(bodies.size(), {0, 0, 0});
        for (size_t i = 0; i < bodies.size(); ++i) {
            for (size_t j = i + 1; j < bodies.size(); ++j) {
                Vec3 diff = bodies[j].position - bodies[i].position;
                double dist_sq = diff.x * diff.x + diff.y * diff.y + diff.z * diff.z + 1e-9;
                double dist = std::sqrt(dist_sq);
                double force = G * bodies[i].mass * bodies[j].mass / dist_sq;
                Vec3 dir = diff * (1.0 / dist);
                Vec3 acc_i = dir * (force / bodies[i].mass);
                Vec3 acc_j = dir * (-force / bodies[j].mass);
                accelerations[i] += acc_i;
                accelerations[j] += acc_j;
            }
        }

        for (size_t i = 0; i < bodies.size(); ++i) {
            bodies[i].velocity += accelerations[i] * dt;
            bodies[i].position += bodies[i].velocity * dt;
        }
    }

    const std::vector<Body> &state() const { return bodies; }

  private:
    double G;
    std::vector<Body> bodies;
};

#ifdef NBODY_DEMO
int main() {
    NBodySimulation sim(1.0); // scaled gravitational constant for demo
    sim.add_body({"Sun", 1000, {0, 0, 0}, {0, 0, 0}});
    sim.add_body({"Earth", 1, {1, 0, 0}, {0, 10, 0}});

    for (int i = 0; i < 5; ++i) {
        sim.step(0.01);
        for (const auto &body : sim.state()) {
            std::cout << body.name << " pos: " << body.position.x << ", " << body.position.y
                      << "\n";
        }
        std::cout << "---\n";
    }
}
#endif
