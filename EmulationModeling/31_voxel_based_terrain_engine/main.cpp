#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <future>
#include <iostream>
#include <optional>
#include <random>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>
#include <numeric>

namespace math {
struct Vec3 {
    float x{}, y{}, z{};
};

struct Plane {
    float a{}, b{}, c{}, d{};

    float distance(const Vec3 &p) const { return a * p.x + b * p.y + c * p.z + d; }
};

struct AABB {
    Vec3 min;
    Vec3 max;
};
} // namespace math

// Simple camera frustum used for chunk culling.
class Frustum {
  public:
    // Build a symmetric perspective frustum around the origin-facing -Z for simplicity.
    static Frustum from_perspective(float fov_deg, float aspect, float near, float far) {
        const float fov_rad = fov_deg * 3.14159265f / 180.0f;
        const float tan_half = std::tan(fov_rad / 2.0f);

        Frustum f;
        // Plane equations are normalized for consistent distance checks.
        f.planes = {
            normalize({0, 0, 1, near}),                                         // Near
            normalize({0, 0, -1, far}),                                          // Far
            normalize({1, 0, tan_half * aspect, 0}),                             // Left
            normalize({-1, 0, tan_half * aspect, 0}),                            // Right
            normalize({0, 1, tan_half, 0}),                                      // Bottom
            normalize({0, -1, tan_half, 0}),                                     // Top
        };
        return f;
    }

    bool intersects(const math::AABB &box) const {
        for (const auto &plane : planes) {
            // Compute the most positive vertex for the plane normal.
            math::Vec3 p{plane.a >= 0 ? box.max.x : box.min.x, plane.b >= 0 ? box.max.y : box.min.y,
                          plane.c >= 0 ? box.max.z : box.min.z};
            if (plane.distance(p) < 0)
                return false; // Completely outside.
        }
        return true;
    }

  private:
    static math::Plane normalize(const math::Plane &p) {
        const float len = std::sqrt(p.a * p.a + p.b * p.b + p.c * p.c);
        return {p.a / len, p.b / len, p.c / len, p.d / len};
    }

    std::array<math::Plane, 6> planes{};
};

// Lightweight Perlin noise for terrain heights.
class PerlinNoise {
  public:
    explicit PerlinNoise(uint32_t seed = 1337) {
        permutation.resize(256);
        std::iota(permutation.begin(), permutation.end(), 0);
        std::mt19937 rng(seed);
        std::shuffle(permutation.begin(), permutation.end(), rng);
        permutation.insert(permutation.end(), permutation.begin(), permutation.end());
    }

    float noise(float x, float y) const {
        const int xi = static_cast<int>(std::floor(x)) & 255;
        const int yi = static_cast<int>(std::floor(y)) & 255;

        const float xf = x - std::floor(x);
        const float yf = y - std::floor(y);

        const float u = fade(xf);
        const float v = fade(yf);

        const int aa = permutation[permutation[xi] + yi];
        const int ab = permutation[permutation[xi] + yi + 1];
        const int ba = permutation[permutation[xi + 1] + yi];
        const int bb = permutation[permutation[xi + 1] + yi + 1];

        const float x1 = lerp(grad(aa, xf, yf), grad(ba, xf - 1, yf), u);
        const float x2 = lerp(grad(ab, xf, yf - 1), grad(bb, xf - 1, yf - 1), u);
        return (lerp(x1, x2, v) + 1.0f) * 0.5f; // Normalize to [0,1].
    }

  private:
    static float fade(float t) { return t * t * t * (t * (t * 6 - 15) + 10); }
    static float lerp(float a, float b, float t) { return a + t * (b - a); }

    static float grad(int hash, float x, float y) {
        const int h = hash & 3;
        const float u = h < 2 ? x : y;
        const float v = h < 2 ? y : x;
        return ((h & 1) ? -u : u) + ((h & 2) ? -2.0f * v : 2.0f * v);
    }

    std::vector<int> permutation;
};

constexpr int CHUNK_SIZE = 16;

enum class BlockType : uint8_t { Air = 0, Solid = 1 };

struct ChunkCoord {
    int x{};
    int z{};

    bool operator==(const ChunkCoord &other) const { return x == other.x && z == other.z; }
};

struct ChunkCoordHash {
    std::size_t operator()(const ChunkCoord &c) const noexcept {
        return std::hash<int>()(c.x * 73856093 ^ c.z * 19349663);
    }
};

struct Quad {
    std::array<float, 12> positions{}; // 4 * (x,y,z)
    std::array<float, 8> uvs{};        // 4 * (u,v)
    std::array<float, 3> normal{};
};

