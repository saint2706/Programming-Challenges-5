#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>
#include <queue>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>
#include <stdexcept>

struct Node {
    int x, y;
    bool operator==(const Node &o) const { return x == o.x && y == o.y; }
};

struct NodeHash {
    size_t operator()(const Node &n) const { return std::hash<int>()(n.x * 73856093 ^ n.y * 19349663); }
};

class GridMap {
  public:
    GridMap(int w, int h) : width(w), height(h), obstacles(w * h, false) {}

    void add_obstacle(int x, int y) { obstacles[index(x, y)] = true; }
    bool is_free(int x, int y) const {
        return x >= 0 && x < width && y >= 0 && y < height && !obstacles[index(x, y)];
    }

    std::vector<Node> neighbors(const Node &n) const {
        static const int dx[] = {1, -1, 0, 0, 1, 1, -1, -1};
        static const int dy[] = {0, 0, 1, -1, 1, -1, 1, -1};
        std::vector<Node> result;
        for (int k = 0; k < 8; ++k) {
            int nx = n.x + dx[k];
            int ny = n.y + dy[k];
            if (is_free(nx, ny)) {
                result.push_back({nx, ny});
            }
        }
        return result;
    }

  private:
    int width, height;
    std::vector<bool> obstacles;

    int index(int x, int y) const { return y * width + x; }
};

class AStarPlanner {
  public:
    explicit AStarPlanner(const GridMap &map) : map(map) {}

    std::vector<Node> plan(const Node &start, const Node &goal) const {
        if (!map.is_free(start.x, start.y) || !map.is_free(goal.x, goal.y))
            throw std::invalid_argument("start or goal blocked");

        using Pair = std::pair<double, Node>;
        auto cmp = [](const Pair &a, const Pair &b) { return a.first > b.first; };
        std::priority_queue<Pair, std::vector<Pair>, decltype(cmp)> open(cmp);

        std::unordered_map<Node, Node, NodeHash> came_from;
        std::unordered_map<Node, double, NodeHash> g_score;
        g_score[start] = 0.0;
        open.emplace(heuristic(start, goal), start);

        std::unordered_set<Node, NodeHash> closed;

        while (!open.empty()) {
            Node current = open.top().second;
            if (current == goal) {
                return reconstruct_path(came_from, current);
            }
            open.pop();
            if (closed.count(current))
                continue;
            closed.insert(current);

            for (const auto &neighbor : map.neighbors(current)) {
                double step_cost = (neighbor.x != current.x && neighbor.y != current.y) ? std::sqrt(2.0) : 1.0;
                double tentative = g_score[current] + step_cost;
                if (!g_score.count(neighbor) || tentative < g_score[neighbor]) {
                    came_from[neighbor] = current;
                    g_score[neighbor] = tentative;
                    double f = tentative + heuristic(neighbor, goal);
                    open.emplace(f, neighbor);
                }
            }
        }
        return {};
    }

  private:
    const GridMap &map;

    static double heuristic(const Node &a, const Node &b) {
        // Octile distance
        int dx = std::abs(a.x - b.x);
        int dy = std::abs(a.y - b.y);
        return (dx + dy) + (std::sqrt(2.0) - 2) * std::min(dx, dy);
    }

    static std::vector<Node> reconstruct_path(const std::unordered_map<Node, Node, NodeHash> &came_from,
                                             Node current) {
        std::vector<Node> path;
        path.push_back(current);
        auto it = came_from.find(current);
        while (it != came_from.end()) {
            current = it->second;
            path.push_back(current);
            it = came_from.find(current);
        }
        std::reverse(path.begin(), path.end());
        return path;
    }
};

#ifdef WAREHOUSE_SIM_DEMO
int main() {
    GridMap map(10, 10);
    map.add_obstacle(4, 5);
    map.add_obstacle(4, 6);
    map.add_obstacle(5, 6);
    AStarPlanner planner(map);
    auto path = planner.plan({0, 0}, {7, 7});
    for (auto node : path) {
        std::cout << "(" << node.x << "," << node.y << ") ";
    }
    std::cout << "\n";
    return 0;
}
#endif
