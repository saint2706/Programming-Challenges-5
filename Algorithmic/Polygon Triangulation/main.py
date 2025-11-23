import matplotlib.pyplot as plt
from triangulation import triangulate_polygon

def main():
    # Define a simple polygon (CCW)
    # A house shape
    polygon = [
        (0, 0),   # Bottom-Left
        (2, 0),   # Bottom-Right
        (2, 2),   # Top-Right
        (1, 3),   # Roof tip
        (0, 2)    # Top-Left
    ]

    print(f"Triangulating polygon: {polygon}")

    try:
        triangles = triangulate_polygon(polygon)
        print(f"Resulting triangles (indices): {triangles}")

        # Visualize
        plt.figure()

        # Draw polygon outline
        poly_x = [p[0] for p in polygon] + [polygon[0][0]]
        poly_y = [p[1] for p in polygon] + [polygon[0][1]]
        plt.plot(poly_x, poly_y, 'k-', linewidth=2, label='Polygon')

        # Draw triangles
        for i, tri in enumerate(triangles):
            pts = [polygon[idx] for idx in tri]
            pts.append(pts[0]) # close loop
            tx = [p[0] for p in pts]
            ty = [p[1] for p in pts]
            plt.fill(tx, ty, alpha=0.3, edgecolor='r', label=f'Tri {i+1}' if i==0 else "")

            # Label centroid
            cx = sum(p[0] for p in pts[:3]) / 3
            cy = sum(p[1] for p in pts[:3]) / 3
            plt.text(cx, cy, str(i+1), ha='center', va='center')

        plt.legend()
        plt.title("Polygon Triangulation (Ear Clipping)")
        plt.gca().set_aspect('equal')

        output_file = "triangulation_demo.png"
        plt.savefig(output_file)
        print(f"Saved visualization to {output_file}")

    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