struct Chunk {
    std::array<BlockType, CHUNK_SIZE * CHUNK_SIZE * CHUNK_SIZE> blocks{};
    std::vector<Quad> mesh;

    BlockType at(int x, int y, int z) const {
        if (x < 0 || y < 0 || z < 0 || x >= CHUNK_SIZE || y >= CHUNK_SIZE || z >= CHUNK_SIZE)
            return BlockType::Air;
        return blocks[x + y * CHUNK_SIZE + z * CHUNK_SIZE * CHUNK_SIZE];
    }
};

struct MeshBuildResult {
    ChunkCoord coord;
    std::vector<Quad> mesh;
};

class GreedyMesher {
  public:
    static std::vector<Quad> build(const Chunk &chunk, const ChunkCoord &coord) {
        std::vector<Quad> result;
        for (int axis = 0; axis < 3; ++axis) {
            slice_axis(axis, chunk, coord, result);
        }
        return result;
    }

  private:
    struct MaskCell {
        BlockType type = BlockType::Air;
        bool exists = false;
        bool forward = true; // which normal direction to emit
    };

    static void slice_axis(int axis, const Chunk &chunk, const ChunkCoord &coord, std::vector<Quad> &quads) {
        const int u = (axis + 1) % 3;
        const int v = (axis + 2) % 3;
        std::array<int, 3> dims{CHUNK_SIZE, CHUNK_SIZE, CHUNK_SIZE};
        std::vector<MaskCell> mask(CHUNK_SIZE * CHUNK_SIZE);

        // Sweep through the chunk along the chosen axis.
        for (int d = 0; d <= dims[axis]; ++d) {
            // Build mask for this slice comparing voxel pairs on both sides.
            for (int j = 0; j < dims[v]; ++j) {
                for (int i = 0; i < dims[u]; ++i) {
                    std::array<int, 3> p1{};
                    std::array<int, 3> p2{};
                    p1[axis] = d;
                    p2[axis] = d - 1;
                    p1[u] = p2[u] = i;
                    p1[v] = p2[v] = j;

                    const BlockType current = get_block(chunk, p1[0], p1[1], p1[2]);
                    const BlockType neighbor = get_block(chunk, p2[0], p2[1], p2[2]);
                    MaskCell cell;
                    cell.exists = (current != neighbor);
                    cell.type = current != BlockType::Air ? current : neighbor;
                    cell.forward = neighbor == BlockType::Air; // Determine normal direction.
                    mask[i + j * dims[u]] = cell;
                }
            }

            // Greedy merge rectangles in the 2D mask.
            for (int j = 0; j < dims[v]; ++j) {
                int i = 0;
                while (i < dims[u]) {
                    const MaskCell cell = mask[i + j * dims[u]];
                    if (!cell.exists) {
                        ++i;
                        continue;
                    }
                    int width = 1;
                    while (i + width < dims[u] && mask[i + width + j * dims[u]].exists &&
                           mask[i + width + j * dims[u]].type == cell.type &&
                           mask[i + width + j * dims[u]].forward == cell.forward) {
                        ++width;
                    }

                    int height = 1;
                    bool extend = true;
                    while (j + height < dims[v] && extend) {
                        for (int k = 0; k < width; ++k) {
                            const MaskCell &next = mask[i + k + (j + height) * dims[u]];
                            if (!next.exists || next.type != cell.type || next.forward != cell.forward) {
                                extend = false;
                                break;
                            }
                        }
                        if (extend)
                            ++height;
                    }

                    // Clear consumed cells.
                    for (int y = 0; y < height; ++y) {
                        for (int x = 0; x < width; ++x) {
                            mask[i + x + (j + y) * dims[u]].exists = false;
                        }
                    }

                    emit_quad(axis, coord, d, i, j, width, height, cell.forward, quads);
                    i += width;
                }
            }
        }
    }

    static BlockType get_block(const Chunk &chunk, int x, int y, int z) { return chunk.at(x, y, z); }

