#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <memory>
#include <thread>
#include <utility>
#include <vector>

constexpr double kEpsilon = 1e-4;
constexpr double kInfinity = std::numeric_limits<double>::infinity();
constexpr double kPi = 3.14159265358979323846;

struct Vec3 {
    double x{}, y{}, z{};

    Vec3() = default;
    Vec3(double x_, double y_, double z_) : x(x_), y(y_), z(z_) {}

    Vec3 operator+(const Vec3 &o) const { return {x + o.x, y + o.y, z + o.z}; }
    Vec3 operator-(const Vec3 &o) const { return {x - o.x, y - o.y, z - o.z}; }
    Vec3 operator-() const { return {-x, -y, -z}; }
    Vec3 operator*(double s) const { return {x * s, y * s, z * s}; }
    Vec3 operator/(double s) const { return {x / s, y / s, z / s}; }
    Vec3 &operator+=(const Vec3 &o) {
        x += o.x;
        y += o.y;
        z += o.z;
        return *this;
    }
    Vec3 &operator*=(double s) {
        x *= s;
        y *= s;
        z *= s;
        return *this;
    }
};

inline Vec3 operator*(double s, const Vec3 &v) { return v * s; }
inline Vec3 operator*(const Vec3 &a, const Vec3 &b) { return {a.x * b.x, a.y * b.y, a.z * b.z}; }

inline double dot(const Vec3 &a, const Vec3 &b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
inline Vec3 cross(const Vec3 &a, const Vec3 &b) {
    return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x};
}

inline double length(const Vec3 &v) { return std::sqrt(dot(v, v)); }
inline Vec3 normalize(const Vec3 &v) {
    double len = length(v);
    if (len == 0)
        return {0, 0, 0};
    return v / len;
}

struct Ray {
    Vec3 origin;
    Vec3 direction;
    Vec3 at(double t) const { return origin + direction * t; }
};

struct Material {
    Vec3 diffuse{0.8, 0.8, 0.8};
    Vec3 specular{0.5, 0.5, 0.5};
    double shininess{32.0};
    double reflectivity{0.0};
};

struct AABB {
    Vec3 min{ kInfinity, kInfinity, kInfinity };
    Vec3 max{ -kInfinity, -kInfinity, -kInfinity };

    AABB() = default;
    AABB(const Vec3 &min_, const Vec3 &max_) : min(min_), max(max_) {}

    bool hit(const Ray &ray, double t_min, double t_max) const {
        for (int a = 0; a < 3; ++a) {
            double invD;
            double orig;
            double minB;
            double maxB;
            if (a == 0) { invD = 1.0 / ray.direction.x; orig = ray.origin.x; minB = min.x; maxB = max.x; }
            else if (a == 1) { invD = 1.0 / ray.direction.y; orig = ray.origin.y; minB = min.y; maxB = max.y; }
            else { invD = 1.0 / ray.direction.z; orig = ray.origin.z; minB = min.z; maxB = max.z; }

            double t0 = (minB - orig) * invD;
            double t1 = (maxB - orig) * invD;
            if (invD < 0.0)
                std::swap(t0, t1);
            t_min = t0 > t_min ? t0 : t_min;
            t_max = t1 < t_max ? t1 : t_max;
            if (t_max <= t_min)
                return false;
        }
        return true;
    }
};

inline AABB surrounding_box(const AABB &a, const AABB &b) {
    Vec3 small(std::min(a.min.x, b.min.x), std::min(a.min.y, b.min.y), std::min(a.min.z, b.min.z));
    Vec3 big(std::max(a.max.x, b.max.x), std::max(a.max.y, b.max.y), std::max(a.max.z, b.max.z));
    return {small, big};
}

struct HitRecord {
    Vec3 point;
    Vec3 normal;
    double t{0.0};
    bool front_face{true};
    Material material;

    void set_face_normal(const Ray &ray, const Vec3 &outward_normal) {
        front_face = dot(ray.direction, outward_normal) < 0;
        normal = front_face ? outward_normal : outward_normal * -1.0;
    }
};

