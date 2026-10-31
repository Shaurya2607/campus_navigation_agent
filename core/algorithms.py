"""
Search Algorithms for Campus Navigation.
Implements:
  1. Breadth-First Search (BFS) - Uninformed FIFO queue search (finds fewest hops)
  2. Depth-First Search (DFS) - Uninformed LIFO stack search (deep path exploration)
  3. A* Search (Distance / Time heuristics) - Informed best-first search (f = g + h)
  4. Uniform Cost Search / Dijkstra - Optimal lowest-cost search (f = g)
  5. Greedy Best-First Search - Heuristic-only guided search (f = h)

Provides complete step-by-step logging of:
  - Current node evaluated
  - Open list (Frontier) contents with f, g, h values
  - Closed list (Explored set) contents
  - Step transitions, path costs, and final path reconstruction.
"""

from collections import deque
import heapq
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict

from core.graph import CampusGraph
from core.state_action import CampusProblem, CampusState, CampusAction
from core.heuristics import get_heuristic_function


@dataclass
class SearchStep:
    """Represents a single step in the algorithm's execution for visualization."""
    step_number: int
    current_node: str
    current_name: str
    action_taken: Optional[str]
    current_cost: float
    open_list: List[Dict[str, Any]]   # Snapshot of frontier nodes
    closed_list: List[str]            # Snapshot of explored node IDs
    f_val: float = 0.0
    g_val: float = 0.0
    h_val: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PathSegment:
    """Detailed information for each hop in the final route."""
    from_id: str
    from_name: str
    to_id: str
    to_name: str
    path_type: str
    distance: float
    travel_time: float
    accessible: bool
    crowd_level: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SearchResult:
    """Complete result returned by any search algorithm."""
    algorithm: str
    success: bool
    start_id: str
    goal_id: str
    total_cost: float
    total_distance: float
    total_time: float
    all_accessible: bool
    max_crowd_level: float
    path_nodes: List[str]
    path_segments: List[PathSegment]
    steps: List[SearchStep]
    nodes_expanded: int
    max_frontier_size: int
    execution_time_ms: float
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "success": self.success,
            "start_id": self.start_id,
            "goal_id": self.goal_id,
            "total_cost": round(self.total_cost, 2),
            "total_distance": round(self.total_distance, 1),
            "total_time": round(self.total_time, 1),
            "all_accessible": self.all_accessible,
            "max_crowd_level": round(self.max_crowd_level, 2),
            "path_nodes": self.path_nodes,
            "path_segments": [s.to_dict() for s in self.path_segments],
            "steps": [st.to_dict() for st in self.steps],
            "nodes_expanded": self.nodes_expanded,
            "max_frontier_size": self.max_frontier_size,
            "execution_time_ms": round(self.execution_time_ms, 3),
            "steps_count": int(round(self.total_distance / 0.75)),
            "calories_burned": round(self.total_distance * 0.045 + (sum(1 for s in self.path_segments if s.path_type == "stairs") * 4.0), 1),
            "error_message": self.error_message
        }


def _reconstruct_path(came_from: Dict[str, Tuple[str, CampusAction]], goal_id: str,
                      start_id: str, graph: CampusGraph) -> Tuple[List[str], List[PathSegment], float, float, bool, float]:
    """Reconstructs path from goal to start following came_from pointers."""
    if goal_id not in came_from and goal_id != start_id:
        return [], [], 0.0, 0.0, True, 1.0

    curr = goal_id
    path_nodes = [curr]
    actions_reversed = []

    while curr != start_id:
        prev, action = came_from[curr]
        actions_reversed.append(action)
        curr = prev
        path_nodes.append(curr)

    path_nodes.reverse()
    actions_reversed.reverse()

    segments = []
    total_distance = 0.0
    total_time = 0.0
    all_accessible = True
    max_crowd = 1.0

    for act in actions_reversed:
        from_n = graph.get_node(act.from_node_id)
        to_n = graph.get_node(act.to_node_id)
        segments.append(PathSegment(
            from_id=act.from_node_id,
            from_name=from_n.name if from_n else act.from_node_id,
            to_id=act.to_node_id,
            to_name=to_n.name if to_n else act.to_node_id,
            path_type=act.path_type,
            distance=act.distance,
            travel_time=act.travel_time,
            accessible=act.accessible,
            crowd_level=act.crowd_level
        ))
        total_distance += act.distance
        total_time += act.travel_time
        if not act.accessible:
            all_accessible = False
        if act.crowd_level > max_crowd:
            max_crowd = act.crowd_level

    return path_nodes, segments, total_distance, total_time, all_accessible, max_crowd


