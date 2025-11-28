"""
Implementation of the algorithm.
"""

from rtree import RTree, Rect
import os

def main():
    """
    Docstring for main.
    """
    tree = RTree()

    # Data: Cities with lat/lon as (x, y)
    cities = [
        ("New York", 40, -74),
        ("Los Angeles", 34, -118),
        ("Chicago", 41, -87),
        ("Houston", 29, -95),
        ("London", 51, 0),
        ("Paris", 48, 2),
        ("Tokyo", 35, 139)
    ]

    print("Inserting cities...")
    for name, lat, lon in cities:
        # Represent point as small rect
        r = Rect(lat, lon, lat, lon)
        tree.insert(r, name)

    print("Saving tree to 'cities.json'...")
    tree.save("cities.json")

    # Query: US approximate bounds (Lat 25-50, Lon -130 to -60)
    query = Rect(25, -130, 50, -60)
    print(f"\nQuerying US Area: {query}")
    results = tree.search(query)
    print(f"Found: {results}")

    # Query: Europe (Lat 35-60, Lon -10 to 40)
    query_eu = Rect(35, -10, 60, 40)
    print(f"\nQuerying Europe Area: {query_eu}")
    results_eu = tree.search(query_eu)
    print(f"Found: {results_eu}")

    # Load test
    print("\nLoading from disk...")
    new_tree = RTree()
    new_tree.load("cities.json")
    results_loaded = new_tree.search(query)
    print(f"Query loaded tree (US): {results_loaded}")

if __name__ == "__main__":
    main()