    static void emit_quad(int axis, const ChunkCoord &coord, int d, int i, int j, int w, int h, bool forward,
                          std::vector<Quad> &quads) {
        // Build four vertices of the quad.
        // axis: 0=x,1=y,2=z. u=(axis+1)%3, v=(axis+2)%3
        const int u = (axis + 1) % 3;
        const int v = (axis + 2) % 3;
        std::array<int, 3> du{};
        std::array<int, 3> dv{};
        du[u] = w;
        dv[v] = h;

        std::array<float, 12> verts{};
        auto set_vert = [&](int idx, const std::array<int, 3> &base) {
            const int ox = coord.x * CHUNK_SIZE;
            const int oz = coord.z * CHUNK_SIZE;
            verts[idx * 3 + 0] = static_cast<float>(base[0] + ox);
            verts[idx * 3 + 1] = static_cast<float>(base[1]);
            verts[idx * 3 + 2] = static_cast<float>(base[2] + oz);
        };

        std::array<int, 3> base{};
        base[axis] = d;
        base[u] = i;
        base[v] = j;

        set_vert(0, base);
        set_vert(1, {base[0] + du[0], base[1] + du[1], base[2] + du[2]});
        set_vert(2, {base[0] + du[0] + dv[0], base[1] + du[1] + dv[1], base[2] + du[2] + dv[2]});
        set_vert(3, {base[0] + dv[0], base[1] + dv[1], base[2] + dv[2]});

        std::array<float, 8> uvs{0, 0, 1, 0, 1, 1, 0, 1};
        std::array<float, 3> normal{};
        normal[axis] = forward ? 1.0f : -1.0f;

        if (!forward) {
            std::swap(verts[0], verts[3]);
            std::swap(verts[1], verts[4]);
            std::swap(verts[2], verts[5]);
            std::swap(verts[6], verts[9]);
            std::swap(verts[7], verts[10]);
            std::swap(verts[8], verts[11]);
        }

        quads.push_back({verts, uvs, normal});
    }
};

class TerrainEngine {
  public:
    TerrainEngine() : noise(42) {}

    void generate_world(int radius) {
        std::vector<std::future<MeshBuildResult>> jobs;
        for (int cx = -radius; cx <= radius; ++cx) {
            for (int cz = -radius; cz <= radius; ++cz) {
                jobs.emplace_back(std::async(std::launch::async, [=, this]() { return build_chunk({cx, cz}); }));
            }
        }
        for (auto &job : jobs) {
            auto result = job.get();
            auto &chunk = chunks[result.coord];
            chunk.mesh = std::move(result.mesh);
        }
    }

    void render_visible(const Frustum &frustum) const {
        for (const auto &[coord, chunk] : chunks) {
            if (!frustum.intersects(chunk_bounds(coord)))
                continue; // Frustum culling.
            std::cout << "Chunk (" << coord.x << ", " << coord.z << ") quads: " << chunk.mesh.size() << "\n";
        }
    }

  private:
    MeshBuildResult build_chunk(const ChunkCoord &coord) const {
        Chunk chunk;
        // Populate voxels using 2D Perlin noise for heightmap.
        for (int x = 0; x < CHUNK_SIZE; ++x) {
            for (int z = 0; z < CHUNK_SIZE; ++z) {
                const int world_x = coord.x * CHUNK_SIZE + x;
                const int world_z = coord.z * CHUNK_SIZE + z;
                const float height = generate_height(world_x, world_z);
                for (int y = 0; y < CHUNK_SIZE; ++y) {
                    const bool solid = y <= height;
                    chunk.blocks[x + y * CHUNK_SIZE + z * CHUNK_SIZE * CHUNK_SIZE] = solid ? BlockType::Solid : BlockType::Air;
                }
            }
        }

        MeshBuildResult result{coord, GreedyMesher::build(chunk, coord)};
        return result;
    }

    float generate_height(int x, int z) const {
        const float scale = 0.05f;
        const float elevation = noise.noise(x * scale, z * scale);
        const float hill = noise.noise(x * scale * 0.5f, z * scale * 0.5f);
        return 4 + elevation * 8 + hill * 4; // Up to ~16 blocks high.
    }

    math::AABB chunk_bounds(const ChunkCoord &coord) const {
        const float min_x = static_cast<float>(coord.x * CHUNK_SIZE);
        const float min_z = static_cast<float>(coord.z * CHUNK_SIZE);
        return {{min_x, 0.0f, min_z}, {min_x + CHUNK_SIZE, static_cast<float>(CHUNK_SIZE), min_z + CHUNK_SIZE}};
    }

    PerlinNoise noise;
    std::unordered_map<ChunkCoord, Chunk, ChunkCoordHash> chunks;
};

int main() {
    TerrainEngine engine;
    // Generate a 3x3 block of chunks around the origin using async meshing.
    engine.generate_world(1);

    Frustum frustum = Frustum::from_perspective(75.0f, 16.0f / 9.0f, 0.1f, 100.0f);
    engine.render_visible(frustum);
    std::cout << "Each chunk uses greedy meshing to minimize draw calls.\n";
    return 0;
}
