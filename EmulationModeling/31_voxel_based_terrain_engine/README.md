# Voxel-based Terrain Engine

A compact C++ voxel terrain prototype featuring chunk-based world generation, greedy meshing, frustum culling, and multithreaded mesh builds.

## 📋 Table of Contents
- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Complexity Analysis](#complexity-analysis)
- [Notes](#notes)

## 🧠 Theory

### Terrain Generation
- **Perlin Noise Heightmap**: 2D Perlin noise (two octaves) generates smooth heights. Heights are clamped to the chunk's vertical span.
- **Chunk Grid**: The world is divided into fixed-size chunks (16×16×16). Each chunk stores a dense voxel array and a mesh built from visible faces.

### Greedy Meshing
- For each axis, a 2D mask compares opposite voxel faces in adjacent slices.
- Rectangles of identical, visible faces are merged into a single quad, drastically reducing draw calls versus naive cube-per-voxel rendering.

### Visibility & Culling
- **Frustum Culling**: Each chunk is bounded by an AABB. The frustum test rejects chunks fully outside the view volume before issuing draw calls.
- **Chunk Updates**: Only meshes for generated/dirty chunks are rebuilt; static chunks simply reuse their cached quad buffers.

### Parallel Mesh Builds
- Chunk generation + meshing runs with `std::async` to leverage multiple cores. This keeps frame-time stable while the main thread renders already-built chunks.

## 💻 Installation

Requires a C++20-compatible compiler (e.g., `g++`, `clang++`). No external libraries are needed for the demo.

## 🚀 Usage

### Build and Run
```bash
g++ -std=c++20 -O2 -pthread main.cpp -o voxel_demo
./voxel_demo
```
The demo prints chunk mesh statistics after culling. Integrate `Quad` buffers with your preferred renderer (e.g., OpenGL VBOs via GLFW/GLAD).

### Key Types
- `TerrainEngine`: Manages chunk generation, meshing, and rendering hooks.
- `GreedyMesher`: Collapses visible voxel faces per chunk into quads.
- `Frustum`: Six-plane view frustum used to cull chunks by AABB.

## 📊 Complexity Analysis

| Operation | Complexity | Notes |
| :--- | :--- | :--- |
| Chunk voxel fill | $O(S^3)$ | `S` = chunk edge (16). Per-voxel height comparison. |
| Greedy meshing | $O(S^3)$ | Three axis sweeps with 2D greedy merging. |
| Frustum culling | $O(C)$ | Per-chunk plane tests, `C` = visible chunks. |

## 📝 Notes
- Replace the console `render_visible` method with real draw calls; the quad buffers are sized for direct upload to GPU vertex buffers.
- Extend the mesher to stitch across chunk borders by sampling neighbor chunks when determining face visibility.
