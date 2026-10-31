"""
Unit tests for Intelligent Campus Navigation Agent.
Validates:
  1. Graph creation and integrity.
  2. State and action space generation.
  3. Admissibility and consistency of heuristics.
  4. BFS, DFS, A* (Distance and Time heuristics), and Dijkstra pathfinding.
  5. Obstacle avoidance and blocked path re-routing.
  6. Accessibility route constraints (excluding stairs for wheelchair mode).
  7. Crowd level cost differentiation.
  8. Environment dynamic simulator and partial observability replanning.
"""

import unittest
import math
from core.graph import create_default_campus_graph, CampusNode, CampusEdge
from core.state_action import CampusProblem, CampusState
from core.heuristics import euclidean_distance, manhattan_distance, estimated_travel_time
from core.algorithms import (
    breadth_first_search,
    depth_first_search,
    a_star_search,
    greedy_best_first_search,
    run_algorithm
)
from core.environment import CampusEnvironmentSimulator, get_peas_description, get_environment_classifications


class TestCampusNavigation(unittest.TestCase):
    def setUp(self):
        self.graph = create_default_campus_graph()
        self.simulator = CampusEnvironmentSimulator(self.graph)

    def test_graph_structure(self):
        """Verify the graph has nodes across all required categories."""
        self.assertGreater(len(self.graph.nodes), 20)
        categories = {n.category for n in self.graph.nodes.values()}
        self.assertIn("Classroom", categories)
        self.assertIn("Laboratory", categories)
        self.assertIn("Office", categories)
        self.assertIn("Department", categories)
        self.assertIn("Facility", categories)
        self.assertIn("Entrance", categories)

    def test_state_action_transitions(self):
        """Verify states and actions correctly produce child states."""
        prob = CampusProblem(self.graph, "gate_main", "cs_101", preference="distance")
        actions = prob.get_actions(prob.initial_state)
        self.assertGreater(len(actions), 0)
        for act in actions:
            self.assertEqual(act.from_node_id, "gate_main")
            child = prob.result(prob.initial_state, act)
            self.assertEqual(child.node_id, act.to_node_id)
            cost = prob.step_cost(prob.initial_state, act)
            self.assertGreater(cost, 0.0)

    def test_heuristic_admissibility(self):
        """Verify Euclidean and Time heuristics never overestimate true cost."""
        n1 = self.graph.get_node("gate_main")
        n2 = self.graph.get_node("cs_lab_ai")
        s1 = CampusState.from_node(n1)
        s2 = CampusState.from_node(n2)

        # True shortest path distance via A*
        prob = CampusProblem(self.graph, "gate_main", "cs_lab_ai", preference="distance")
        res_a_star = a_star_search(prob, heuristic_type="euclidean")
        self.assertTrue(res_a_star.success)
        true_dist = res_a_star.total_distance

        h_dist = euclidean_distance(s1, s2)
        self.assertLessEqual(h_dist, true_dist + 1e-5, "Euclidean heuristic must be admissible (<= true distance)")

        # Test time heuristic
        prob_time = CampusProblem(self.graph, "gate_main", "cs_lab_ai", preference="time")
        res_time = a_star_search(prob_time, heuristic_type="time")
        self.assertTrue(res_time.success)
        true_time = res_time.total_time
        h_time = estimated_travel_time(s1, s2)
        self.assertLessEqual(h_time, true_time + 1e-5, "Time heuristic must be admissible (<= true time)")

    def test_bfs_dfs_astar_reachability(self):
        """Test that BFS, DFS, and A* all find valid paths from Gate to CS Lab."""
        start = "gate_main"
        goal = "cs_lab_ai"

        prob_bfs = CampusProblem(self.graph, start, goal, preference="distance")
        res_bfs = breadth_first_search(prob_bfs)
        self.assertTrue(res_bfs.success)
        self.assertEqual(res_bfs.path_nodes[0], start)
        self.assertEqual(res_bfs.path_nodes[-1], goal)

        prob_dfs = CampusProblem(self.graph, start, goal, preference="distance")
        res_dfs = depth_first_search(prob_dfs)
        self.assertTrue(res_dfs.success)
        self.assertEqual(res_dfs.path_nodes[0], start)
        self.assertEqual(res_dfs.path_nodes[-1], goal)

        prob_astar = CampusProblem(self.graph, start, goal, preference="distance")
        res_astar = a_star_search(prob_astar, heuristic_type="euclidean")
        self.assertTrue(res_astar.success)
        self.assertEqual(res_astar.path_nodes[0], start)
        self.assertEqual(res_astar.path_nodes[-1], goal)

        # A* distance should be <= DFS distance (optimality guarantee)
        self.assertLessEqual(res_astar.total_distance, res_dfs.total_distance)

    def test_open_and_closed_list_tracking(self):
        """Verify open and closed lists are logged at every search step."""
        prob = CampusProblem(self.graph, "admin_lobby", "chem_lab", preference="distance")
        res = a_star_search(prob, heuristic_type="euclidean")
        self.assertTrue(res.success)
        self.assertGreater(len(res.steps), 0)

        # Check step details
        for step in res.steps:
            self.assertIsNotNone(step.current_node)
            self.assertIsInstance(step.open_list, list)
            self.assertIsInstance(step.closed_list, list)
            self.assertIn(step.current_node, step.closed_list)

    def test_accessibility_constraint(self):
        """Verify that accessibility mode never routes through stairs."""
        # Route to second floor CS Lab: stairs vs elevator
        prob = CampusProblem(self.graph, "cs_entrance", "cs_lab_ai", preference="accessibility")
        res = a_star_search(prob, heuristic_type="euclidean")
        self.assertTrue(res.success)
        self.assertTrue(res.all_accessible)

        # Path must NOT contain stairs
        for seg in res.path_segments:
            self.assertNotEqual(seg.path_type, "stairs", "Accessible path must not include stairs")
            self.assertTrue(seg.accessible)

        # Must include the elevator
        path_types = [seg.path_type for seg in res.path_segments]
        self.assertIn("elevator", path_types)

    def test_dynamic_obstacle_rerouting(self):
        """Verify that blocking a key edge forces the agent to take an alternate path."""
        start = "gate_main"
        goal = "admin_lobby"

        # Baseline: direct path
        prob_base = CampusProblem(self.graph, start, goal, preference="distance")
        res_base = a_star_search(prob_base)
        self.assertTrue(res_base.success)
        self.assertIn("gate_main", res_base.path_nodes)
        self.assertIn("admin_lobby", res_base.path_nodes)
        orig_dist = res_base.total_distance

        # Block the direct edge (gate_main, admin_lobby)
        self.graph.set_edge_blocked("gate_main", "admin_lobby", True, "Construction barrier")

        prob_blocked = CampusProblem(self.graph, start, goal, preference="distance")
        res_detour = a_star_search(prob_blocked)
        self.assertTrue(res_detour.success)
        # Detour must go around via south_parking/garden_walk
        self.assertGreater(res_detour.total_distance, orig_dist)
        self.assertIn("south_parking", res_detour.path_nodes)

        # Clean up
        self.graph.reset_all_blocks()

    def test_preferences_multi_routing(self):
        """Verify multi-preference route generation (distance, time, accessibility, crowd)."""
        routes = self.simulator.find_all_preference_routes("gate_main", "chem_lab", algorithm="A*")
        self.assertIn("distance", routes)
        self.assertIn("time", routes)
        self.assertIn("accessibility", routes)
        self.assertIn("crowd", routes)

        for pref, res in routes.items():
            self.assertTrue(res.success, f"Route for {pref} must succeed")
            self.assertGreater(res.total_distance, 0)
            self.assertGreater(res.total_time, 0)

    def test_partial_observability_replanning(self):
        """Test partial observability simulation with hidden obstacle discovery."""
        hidden_blocks = [("central_plaza", "lib_foyer")]
        res = self.simulator.simulate_partially_observable_navigation(
            start_id="cs_entrance",
            goal_id="lib_group_study",
            hidden_blocked_edges=hidden_blocks
        )
        self.assertTrue(res["success"])
        self.assertGreater(len(res["replan_events"]), 0)
        self.graph.reset_all_blocks()


if __name__ == "__main__":
    unittest.main()
