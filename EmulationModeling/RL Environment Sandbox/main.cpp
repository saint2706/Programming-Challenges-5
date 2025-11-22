#include <iostream>
#include <random>
#include <stdexcept>
#include <unordered_set>
#include <vector>

enum Action { UP, DOWN, LEFT, RIGHT };

struct Transition {
    int state;
    double reward;
    bool done;
};

struct CellHash {
    size_t operator()(const std::pair<int, int> &p) const { return std::hash<int>()(p.first ^ (p.second << 16)); }
};

class GridWorld {
  public:
    GridWorld(int width, int height, int goal_x, int goal_y, double slip = 0.0)
        : w(width), h(height), goal{goal_x, goal_y}, rng(std::random_device{}()), slip_dist(0.0, 1.0), slip_prob(slip) {
        if (w <= 0 || h <= 0)
            throw std::invalid_argument("grid must be positive size");
        if (!in_bounds(goal_x, goal_y))
            throw std::invalid_argument("goal out of bounds");
        state = {0, 0};
    }

    void add_wall(int x, int y) { walls.insert({x, y}); }

    Transition step(Action action) {
        if (done_flag)
            return {state_index(), 0.0, true};

        Action applied = action;
        if (slip_dist(rng) < slip_prob) {
            applied = static_cast<Action>((action + 1) % 4); // deterministic sidestep on slip
        }

        auto next = state;
        switch (applied) {
        case UP:
            next.second -= 1;
            break;
        case DOWN:
            next.second += 1;
            break;
        case LEFT:
            next.first -= 1;
            break;
        case RIGHT:
            next.first += 1;
            break;
        }

        if (in_bounds(next.first, next.second) && !is_wall(next)) {
            state = next;
        }

        done_flag = state == goal;
        double reward = done_flag ? 1.0 : -0.02;
        return {state_index(), reward, done_flag};
    }

    Transition reset() {
        std::uniform_int_distribution<int> dist_x(0, w - 1);
        std::uniform_int_distribution<int> dist_y(0, h - 1);
        do {
            state = {dist_x(rng), dist_y(rng)};
        } while (is_wall(state) || state == goal);
        done_flag = false;
        return {state_index(), 0.0, false};
    }

    int observation_space() const { return w * h; }
    int action_space() const { return 4; }

    void render_ascii() const {
        for (int y = 0; y < h; ++y) {
            for (int x = 0; x < w; ++x) {
                if (std::make_pair(x, y) == state)
                    std::cout << 'A';
                else if (std::make_pair(x, y) == goal)
                    std::cout << 'G';
                else if (is_wall({x, y}))
                    std::cout << '#';
                else
                    std::cout << '.';
            }
            std::cout << '\n';
        }
        std::cout << "----\n";
    }

  private:
    int w, h;
    std::pair<int, int> goal;
    std::pair<int, int> state;
    bool done_flag = false;
    std::unordered_set<std::pair<int, int>, CellHash> walls;
    std::mt19937 rng;
    std::uniform_real_distribution<double> slip_dist;
    double slip_prob;

    int state_index() const { return state.second * w + state.first; }
    bool in_bounds(int x, int y) const { return x >= 0 && x < w && y >= 0 && y < h; }
    bool is_wall(const std::pair<int, int> &p) const { return walls.count(p) > 0; }
};

#ifdef RL_SANDBOX_DEMO
int main() {
    GridWorld env(5, 5, 4, 4, 0.1);
    env.add_wall(2, 2);
    auto t = env.reset();
    int steps = 0;
    while (!t.done && steps < 30) {
        t = env.step(static_cast<Action>(steps % 4));
        env.render_ascii();
        ++steps;
    }
}
#endif