# ==========================================
# 1. Breadth-First Search (BFS)
# ==========================================
def breadth_first_search(problem: CampusProblem, max_steps: int = 2000) -> SearchResult:
    """
    Breadth-First Search: Explores shallowest nodes first using a FIFO queue.
    Optimal for uniform step costs (e.g., minimum hops).
    """
    start_time = time.perf_counter()
    start_state = problem.initial_state
    goal_id = problem.goal_state.node_id
    graph = problem.graph

    if problem.is_goal(start_state):
        return SearchResult(
            algorithm="BFS",
            success=True,
            start_id=start_state.node_id,
            goal_id=goal_id,
            total_cost=0.0,
            total_distance=0.0,
            total_time=0.0,
            all_accessible=True,
            max_crowd_level=1.0,
            path_nodes=[start_state.node_id],
            path_segments=[],
            steps=[],
            nodes_expanded=0,
            max_frontier_size=1,
            execution_time_ms=(time.perf_counter() - start_time) * 1000.0
        )

    # FIFO queue of tuples: (state, cumulative_cost)
    frontier = deque([start_state])
    frontier_set = {start_state.node_id}
    explored = set()
    came_from: Dict[str, Tuple[str, CampusAction]] = {}
    g_costs = {start_state.node_id: 0.0}

    steps: List[SearchStep] = []
    step_num = 0
    max_frontier_size = 1

    while frontier and step_num < max_steps:
        step_num += 1
        current_state = frontier.popleft()
        current_id = current_state.node_id
        frontier_set.discard(current_id)
        explored.add(current_id)

        # Snapshot open list for UI
        open_list_snapshot = [{"id": s.node_id, "name": s.name, "g": round(g_costs.get(s.node_id, 0), 1)} for s in frontier]
        steps.append(SearchStep(
            step_number=step_num,
            current_node=current_id,
            current_name=current_state.name,
            action_taken=f"Expanded {current_state.name}",
            current_cost=round(g_costs.get(current_id, 0.0), 1),
            open_list=open_list_snapshot,
            closed_list=list(explored),
            g_val=round(g_costs.get(current_id, 0.0), 1)
        ))

        if current_id == goal_id:
            path_nodes, segments, dist, t_time, acc, crowd = _reconstruct_path(came_from, goal_id, start_state.node_id, graph)
            return SearchResult(
                algorithm="BFS",
                success=True,
                start_id=start_state.node_id,
                goal_id=goal_id,
                total_cost=g_costs[goal_id],
                total_distance=dist,
                total_time=t_time,
                all_accessible=acc,
                max_crowd_level=crowd,
                path_nodes=path_nodes,
                path_segments=segments,
                steps=steps,
                nodes_expanded=len(explored),
                max_frontier_size=max_frontier_size,
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0
            )

        for action in problem.get_actions(current_state):
            child_state = problem.result(current_state, action)
            child_id = child_state.node_id
            step_c = problem.step_cost(current_state, action)

            if child_id not in explored and child_id not in frontier_set:
                came_from[child_id] = (current_id, action)
                g_costs[child_id] = g_costs[current_id] + step_c
                frontier.append(child_state)
                frontier_set.add(child_id)
                if len(frontier) > max_frontier_size:
                    max_frontier_size = len(frontier)

    # No path found
    return SearchResult(
        algorithm="BFS",
        success=False,
        start_id=start_state.node_id,
        goal_id=goal_id,
        total_cost=0.0,
        total_distance=0.0,
        total_time=0.0,
        all_accessible=True,
        max_crowd_level=1.0,
        path_nodes=[],
        path_segments=[],
        steps=steps,
        nodes_expanded=len(explored),
        max_frontier_size=max_frontier_size,
        execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
        error_message="No pathway exists between source and destination (all connecting paths may be blocked)."
    )