class Shape {
  public:
    virtual ~Shape() = default;
    virtual bool intersect(const Ray &ray, double t_min, double t_max, HitRecord &rec) const = 0;
    virtual AABB bounding_box() const = 0;
};

class Sphere : public Shape {
  public:
    Sphere(Vec3 c, double r, Material m) : center(c), radius(r), mat(std::move(m)) {}

    bool intersect(const Ray &ray, double t_min, double t_max, HitRecord &rec) const override {
        Vec3 oc = ray.origin - center;
        double a = dot(ray.direction, ray.direction);
        double b = dot(oc, ray.direction);
        double c = dot(oc, oc) - radius * radius;
        double discriminant = b * b - a * c;
        if (discriminant < 0)
            return false;
        double sqrt_d = std::sqrt(discriminant);

        auto root = (-b - sqrt_d) / a;
        if (root < t_min || root > t_max) {
            root = (-b + sqrt_d) / a;
            if (root < t_min || root > t_max)
                return false;
        }

        rec.t = root;
        rec.point = ray.at(rec.t);
        Vec3 outward_normal = (rec.point - center) / radius;
        rec.set_face_normal(ray, outward_normal);
        rec.material = mat;
        return true;
    }

    AABB bounding_box() const override {
        Vec3 r(radius, radius, radius);
        return {center - r, center + r};
    }

  private:
    Vec3 center;
    double radius;
    Material mat;
};

class Plane : public Shape {
  public:
    Plane(Vec3 p, Vec3 n, Material m) : point(p), normal_vec(normalize(n)), mat(std::move(m)) {}

    bool intersect(const Ray &ray, double t_min, double t_max, HitRecord &rec) const override {
        double denom = dot(normal_vec, ray.direction);
        if (std::abs(denom) < 1e-8)
            return false;
        double t = dot(point - ray.origin, normal_vec) / denom;
        if (t < t_min || t > t_max)
            return false;
        rec.t = t;
        rec.point = ray.at(t);
        rec.set_face_normal(ray, normal_vec);
        rec.material = mat;
        return true;
    }

    AABB bounding_box() const override {
        // Large but finite bounding box to keep BVH stable with infinite planes.
        const double big = 1e5;
        return {Vec3(-big, -big, -big), Vec3(big, big, big)};
    }

  private:
    Vec3 point;
    Vec3 normal_vec;
    Material mat;
};

class BVHNode : public Shape {
  public:
    BVHNode() = default;

    explicit BVHNode(std::vector<std::shared_ptr<Shape>> &objects, size_t start, size_t end) {
        auto span = end - start;
        if (span == 0)
            throw std::runtime_error("BVHNode created with empty span");

        int axis = static_cast<int>(std::rand() % 3);
        auto comparator = [axis](const std::shared_ptr<Shape> &a, const std::shared_ptr<Shape> &b) {
            return centroid(a->bounding_box(), axis) < centroid(b->bounding_box(), axis);
        };

        if (span == 1) {
            left = right = objects[start];
        } else if (span == 2) {
            if (comparator(objects[start], objects[start + 1])) {
                left = objects[start];
                right = objects[start + 1];
            } else {
                left = objects[start + 1];
                right = objects[start];
            }
        } else {
            std::sort(objects.begin() + start, objects.begin() + end, comparator);
            size_t mid = start + span / 2;
            left = std::make_shared<BVHNode>(objects, start, mid);
            right = std::make_shared<BVHNode>(objects, mid, end);
        }

        AABB box_left = left->bounding_box();
        AABB box_right = right->bounding_box();
        box = surrounding_box(box_left, box_right);
    }

    bool intersect(const Ray &ray, double t_min, double t_max, HitRecord &rec) const override {
        if (!box.hit(ray, t_min, t_max))
            return false;
        bool hit_left = left->intersect(ray, t_min, t_max, rec);
        bool hit_right = right->intersect(ray, t_min, hit_left ? rec.t : t_max, rec_right);

        if (hit_right)
            rec = rec_right;
        return hit_left || hit_right;
    }

    AABB bounding_box() const override { return box; }

