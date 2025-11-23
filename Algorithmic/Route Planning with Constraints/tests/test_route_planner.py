import unittest
from route_planner import Graph, RoutePlanner

class TestRoutePlanner(unittest.TestCase):
    def setUp(self):
        self.g = Graph()
        # A --1-- B --2-- C
        # |       |
        # 4       1
        # |       |
        # D --1-- E

        edges = [
            ('A', 'B', 1), ('B', 'C', 2),
            ('A', 'D', 4), ('D', 'E', 1),
            ('B', 'E', 1)
        ]
        for u, v, w in edges:
            self.g.add_edge(u, v, w)

        self.planner = RoutePlanner(self.g)

    def test_basic_path(self):
        path, cost = self.planner.find_route('A', 'C')
        # A -> B -> C (1 + 2 = 3)
        self.assertEqual(path, ['A', 'B', 'C'])
        self.assertEqual(cost, 3)

    def test_forbidden_node(self):
        # Block B. A -> D -> E -> B(X) ... wait B is blocked.
        # To get to C, must go A -> D -> E -> B -> C? No B is blocked.
        # Is there another way?
        # A -> D -> E ... E is connected to B and D.
        # C is only connected to B.
        # So if B is forbidden, C is unreachable.
        path, cost = self.planner.find_route('A', 'C', forbidden_nodes=['B'])
        self.assertEqual(path, [])
        self.assertEqual(cost, float('inf'))

        # Block E. A -> B -> C (valid)
        path, cost = self.planner.find_route('A', 'C', forbidden_nodes=['E'])
        self.assertEqual(path, ['A', 'B', 'C'])

    def test_forbidden_edge(self):
        # Block A-B. Path must be A -> D -> E -> B -> C
        # Cost: 4 + 1 + 1 + 2 = 8
        path, cost = self.planner.find_route('A', 'C', forbidden_edges=[('A', 'B')])
        self.assertEqual(path, ['A', 'D', 'E', 'B', 'C'])
        self.assertEqual(cost, 8)

    def test_must_visit(self):
        # A -> C, but must visit D.
        # Direct A->D is 4. A->B->E->D is 1+1+1=3.
        # So segment A->D will be A->B->E->D.
        # Segment D->C: D->E->B->C is 1+1+2=4.
        # Total cost: 3 + 4 = 7.
        # Path: A, B, E, D, E, B, C.
        path, cost = self.planner.find_route('A', 'C', must_visit=['D'])
        self.assertEqual(path, ['A', 'B', 'E', 'D', 'E', 'B', 'C'])
        self.assertEqual(cost, 7)

    def test_must_visit_order(self):
        # A -> C, must visit E then B.
        # Segment A->E: A->B->E (Cost 2)
        # Segment E->B: E->B (Cost 1)
        # Segment B->C: B->C (Cost 2)
        # Total Cost: 5.
        # Path: A, B, E, B, C
        path, cost = self.planner.find_route('A', 'C', must_visit=['E', 'B'])
        self.assertEqual(path, ['A', 'B', 'E', 'B', 'C'])

        # A -> C, must visit B then E.
        # A -> B -> E -> B -> C ? (if revisiting allowed)
        # Segments: A->B, B->E, E->C
        # A->B (1)
        # B->E (1)
        # E->B->C (1+2=3)
        # Total: 1+1+3 = 5
        # Path: A, B, E, B, C
        path, cost = self.planner.find_route('A', 'C', must_visit=['B', 'E'])
        self.assertEqual(path, ['A', 'B', 'E', 'B', 'C'])
        self.assertEqual(cost, 5)

if __name__ == '__main__':
    unittest.main()
