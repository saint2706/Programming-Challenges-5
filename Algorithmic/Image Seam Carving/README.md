# Image Seam Carving

## Theory
Seam carving (also known as liquid rescaling) is an algorithm for content-aware image resizing. Unlike standard scaling (which distorts content) or cropping (which removes content blindly), seam carving establishes a number of "seams" (paths of least importance) in an image and automatically removes the seam with the lowest energy.

The process involves:
1.  **Energy Map Calculation:** Compute the importance of each pixel. High energy (edges, texture) means high importance. We use the dual-gradient energy function: $E(x,y) = |\Delta x| + |\Delta y|$.
2.  **Accumulated Cost Matrix:** Use Dynamic Programming (DP) to find the path of minimum energy from top to bottom (for vertical seams).
    *   `dp[i][j] = energy[i][j] + min(dp[i-1][j-1], dp[i-1][j], dp[i-1][j+1])`
3.  **Seam Identification:** Backtrack from the bottom row to find the optimal seam.
4.  **Seam Removal:** Shift pixels to fill the gap left by the seam.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
Run the CLI to resize an image:

```bash
python main.py input.jpg output.jpg --width 400 --height 300
```

Or scale by a factor:
```bash
python main.py input.jpg output.jpg --scale 0.8
```

## Complexity Analysis
*   **Energy Calculation:** $O(W \times H)$
*   **Seam Finding:** $O(W \times H)$
*   **Seam Removal:** $O(W \times H)$
*   **Total for $k$ seams:** $O(k \times W \times H)$

Where $W$ is width and $H$ is height. This makes it computationally expensive for large images or large reduction factors.

## Demos
(Screenshots would go here)