  private:
    std::shared_ptr<Shape> left;
    std::shared_ptr<Shape> right;
    AABB box;
    mutable HitRecord rec_right;

    static double centroid(const AABB &bbox, int axis) {
        if (axis == 0)
            return (bbox.min.x + bbox.max.x) * 0.5;
        if (axis == 1)
            return (bbox.min.y + bbox.max.y) * 0.5;
        return (bbox.min.z + bbox.max.z) * 0.5;
    }
};

struct Light {
    Vec3 position;
    Vec3 color{1.0, 1.0, 1.0};
    double intensity{1.0};
};

class Scene {
  public:
    void add_object(const std::shared_ptr<Shape> &obj) { objects.push_back(obj); }
    void set_light(const Light &l) { light = l; }

    void build_bvh() { bvh_root = std::make_shared<BVHNode>(objects, 0, objects.size()); }

    bool trace(const Ray &ray, double t_min, double t_max, HitRecord &rec) const {
        if (bvh_root)
            return bvh_root->intersect(ray, t_min, t_max, rec);
        bool hit_anything = false;
        double closest = t_max;
        for (const auto &obj : objects) {
            if (obj->intersect(ray, t_min, closest, rec)) {
                hit_anything = true;
                closest = rec.t;
            }
        }
        return hit_anything;
    }

    bool in_shadow(const Vec3 &point, const Vec3 &light_dir, double light_distance) const {
        Ray shadow_ray{point + kEpsilon * light_dir, light_dir};
        HitRecord temp;
        return trace(shadow_ray, kEpsilon, light_distance, temp);
    }

    const Light &get_light() const { return light; }

  private:
    std::vector<std::shared_ptr<Shape>> objects;
    std::shared_ptr<BVHNode> bvh_root;
    Light light;
};

class Camera {
  public:
    Camera(Vec3 lookfrom, Vec3 lookat, Vec3 vup, double vfov, double aspect) {
        double theta = vfov * kPi / 180.0;
        double h = std::tan(theta / 2.0);
        double viewport_height = 2.0 * h;
        double viewport_width = aspect * viewport_height;

        w = normalize(lookfrom - lookat);
        u = normalize(cross(vup, w));
        v = cross(w, u);

        origin = lookfrom;
        horizontal = viewport_width * u;
        vertical = viewport_height * v;
        lower_left_corner = origin - horizontal / 2 - vertical / 2 - w;
    }

    Ray get_ray(double s, double t) const {
        return {origin, normalize(lower_left_corner + s * horizontal + t * vertical - origin)};
    }

  private:
    Vec3 origin;
    Vec3 lower_left_corner;
    Vec3 horizontal;
    Vec3 vertical;
    Vec3 u, v, w;
};

Vec3 clamp_color(const Vec3 &c) {
    auto clamp = [](double x) { return std::max(0.0, std::min(1.0, x)); };
    return {clamp(c.x), clamp(c.y), clamp(c.z)};
}

Vec3 shade(const Scene &scene, const Ray &ray, const HitRecord &rec, int depth) {
    const Material &mat = rec.material;
    Vec3 ambient = 0.05 * mat.diffuse;
    Vec3 color = ambient;

    const Light &light = scene.get_light();
    Vec3 to_light = light.position - rec.point;
    double distance_to_light = length(to_light);
    Vec3 light_dir = normalize(to_light);

    bool shadowed = scene.in_shadow(rec.point, light_dir, distance_to_light);

    if (!shadowed) {
        double diff_intensity = std::max(0.0, dot(rec.normal, light_dir)) * light.intensity;
        Vec3 diffuse = diff_intensity * (mat.diffuse * light.color);

        Vec3 view_dir = normalize(-ray.direction);
        Vec3 reflect_dir = normalize(2 * dot(rec.normal, light_dir) * rec.normal - light_dir);
        double spec_angle = std::max(0.0, dot(view_dir, reflect_dir));
        Vec3 specular = std::pow(spec_angle, mat.shininess) * (mat.specular * light.intensity);

        color += diffuse + specular;
    }

    if (depth <= 0 || mat.reflectivity <= 0.0)
        return color;

    Vec3 reflect_dir = normalize(ray.direction - 2 * dot(ray.direction, rec.normal) * rec.normal);
    Ray reflected_ray{rec.point + reflect_dir * kEpsilon, reflect_dir};
    HitRecord reflected_hit;
    if (scene.trace(reflected_ray, kEpsilon, kInfinity, reflected_hit)) {
        color += mat.reflectivity * shade(scene, reflected_ray, reflected_hit, depth - 1);
    }
    return color;
}

