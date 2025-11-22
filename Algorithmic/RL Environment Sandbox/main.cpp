#include <iostream>
#include <random>
#include <vector>

enum Action { UP, DOWN, LEFT, RIGHT };

struct Transition {
    int state;
    double reward;
    bool done;
};

class GridWorld {
  public:
    GridWorld(int width, int height, int goal_x, int goal_y)
        : w(width), h(height), goal{goal_x, goal_y}, state{0, 0}, rng(std::random_device{}()) {}

    Transition step(Action action) {
        switch (action) {
        case UP:
            state.second = std::max(0, state.second - 1);
            break;
        case DOWN:
            state.second = std::min(h - 1, state.second + 1);
            break;
        case LEFT:
            state.first = std::max(0, state.first - 1);
            break;
        case RIGHT:
            state.first = std::min(w - 1, state.first + 1);
            break;
        }

        bool done = state == goal;
        double reward = done ? 1.0 : -0.01;
        return {state_index(), reward, done};
    }

    Transition reset() {
        std::uniform_int_distribution<int> dist_x(0, w - 1);
        std::uniform_int_distribution<int> dist_y(0, h - 1);
        state = {dist_x(rng), dist_y(rng)};
        return {state_index(), 0.0, state == goal};
    }

    int observation_space() const { return w * h; }
    int action_space() const { return 4; }

  private:
    int w, h;
    std::pair<int, int> goal;
    std::pair<int, int> state;
    std::mt19937 rng;

    int state_index() const { return state.second * w + state.first; }
};

#ifdef RL_SANDBOX_DEMO
int main() {
    GridWorld env(5, 5, 4, 4);
    auto t = env.reset();
    int steps = 0;
    while (!t.done && steps < 20) {
        t = env.step(static_cast<Action>(steps % 4));
        std::cout << "State: " << t.state << " reward: " << t.reward << " done: " << t.done << "\n";
        ++steps;
    }
}
#endif
