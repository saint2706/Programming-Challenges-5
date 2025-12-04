# Neural Cellular Automata

Implementation of a Neural Cellular Automata (NCA) using PyTorch.

## How to Run

```bash
python EmulationModeling/50_neural_cellular_automata/main.py
```

## Logic

1.  **State**: Grid of cells with $C$ channels (RGBA + hidden).
2.  **Update Rule**: A Convolutional Neural Network (CNN) is applied to every cell.
    *   **Perception**: Sobel filters measure local gradients.
    *   **Logic**: 1x1 Convolutions (Dense layers per pixel) update the state.
    *   **Stochasticity**: Updates are applied randomly to emulate asynchronous behavior.
3.  **Visualization**: The first 3 channels are interpreted as RGB colors.

> Note: This simulation runs with random weights, producing abstract patterns. To generate specific shapes, the network would need to be trained via gradient descent to minimize difference from a target image.