# ==========================================
# 2. Depth-First Search (DFS)
# ==========================================
def depth_first_search(problem: CampusProblem, max_steps: int = 2000) -> SearchResult:
    """
    Depth-First Search: Explores deepest node in frontier using a LIFO stack.
    Not guaranteed to find shortest or lowest cost path, but explores deep branches.
    """
    start_time = time.perf_counter()
    start_state = problem.initial_state
    goal_id = problem.goal_state.node_id
    graph = problem.graph

    if problem.is_goal(start_state):
        return SearchResult(
            algorithm="DFS",
            success=True,
            start_id=start_state.node_id,
            goal_id=goal_id,
            total_cost=0.0,
            total_distance=0.0,
            total_time=0.0,
            all_accessible=True,
            max_crowd_level=1.0,
            path_nodes=[start_state.node_id],
            path_segments=[],
            steps=[],
            nodes_expanded=0,
            max_frontier_size=1,
            execution_time_ms=(time.perf_counter() - start_time) * 1000.0
        )

    # LIFO stack
    stack = [start_state]
    frontier_set = {start_state.node_id}
    explored = set()
    came_from: Dict[str, Tuple[str, CampusAction]] = {}
    g_costs = {start_state.node_id: 0.0}

    steps: List[SearchStep] = []
    step_num = 0
    max_frontier_size = 1

    while stack and step_num < max_steps:
        step_num += 1
        current_state = stack.pop()
        current_id = current_state.node_id
        frontier_set.discard(current_id)
        explored.add(current_id)

        open_list_snapshot = [{"id": s.node_id, "name": s.name, "g": round(g_costs.get(s.node_id, 0), 1)} for s in reversed(stack)]
        steps.append(SearchStep(
            step_number=step_num,
            current_node=current_id,
            current_name=current_state.name,
            action_taken=f"Expanded {current_state.name} (LIFO)",
            current_cost=round(g_costs.get(current_id, 0.0), 1),
            open_list=open_list_snapshot,
            closed_list=list(explored),
            g_val=round(g_costs.get(current_id, 0.0), 1)
        ))

        if current_id == goal_id:
            path_nodes, segments, dist, t_time, acc, crowd = _reconstruct_path(came_from, goal_id, start_state.node_id, graph)
            return SearchResult(
                algorithm="DFS",
                success=True,
                start_id=start_state.node_id,
                goal_id=goal_id,
                total_cost=g_costs[goal_id],
                total_distance=dist,
                total_time=t_time,
                all_accessible=acc,
                max_crowd_level=crowd,
                path_nodes=path_nodes,
                path_segments=segments,
                steps=steps,
                nodes_expanded=len(explored),
                max_frontier_size=max_frontier_size,
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0
            )

        for action in problem.get_actions(current_state):
            child_state = problem.result(current_state, action)
            child_id = child_state.node_id
            step_c = problem.step_cost(current_state, action)

            if child_id not in explored and child_id not in frontier_set:
                came_from[child_id] = (current_id, action)
                g_costs[child_id] = g_costs[current_id] + step_c
                stack.append(child_state)
                frontier_set.add(child_id)
                if len(stack) > max_frontier_size:
                    max_frontier_size = len(stack)

    return SearchResult(
        algorithm="DFS",
        success=False,
        start_id=start_state.node_id,
        goal_id=goal_id,
        total_cost=0.0,
        total_distance=0.0,
        total_time=0.0,
        all_accessible=True,
        max_crowd_level=1.0,
        path_nodes=[],
        path_segments=[],
        steps=steps,
        nodes_expanded=len(explored),
        max_frontier_size=max_frontier_size,
        execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
        error_message="No pathway found using DFS."
    )


