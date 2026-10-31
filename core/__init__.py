"""
Campus Navigation Agent Core Package.
"""

from core.graph import CampusGraph, CampusNode, CampusEdge, create_default_campus_graph
from core.state_action import CampusState, CampusAction, CampusProblem
from core.heuristics import euclidean_distance, manhattan_distance, estimated_travel_time
from core.algorithms import (
    breadth_first_search,
    depth_first_search,
    a_star_search,
    greedy_best_first_search,
    run_algorithm,
    SearchResult,
    SearchStep
)
from core.environment import (
    get_peas_description,
    get_environment_classifications,
    CampusEnvironmentSimulator
)

__all__ = [
    "CampusGraph",
    "CampusNode",
    "CampusEdge",
    "create_default_campus_graph",
    "CampusState",
    "CampusAction",
    "CampusProblem",
    "euclidean_distance",
    "manhattan_distance",
    "estimated_travel_time",
    "breadth_first_search",
    "depth_first_search",
    "a_star_search",
    "greedy_best_first_search",
    "run_algorithm",
    "SearchResult",
    "SearchStep",
    "get_peas_description",
    "get_environment_classifications",
    "CampusEnvironmentSimulator"
]
