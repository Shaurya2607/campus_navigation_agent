"""
Formal AI State and Action representations for Campus Navigation.
Implements the Russell & Norvig problem formulation:
  - States: Campus locations (node id, building, floor, coordinate)
  - Actions: Traversing accessible pathways between locations
  - Transition Model: Result(state, action) -> new_state
  - Goal Test: IsGoal(state, goal_state) -> bool
  - Path Cost: StepCost(state, action, preference)
"""

from dataclasses import dataclass
from typing import List, Optional
from core.graph import CampusNode, CampusEdge, CampusGraph


@dataclass(frozen=True)
class CampusState:
    """Represents a state in the state space."""
    node_id: str
    name: str
    building: str
    floor: int
    x: float
    y: float

    @classmethod
    def from_node(cls, node: CampusNode) -> 'CampusState':
        return cls(
            node_id=node.id,
            name=node.name,
            building=node.building,
            floor=node.floor,
            x=node.x,
            y=node.y
        )

    def __repr__(self) -> str:
        return f"State({self.node_id} @ {self.building} F{self.floor})"


@dataclass(frozen=True)
class CampusAction:
    """Represents an action taken by the navigation agent."""
    from_node_id: str
    to_node_id: str
    path_type: str
    distance: float
    accessible: bool
    crowd_level: float
    travel_time: float

    @classmethod
    def from_edge(cls, edge: CampusEdge) -> 'CampusAction':
        return cls(
            from_node_id=edge.source,
            to_node_id=edge.target,
            path_type=edge.path_type,
            distance=edge.distance,
            accessible=edge.accessible,
            crowd_level=edge.crowd_level,
            travel_time=edge.travel_time
        )

    @property
    def name(self) -> str:
        return f"Move({self.from_node_id} -> {self.to_node_id} via {self.path_type})"


class CampusProblem:
    """
    Formal AI Search Problem formulation.
    Encapsulates Initial State, Actions, Transition Model, Goal Test, and Step Cost.
    """
    def __init__(self, graph: CampusGraph, start_node_id: str, goal_node_id: str,
                 preference: str = "distance", respect_blocks: bool = True):
        self.graph = graph
        self.start_node = graph.get_node(start_node_id)
        self.goal_node = graph.get_node(goal_node_id)
        if not self.start_node:
            raise ValueError(f"Start node '{start_node_id}' does not exist in graph.")
        if not self.goal_node:
            raise ValueError(f"Goal node '{goal_node_id}' does not exist in graph.")

        self.initial_state = CampusState.from_node(self.start_node)
        self.goal_state = CampusState.from_node(self.goal_node)
        self.preference = preference.lower()  # 'distance', 'time', 'accessibility', 'crowd'
        self.respect_blocks = respect_blocks

    def is_goal(self, state: CampusState) -> bool:
        """Goal test: determines if state reaches the target location."""
        return state.node_id == self.goal_state.node_id

    def get_actions(self, state: CampusState) -> List[CampusAction]:
        """Returns valid actions from the given state."""
        accessible_only = (self.preference == "accessibility")
        neighbors = self.graph.get_neighbors(
            state.node_id,
            respect_blocks=self.respect_blocks,
            accessible_only=accessible_only
        )
        return [CampusAction.from_edge(edge) for _, edge in neighbors]

    def result(self, state: CampusState, action: CampusAction) -> CampusState:
        """Transition model: returns the state that results from doing action in state."""
        if action.from_node_id != state.node_id:
            raise ValueError(f"Action {action} cannot be executed from state {state}")
        target_node = self.graph.get_node(action.to_node_id)
        if not target_node:
            raise ValueError(f"Target node '{action.to_node_id}' not found.")
        return CampusState.from_node(target_node)

    def step_cost(self, state: CampusState, action: CampusAction) -> float:
        """
        Calculates the step cost c(s, a, s') based on the chosen optimization criteria:
        - 'distance': Physical distance in meters
        - 'time': Estimated travel time in seconds (accounting for speed, stairs, crowd)
        - 'accessibility': Requires wheelchair-accessible paths; penalized if non-accessible
        - 'crowd': Heavily penalizes crowded corridors (distance * crowd_level^2)
        """
        if self.preference == "distance":
            return action.distance
        elif self.preference == "time":
            return action.travel_time
        elif self.preference == "accessibility":
            if not action.accessible:
                return float('inf')
            # For accessible paths, optimize for easy travel time
            return action.travel_time
        elif self.preference == "crowd":
            # Congestion multiplier: higher crowd levels get exponential penalty
            return action.distance * (action.crowd_level ** 2)
        elif self.preference in ("shelter", "rain"):
            # Rain Mode: heavily penalize open outdoor pathways, favoring indoor corridors & skybridges
            is_unsheltered = action.path_type in ("walkway", "plaza", "garden")
            penalty = 3.5 if is_unsheltered else 1.0
            return action.distance * penalty
        return action.distance