# ==========================================
# 3. A* Search (A-Star) & Dijkstra
# ==========================================
def a_star_search(problem: CampusProblem, heuristic_type: str = "euclidean",
                  max_steps: int = 2000) -> SearchResult:
    """
    A* Search: Best-first search evaluating f(n) = g(n) + h(n).
    Guarantees optimal path when heuristic is admissible and consistent.
    """
    start_time = time.perf_counter()
    start_state = problem.initial_state
    goal_state = problem.goal_state
    goal_id = goal_state.node_id
    graph = problem.graph

    h_fn = get_heuristic_function(heuristic_type, goal_state, problem.preference)

    # Priority queue storing: (f_score, tie_breaker, state)
    counter = 0
    initial_h = h_fn(start_state)
    frontier = []
    heapq.heappush(frontier, (initial_h, counter, start_state))

    g_score: Dict[str, float] = {start_state.node_id: 0.0}
    f_score: Dict[str, float] = {start_state.node_id: initial_h}
    came_from: Dict[str, Tuple[str, CampusAction]] = {}
    explored: Set[str] = set()

    steps: List[SearchStep] = []
    step_num = 0
    max_frontier_size = 1

    while frontier and step_num < max_steps:
        step_num += 1
        current_f, _, current_state = heapq.heappop(frontier)
        current_id = current_state.node_id

        if current_id in explored:
            continue

        explored.add(current_id)
        current_g = g_score[current_id]
        current_h = h_fn(current_state)

        # Snapshot frontier for live UI inspection
        open_list_snapshot = [
            {
                "id": s.node_id,
                "name": s.name,
                "f": round(f_val, 1),
                "g": round(g_score.get(s.node_id, 0.0), 1),
                "h": round(h_fn(s), 1)
            }
            for (f_val, _, s) in sorted(frontier, key=lambda x: x[0])[:15] # Top 15 in priority
        ]

        steps.append(SearchStep(
            step_number=step_num,
            current_node=current_id,
            current_name=current_state.name,
            action_taken=f"Selected {current_state.name} with min f={current_f:.1f}",
            current_cost=round(current_g, 1),
            open_list=open_list_snapshot,
            closed_list=list(explored),
            f_val=round(current_f, 1),
            g_val=round(current_g, 1),
            h_val=round(current_h, 1)
        ))

        # Goal check
        if current_id == goal_id:
            path_nodes, segments, dist, t_time, acc, crowd = _reconstruct_path(came_from, goal_id, start_state.node_id, graph)
            algo_name = "Dijkstra" if heuristic_type == "zero" else f"A* ({heuristic_type.title()})"
            return SearchResult(
                algorithm=algo_name,
                success=True,
                start_id=start_state.node_id,
                goal_id=goal_id,
                total_cost=g_score[goal_id],
                total_distance=dist,
                total_time=t_time,
                all_accessible=acc,
                max_crowd_level=crowd,
                path_nodes=path_nodes,
                path_segments=segments,
                steps=steps,
                nodes_expanded=len(explored),
                max_frontier_size=max_frontier_size,
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0
            )

        for action in problem.get_actions(current_state):
            neighbor_state = problem.result(current_state, action)
            neighbor_id = neighbor_state.node_id

            if neighbor_id in explored:
                continue

            tentative_g = current_g + problem.step_cost(current_state, action)

            if tentative_g < g_score.get(neighbor_id, float('inf')):
                came_from[neighbor_id] = (current_id, action)
                g_score[neighbor_id] = tentative_g
                h_val = h_fn(neighbor_state)
                neighbor_f = tentative_g + h_val
                f_score[neighbor_id] = neighbor_f

                counter += 1
                heapq.heappush(frontier, (neighbor_f, counter, neighbor_state))
                if len(frontier) > max_frontier_size:
                    max_frontier_size = len(frontier)

    algo_name = "Dijkstra" if heuristic_type == "zero" else f"A* ({heuristic_type.title()})"
    return SearchResult(
        algorithm=algo_name,
        success=False,
        start_id=start_state.node_id,
        goal_id=goal_id,
        total_cost=0.0,
        total_distance=0.0,
        total_time=0.0,
        all_accessible=True,
        max_crowd_level=1.0,
        path_nodes=[],
        path_segments=[],
        steps=steps,
        nodes_expanded=len(explored),
        max_frontier_size=max_frontier_size,
        execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
        error_message="No accessible path found between selected campus locations."
    )


