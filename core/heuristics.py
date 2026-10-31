"""
Admissible and Consistent Heuristic functions for A* Search.
Ensures h(n) <= h*(n) (never overestimates the true remaining cost to goal).
"""

import math
from typing import Callable
from core.state_action import CampusState

# Campus coordinate scale factor: DIT University compact 21-acre campus space (~0.28m per pixel)
PIXEL_TO_METERS = 0.28

# Maximum walking/sprinting speed in m/s used for admissible time lower-bound
MAX_CAMPUS_SPEED = 2.0  # m/s


def euclidean_distance(state: CampusState, goal: CampusState) -> float:
    """
    Straight-line Euclidean distance in meters.
    Admissible and consistent for physical 2D navigation (triangle inequality holds).
    """
    dx = (state.x - goal.x) * PIXEL_TO_METERS
    dy = (state.y - goal.y) * PIXEL_TO_METERS
    # Vertical floor difference penalty (estimated 4 meters per floor)
    floor_diff = abs(state.floor - goal.floor) * 4.0
    return math.hypot(dx, dy, floor_diff)


def manhattan_distance(state: CampusState, goal: CampusState) -> float:
    """
    L1 Manhattan distance in meters.
    Useful for orthogonal indoor hallway layouts.
    """
    dx = abs(state.x - goal.x) * PIXEL_TO_METERS
    dy = abs(state.y - goal.y) * PIXEL_TO_METERS
    floor_diff = abs(state.floor - goal.floor) * 4.0
    return dx + dy + floor_diff


def estimated_travel_time(state: CampusState, goal: CampusState) -> float:
    """
    Admissible lower bound for travel time in seconds.
    h(n) = euclidean_distance / MAX_CAMPUS_SPEED.
    Because true travel time = distance / effective_speed, and effective_speed <= MAX_CAMPUS_SPEED,
    this heuristic strictly never overestimates actual travel time.
    """
    dist = euclidean_distance(state, goal)
    return dist / MAX_CAMPUS_SPEED


def get_heuristic_function(heuristic_type: str, goal_state: CampusState, preference: str = "distance") -> Callable[[CampusState], float]:
    """
    Returns an appropriate heuristic function h(state) for A* search based on preference and type.
    """
    heuristic_type = heuristic_type.lower()
    preference = preference.lower()

    if preference == "time" or heuristic_type == "time":
        return lambda s: estimated_travel_time(s, goal_state)
    elif heuristic_type == "manhattan":
        return lambda s: manhattan_distance(s, goal_state)
    elif heuristic_type == "zero" or heuristic_type == "dijkstra":
        # Zero heuristic turns A* into Dijkstra / Uniform Cost Search
        return lambda s: 0.0
    else:
        # Default: Euclidean distance
        return lambda s: euclidean_distance(s, goal_state)
