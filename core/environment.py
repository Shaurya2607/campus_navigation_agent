"""
Environment Model & Classification for the Intelligent Campus Navigation Agent.
Provides:
  1. Formal PEAS (Performance, Environment, Actuators, Sensors) analysis.
  2. Theoretical Environment Classification (Observable, Deterministic, Sequential, Dynamic, etc.).
  3. Interactive Simulation Engine supporting:
     - Full vs. Partial Observability (Sensor range / Fog of War & dynamic replanning)
     - Deterministic vs. Stochastic transitions (random delays, stochastic blockages)
     - Dynamic events (rush hour crowd surges, pop-up maintenance blocks)
     - Multiple route comparison & ranking (Distance, Time, Accessibility, Crowd Level).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import random
import math

from core.graph import CampusGraph, CampusNode, CampusEdge
from core.state_action import CampusProblem, CampusState
from core.algorithms import run_algorithm, SearchResult


@dataclass
class EnvironmentClassification:
    """Detailed structural classification of the campus navigation environment."""
    dimension: str
    classification: str
    explanation: str
    agent_implication: str


def get_peas_description() -> Dict[str, Any]:
    """Returns the formal PEAS description of the campus navigation agent."""
    return {
        "Performance_Measure": [
            "Minimize total travel time (seconds) and physical distance (meters).",
            "100% adherence to mobility/accessibility constraints (zero wheelchair stair violations).",
            "Avoidance of congested corridors, high crowd density, and safety hazards.",
            "Algorithm efficiency: minimal node expansions and fastest computational execution time."
        ],
        "Environment": [
            "University campus spanning indoor academic blocks, labs, offices, and outdoor pathways.",
            "Multi-floor buildings connected by stairs and elevators.",
            "Dynamic obstacles: construction closures, maintenance, emergency cordons, class transitions."
        ],
        "Actuators": [
            "Move along path to adjacent location (walkway, hallway, stairs, elevator).",
            "Select alternative path when an obstacle is encountered.",
            "Issue turn-by-turn navigation instructions and route updates to user."
        ],
        "Sensors": [
            "Location positioning (Campus Wi-Fi triangulation / indoor BLE beacons / GPS).",
            "Campus Facility Monitoring API (live status of doors, elevators, maintenance).",
            "Crowd density estimation (Wi-Fi access point device count, camera analytics)."
        ]
    }


def get_environment_classifications() -> List[Dict[str, str]]:
    """Returns the theoretical classification across the 6 Russell & Norvig dimensions."""
    return [
        {
            "dimension": "Observability",
            "type": "Fully Observable (Nominal) / Partially Observable (Real-world)",
            "details": "With access to the central campus GIS database, the agent has complete graph knowledge. In real deployment, local disruptions (e.g. locked doors, temporary spills) are only detected when the agent enters sensor range, requiring dynamic re-planning.",
            "badge": "Fully / Partially Observable"
        },
        {
            "dimension": "Determinism",
            "type": "Deterministic (Nominal) / Stochastic (Crowd & Transit)",
            "details": "Traversing edge (u, v) deterministically leads to state v. However, actual travel time is stochastic due to elevator door cycles, human walking variations, and spontaneous corridor congestion.",
            "badge": "Deterministic / Stochastic"
        },
        {
            "dimension": "Temporality",
            "type": "Sequential",
            "details": "Every navigational decision directly dictates subsequent available actions, accumulated path cost, and spatial location. Past choices constrain future state space.",
            "badge": "Sequential"
        },
        {
            "dimension": "Dynamics",
            "type": "Dynamic",
            "details": "The campus changes continuously while the agent is planning and traveling. Class bells trigger sudden surges in hallways, cafeteria lines spike at noon, and maintenance teams can close hallways mid-journey.",
            "badge": "Dynamic"
        },
        {
            "dimension": "Discreteness",
            "type": "Discrete",
            "details": "The state space is partitioned into discrete navigational waypoints (classrooms, junctions, offices) connected by discrete topological actions.",
            "badge": "Discrete"
        },
        {
            "dimension": "Agency",
            "type": "Single-Agent (Navigating) with Multi-Agent Background",
            "details": "The navigation agent acts autonomously to find the optimal path, treating other human pedestrians as dynamic environment elements / crowd density factors.",
            "badge": "Single-Agent"
        }
    ]


class CampusEnvironmentSimulator:
    """
    Simulates dynamic campus environment conditions:
      - Dynamic crowd fluctuations (e.g., peak rush hour)
      - Dynamic obstacle generation (e.g., sudden maintenance)
      - Partial observability with sensor horizon & replanning
      - Multi-preference route generation (Distance, Time, Accessibility, Crowd)
    """
    def __init__(self, graph: CampusGraph):
        self.graph = graph
        self.sensor_radius_meters = 60.0  # Sensor horizon for partially observable mode
        self.dynamic_events: List[str] = []

    def simulate_rush_hour(self, active: bool = True) -> None:
        """Simulate peak class-transition rush hour: heavily spikes cafeteria, quad, and hallway crowd levels."""
        crowd_factor = 2.5 if active else 1.0
        affected_areas = ["cafeteria_main", "central_plaza", "student_union", "cs_entrance", "fountain_cross"]

        for u in affected_areas:
            for edge in self.graph.edges.get(u, []):
                edge.crowd_level = round(edge.crowd_level * (1.8 if active else 0.55), 2)
                edge.crowd_level = max(1.0, min(3.5, edge.crowd_level))

        event_msg = "Rush hour crowd spike activated across central campus." if active else "Campus foot traffic normalized."
        self.dynamic_events.append(event_msg)

    def trigger_random_obstacle(self) -> Optional[str]:
        """Introduce a realistic random obstacle on a corridor."""
        candidates = []
        for u, edges in self.graph.edges.items():
            for edge in edges:
                if not edge.is_blocked and edge.source < edge.target:
                    candidates.append((edge.source, edge.target))

        if not candidates:
            return None

        u, v = random.choice(candidates)
        reasons = [
            "Floor waxing & maintenance underway",
            "Temporary emergency fire drill inspection",
            "Electrical conduit rewiring",
            "Water pipe leak maintenance"
        ]
        reason = random.choice(reasons)
        self.graph.set_edge_blocked(u, v, True, reason)
        event_str = f"Obstacle placed between {u} and {v}: {reason}"
        self.dynamic_events.append(event_str)
        return event_str

    def find_all_preference_routes(self, start_id: str, goal_id: str, algorithm: str = "A*") -> Dict[str, SearchResult]:
        """
        Generates 4 distinct route options according to user preferences:
          1. 'distance' - Shortest physical distance
          2. 'time' - Fastest estimated travel time
          3. 'accessibility' - 100% ADA wheelchair compliant (no stairs, only elevators/ramps)
          4. 'crowd' - Lowest crowd congestion (avoids packed halls and dining areas)
        """
        preferences = ["distance", "time", "accessibility", "crowd"]
        results = {}

        for pref in preferences:
            try:
                problem = CampusProblem(self.graph, start_id, goal_id, preference=pref, respect_blocks=True)
                heur = "time" if pref == "time" else "euclidean"
                res = run_algorithm(algorithm, problem, heuristic=heur)
                results[pref] = res
            except Exception as e:
                # In case of no path or error
                results[pref] = SearchResult(
                    algorithm=f"{algorithm} ({pref})",
                    success=False,
                    start_id=start_id,
                    goal_id=goal_id,
                    total_cost=0.0,
                    total_distance=0.0,
                    total_time=0.0,
                    all_accessible=False,
                    max_crowd_level=1.0,
                    path_nodes=[],
                    path_segments=[],
                    steps=[],
                    nodes_expanded=0,
                    max_frontier_size=0,
                    execution_time_ms=0.0,
                    error_message=str(e)
                )

        return results

    def simulate_partially_observable_navigation(self, start_id: str, goal_id: str,
                                                 hidden_blocked_edges: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Demonstrates Partial Observability & Online Replanning:
        Agent begins navigation with its known map. Hidden obstacles are ONLY discovered
        when the agent reaches a node directly incident to or within sensor range of the blocked edge.
        Upon discovering the obstacle, the agent recalculates a new route using A*.
        """
        agent_current = start_id
        full_traversed_path = [start_id]
        replan_events = []
        total_traveled_dist = 0.0
        total_traveled_time = 0.0

        # Temporarily clear hidden blocks from agent's initial belief state
        original_block_states = {}
        for (u, v) in hidden_blocked_edges:
            # Record true reality
            original_block_states[(u, v)] = True
            # In agent belief map, clear it initially
            self.graph.set_edge_blocked(u, v, False)

        # Agent plans initial path
        problem = CampusProblem(self.graph, agent_current, goal_id, preference="time")
        current_plan = run_algorithm("A*", problem)

        if not current_plan.success:
            return {"success": False, "message": "No initial path found."}

        planned_nodes = current_plan.path_nodes.copy()
        step_idx = 0

        while agent_current != goal_id and step_idx < len(planned_nodes) - 1:
            next_node = planned_nodes[step_idx + 1]

            # Check if edge (agent_current, next_node) is actually blocked in reality
            is_really_blocked = original_block_states.get((agent_current, next_node)) or original_block_states.get((next_node, agent_current))

            if is_really_blocked:
                # SENSOR TRIGGER: Agent discovers the blocked path at runtime!
                replan_events.append({
                    "event": "Obstacle Discovered",
                    "at_node": agent_current,
                    "blocked_edge": (agent_current, next_node),
                    "description": f"Agent arrived at {agent_current} and detected hallway to {next_node} is blocked!"
                })
                # Update belief map: mark edge blocked
                self.graph.set_edge_blocked(agent_current, next_node, True, "Discovered during navigation")

                # RE-PLAN from current location to goal
                replan_problem = CampusProblem(self.graph, agent_current, goal_id, preference="time")
                new_plan = run_algorithm("A*", replan_problem)

                if not new_plan.success:
                    return {
                        "success": False,
                        "traversed_path": full_traversed_path,
                        "replan_events": replan_events,
                        "message": f"Trapped at {agent_current}. All detour routes are blocked."
                    }

                replan_events.append({
                    "event": "Replanned Route",
                    "new_path": new_plan.path_nodes,
                    "added_cost": new_plan.total_cost
                })
                planned_nodes = new_plan.path_nodes
                step_idx = 0
                continue

            # Move along the edge
            for seg in current_plan.path_segments:
                if seg.from_id == agent_current and seg.to_id == next_node:
                    total_traveled_dist += seg.distance
                    total_traveled_time += seg.travel_time
                    break

            agent_current = next_node
            full_traversed_path.append(agent_current)
            step_idx += 1

        return {
            "success": True,
            "final_traversed_path": full_traversed_path,
            "total_distance": round(total_traveled_dist, 1),
            "total_time": round(total_traveled_time, 1),
            "replan_events": replan_events
        }