# ==========================================
# 4. Greedy Best-First Search
# ==========================================
def greedy_best_first_search(problem: CampusProblem, heuristic_type: str = "euclidean",
                             max_steps: int = 2000) -> SearchResult:
    """
    Greedy Best-First Search: Evaluates nodes purely by heuristic value f(n) = h(n).
    Fast in unobstructed space, but can be misled by obstacles into sub-optimal routes.
    """
    start_time = time.perf_counter()
    start_state = problem.initial_state
    goal_state = problem.goal_state
    goal_id = goal_state.node_id
    graph = problem.graph

    h_fn = get_heuristic_function(heuristic_type, goal_state, problem.preference)

    counter = 0
    initial_h = h_fn(start_state)
    frontier = []
    heapq.heappush(frontier, (initial_h, counter, start_state))

    g_score = {start_state.node_id: 0.0}
    came_from: Dict[str, Tuple[str, CampusAction]] = {}
    explored: Set[str] = set()

    steps: List[SearchStep] = []
    step_num = 0
    max_frontier_size = 1

    while frontier and step_num < max_steps:
        step_num += 1
        current_h, _, current_state = heapq.heappop(frontier)
        current_id = current_state.node_id

        if current_id in explored:
            continue

        explored.add(current_id)
        current_g = g_score.get(current_id, 0.0)

        open_list_snapshot = [
            {"id": s.node_id, "name": s.name, "h": round(h_val, 1)}
            for (h_val, _, s) in sorted(frontier, key=lambda x: x[0])[:15]
        ]

        steps.append(SearchStep(
            step_number=step_num,
            current_node=current_id,
            current_name=current_state.name,
            action_taken=f"Greedy expand {current_state.name} (h={current_h:.1f})",
            current_cost=round(current_g, 1),
            open_list=open_list_snapshot,
            closed_list=list(explored),
            f_val=round(current_h, 1),
            g_val=round(current_g, 1),
            h_val=round(current_h, 1)
        ))

        if current_id == goal_id:
            path_nodes, segments, dist, t_time, acc, crowd = _reconstruct_path(came_from, goal_id, start_state.node_id, graph)
            return SearchResult(
                algorithm="Greedy Best-First",
                success=True,
                start_id=start_state.node_id,
                goal_id=goal_id,
                total_cost=g_score[goal_id],
                total_distance=dist,
                total_time=t_time,
                all_accessible=acc,
                max_crowd_level=crowd,
                path_nodes=path_nodes,
                path_segments=segments,
                steps=steps,
                nodes_expanded=len(explored),
                max_frontier_size=max_frontier_size,
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0
            )

        for action in problem.get_actions(current_state):
            neighbor_state = problem.result(current_state, action)
            neighbor_id = neighbor_state.node_id

            if neighbor_id not in explored:
                step_c = problem.step_cost(current_state, action)
                if neighbor_id not in g_score:
                    g_score[neighbor_id] = current_g + step_c
                    came_from[neighbor_id] = (current_id, action)
                    h_val = h_fn(neighbor_state)
                    counter += 1
                    heapq.heappush(frontier, (h_val, counter, neighbor_state))
                    if len(frontier) > max_frontier_size:
                        max_frontier_size = len(frontier)

    return SearchResult(
        algorithm="Greedy Best-First",
        success=False,
        start_id=start_state.node_id,
        goal_id=goal_id,
        total_cost=0.0,
        total_distance=0.0,
        total_time=0.0,
        all_accessible=True,
        max_crowd_level=1.0,
        path_nodes=[],
        path_segments=[],
        steps=steps,
        nodes_expanded=len(explored),
        max_frontier_size=max_frontier_size,
        execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
        error_message="No path found using Greedy Best-First Search."
    )


def run_algorithm(algo_name: str, problem: CampusProblem, heuristic: str = "euclidean") -> SearchResult:
    """Master dispatcher to run the requested algorithm."""
    algo = algo_name.lower()
    if algo == "bfs":
        return breadth_first_search(problem)
    elif algo == "dfs":
        return depth_first_search(problem)
    elif algo in ("a*", "astar", "a_star"):
        return a_star_search(problem, heuristic_type=heuristic)
    elif algo in ("dijkstra", "ucs"):
        return a_star_search(problem, heuristic_type="zero")
    elif algo in ("greedy", "greedy_best_first"):
        return greedy_best_first_search(problem, heuristic_type=heuristic)
    else:
        raise ValueError(f"Unknown algorithm '{algo_name}'. Choose BFS, DFS, A*, Dijkstra, or Greedy.")


