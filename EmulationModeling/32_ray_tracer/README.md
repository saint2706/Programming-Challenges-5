# Ray Tracer

A multithreaded C++ ray tracer supporting spheres and planes with Phong illumination, hard shadows, and basic reflections. A bounding volume hierarchy (BVH) reduces per-ray intersection cost, enabling more complex scenes.

## 📋 Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Performance Notes](#performance-notes)

## 🌟 Features
- Sphere and infinite plane primitives with per-object materials.
- Point light with diffuse and specular (Phong) shading plus configurable ambient term.
- Hard shadows by tracing shadow rays toward the light.
- Optional reflections with a recursion depth cap.
- BVH acceleration structure to prune intersection tests.
- Parallel rendering across scanlines using C++17 threads.
- Outputs a PPM image so no external dependencies are needed.

## 🛠️ Installation
Ensure a C++17 compiler is available (e.g., `g++`, `clang++`).

## 🚀 Usage
Compile and run the demo scene:

```bash
g++ -std=c++17 -O2 main.cpp -o ray_tracer
./ray_tracer > output.ppm
```

Open `output.ppm` with any image viewer that supports the PPM format.

## ⚡ Performance Notes
- The BVH is rebuilt once at startup to reduce intersection checks during rendering.
- The render loop divides scanlines across threads using `std::thread` and joins all workers before writing the image.
- Adjust image resolution or recursion depth to trade visual quality for performance.
