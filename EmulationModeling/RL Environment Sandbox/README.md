# RL Environment Sandbox

A reinforcement learning environment sandbox implementing the OpenAI Gym interface (`reset`, `step`, `render`) for a GridWorld problem.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Demos](#demos)

## 🧠 Theory

### Markov Decision Process (MDP)
-   **State ($S$)**: The agent's position in the grid.
-   **Action ($A$)**: Up, Down, Left, Right.
-   **Reward ($R$)**: +1 for reaching the goal, -1 for pits, -0.01 per step (living cost).
-   **Transition ($P$)**: Deterministic movement (unless hitting a wall).

### Q-Learning (Demo)
The demo implements a Q-learning agent that updates its value estimates:
$$Q(s,a) \leftarrow Q(s,a) + \alpha [r + \gamma \max_{a'} Q(s', a') - Q(s,a)]$$

## 💻 Installation

Ensure you have a C++17 compatible compiler.

## 🚀 Usage

### Compiling and Running

```bash
g++ -std=c++17 -DRL_SANDBOX_DEMO main.cpp -o rl_env
./rl_env
```

### API
```cpp
GridWorld env(4, 4); // 4x4 grid
auto state = env.reset();
auto [next_state, reward, done] = env.step(Action::RIGHT);
```

## 📊 Complexity Analysis

-   **Step**: $O(1)$ state update.
-   **Learning**: $O(T)$ where $T$ is total steps. Convergence depends on state space size $|S| \times |A|$.

## 🎬 Demos

The demo trains an agent to find a path from Start (0,0) to Goal (3,3) avoiding obstacles, then visualizes the path taken.