void render_section(const Scene &scene, const Camera &camera, int width, int height, int start_row, int end_row,
                    int max_depth, std::vector<Vec3> &framebuffer) {
    for (int j = start_row; j < end_row; ++j) {
        for (int i = 0; i < width; ++i) {
            double u = (i + 0.5) / static_cast<double>(width);
            double v = (j + 0.5) / static_cast<double>(height);
            Ray ray = camera.get_ray(u, 1.0 - v);
            HitRecord rec;
            Vec3 pixel_color{0, 0, 0};
            if (scene.trace(ray, kEpsilon, kInfinity, rec)) {
                pixel_color = shade(scene, ray, rec, max_depth);
            }
            framebuffer[j * width + i] = clamp_color(pixel_color);
        }
    }
}

int main() {
    const int image_width = 640;
    const int image_height = 360;
    const int max_depth = 3;

    // Camera setup
    Vec3 lookfrom(0, 1, 5);
    Vec3 lookat(0, 0.5, 0);
    Vec3 vup(0, 1, 0);
    double vfov = 60.0;
    double aspect_ratio = static_cast<double>(image_width) / image_height;
    Camera camera(lookfrom, lookat, vup, vfov, aspect_ratio);

    // Scene
    Scene scene;
    Light light{{5, 5, 5}, {1, 1, 1}, 1.2};
    scene.set_light(light);

    Material red_diffuse{{0.9, 0.2, 0.2}, {0.5, 0.5, 0.5}, 16.0, 0.2};
    Material green_diffuse{{0.2, 0.9, 0.2}, {0.4, 0.4, 0.4}, 16.0, 0.0};
    Material mirror{{0.8, 0.8, 0.8}, {1.0, 1.0, 1.0}, 64.0, 0.6};
    Material floor_mat{{0.75, 0.75, 0.75}, {0.2, 0.2, 0.2}, 8.0, 0.0};

    scene.add_object(std::make_shared<Sphere>(Vec3(-1.0, 0.5, 0.0), 0.5, red_diffuse));
    scene.add_object(std::make_shared<Sphere>(Vec3(1.0, 0.5, -0.5), 0.5, green_diffuse));
    scene.add_object(std::make_shared<Sphere>(Vec3(0.0, 1.0, -1.5), 0.7, mirror));
    scene.add_object(std::make_shared<Plane>(Vec3(0, 0, 0), Vec3(0, 1, 0), floor_mat));

    scene.build_bvh();

    std::vector<Vec3> framebuffer(image_width * image_height);

    unsigned int thread_count = std::max(1u, std::thread::hardware_concurrency());
    std::vector<std::thread> workers;
    int rows_per_thread = (image_height + thread_count - 1) / thread_count;

    for (unsigned int t = 0; t < thread_count; ++t) {
        int start_row = t * rows_per_thread;
        int end_row = std::min(image_height, start_row + rows_per_thread);
        if (start_row >= end_row)
            continue;
        workers.emplace_back(render_section, std::cref(scene), std::cref(camera), image_width, image_height, start_row,
                             end_row, max_depth, std::ref(framebuffer));
    }

    for (auto &w : workers)
        w.join();

    std::cout << "P3\n" << image_width << " " << image_height << "\n255\n";
    for (const auto &c : framebuffer) {
        int ir = static_cast<int>(255.999 * c.x);
        int ig = static_cast<int>(255.999 * c.y);
        int ib = static_cast<int>(255.999 * c.z);
        std::cout << ir << ' ' << ig << ' ' << ib << '\n';
    }

    return 0;
}
