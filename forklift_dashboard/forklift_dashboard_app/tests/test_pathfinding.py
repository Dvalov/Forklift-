from django.test import TestCase
from forklift_dashboard_app.pathfinding import astar


class AstarTest(TestCase):

    def test_start_equals_goal_returns_empty_list(self):
        result = astar((3, 5), (3, 5), set())
        self.assertEqual(result, [])

    def test_adjacent_goal_no_obstacles(self):
        result = astar((0, 0), (1, 0), set())
        self.assertEqual(result, [{"x": 1, "z": 0}])

    def test_straight_path_two_steps(self):
        result = astar((0, 0), (2, 0), set())
        self.assertEqual(result, [{"x": 1, "z": 0}, {"x": 2, "z": 0}])

    def test_path_around_single_obstacle(self):
        # Direct path (1,0) is blocked; must go via (0,1)->(1,1)->(2,1) or similar
        obstacles = {(1, 0)}
        result = astar((0, 0), (2, 0), obstacles)
        self.assertIsNotNone(result)
        # First element must not be start
        self.assertNotEqual(result[0], {"x": 0, "z": 0})
        # Last element must be goal
        self.assertEqual(result[-1], {"x": 2, "z": 0})
        # No waypoint is the blocked cell
        self.assertNotIn({"x": 1, "z": 0}, result)

    def test_no_path_returns_none(self):
        # Surround start completely
        obstacles = {(1, 0), (-1, 0), (0, 1), (0, -1)}
        result = astar((0, 0), (5, 5), obstacles)
        self.assertIsNone(result)

    def test_goal_in_obstacle_set_is_discarded(self):
        # goal (2,0) is in obstacle set — must still be reachable (decision A-2 pitfall fix)
        obstacles = {(2, 0)}
        result = astar((0, 0), (2, 0), obstacles)
        self.assertIsNotNone(result, "goal should be discarded from obstacles before A* search")
        self.assertEqual(result[-1], {"x": 2, "z": 0})

    def test_start_not_in_returned_path(self):
        result = astar((0, 0), (3, 0), set())
        start_dict = {"x": 0, "z": 0}
        self.assertNotIn(start_dict, result)

    def test_path_waypoints_are_dicts_with_x_and_z(self):
        result = astar((0, 0), (2, 2), set())
        self.assertIsNotNone(result)
        for wp in result:
            self.assertIn("x", wp)
            self.assertIn("z", wp)
            self.assertIsInstance(wp["x"], int)
            self.assertIsInstance(wp["z"], int)

    def test_float_start_coerced_to_int(self):
        # Forklift position_x/z are FloatField; astar must coerce them
        result = astar((0.7, 0.3), (2, 0), set())
        self.assertIsNotNone(result)
        self.assertEqual(result[-1], {"x": 2, "z": 0})