def find_nearest_facility(graph: CampusGraph, start_id: str, facility_type: str, preference: str = "distance") -> Optional[SearchResult]:
    """
    Finds the optimal route to the nearest facility of a given type from the start location.
    Supported types: 'food', 'medical', 'atm', 'lab', 'library', 'gate'
    """
    TYPE_TARGETS = {
        "food": ["cafeteria_main", "night_canteen"],
        "medical": ["health_center", "pharmacy", "ambulance_bay"],
        "atm": ["bank_atm"],
        "lab": ["cs_lab_ai", "cs_lab_cyber", "ee_circuits_lab", "mech_workshop", "chem_lab", "physics_lab", "maker_space", "fintech_lab"],
        "library": ["lib_foyer", "lib_group_study", "lib_quiet_hall", "bookstore"],
        "gate": ["gate_main", "gate_north"],
    }
    targets = TYPE_TARGETS.get(facility_type.lower(), [])
    if not targets:
        targets = [nid for nid, n in graph.nodes.items() if n.category.lower() == facility_type.lower()]

    if not targets:
        return None

    viable_targets = [t for t in targets if t in graph.nodes and not graph.nodes[t].is_blocked and t != start_id]
    if not viable_targets:
        viable_targets = [t for t in targets if t in graph.nodes and not graph.nodes[t].is_blocked]

    results = []
    for tgt in viable_targets:
        prob = CampusProblem(graph, start_id, tgt, preference=preference)
        res = a_star_search(prob)
        if res.success:
            results.append(res)

    if not results:
        return None

    return min(results, key=lambda r: r.total_cost)


def find_multi_stop_route(graph: CampusGraph, start_id: str, via_id: str, goal_id: str, algorithm: str = "A*", preference: str = "distance") -> SearchResult:
    """
    Computes a compound route through an intermediate waypoint: start -> via -> goal.
    """
    prob1 = CampusProblem(graph, start_id, via_id, preference=preference)
    res1 = run_algorithm(algorithm, prob1)
    if not res1.success:
        return res1

    prob2 = CampusProblem(graph, via_id, goal_id, preference=preference)
    res2 = run_algorithm(algorithm, prob2)
    if not res2.success:
        return res2

    combined_nodes = res1.path_nodes + res2.path_nodes[1:]
    combined_segments = res1.path_segments + res2.path_segments
    combined_steps = res1.steps + [
        SearchStep(
            step_number=len(res1.steps) + st.step_number,
            current_node=st.current_node,
            current_name=st.current_name,
            action_taken=st.action_taken,
            current_cost=round(res1.total_cost + st.current_cost, 2),
            open_list=st.open_list,
            closed_list=res1.steps[-1].closed_list + st.closed_list if res1.steps else st.closed_list,
            f_val=round(st.f_val + res1.total_cost, 2),
            g_val=round(st.g_val + res1.total_cost, 2),
            h_val=st.h_val
        )
        for st in res2.steps
    ]

    return SearchResult(
        algorithm=f"{algorithm} (via {graph.nodes[via_id].name if via_id in graph.nodes else via_id})",
        success=True,
        start_id=start_id,
        goal_id=goal_id,
        total_cost=round(res1.total_cost + res2.total_cost, 2),
        total_distance=round(res1.total_distance + res2.total_distance, 1),
        total_time=round(res1.total_time + res2.total_time, 1),
        all_accessible=res1.all_accessible and res2.all_accessible,
        max_crowd_level=max(res1.max_crowd_level, res2.max_crowd_level),
        path_nodes=combined_nodes,
        path_segments=combined_segments,
        steps=combined_steps,
        nodes_expanded=res1.nodes_expanded + res2.nodes_expanded,
        max_frontier_size=max(res1.max_frontier_size, res2.max_frontier_size),
        execution_time_ms=round(res1.execution_time_ms + res2.execution_time_ms, 3)
    )
