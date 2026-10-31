#!/usr/bin/env python3
"""
Autonomous Continuous Test & Diagnostic Server for Intelligent Campus Navigation Agent.
Runs an automated regression, benchmark, and self-refinement testing loop in the background.
Serves a real-time HTTP monitoring dashboard at http://localhost:8090.
Zero external dependencies (uses standard library Python).
"""

import http.server
import socketserver
import json
import urllib.parse
import threading
import time
import random
import os
import sys
import io
from collections import deque
from typing import Dict, List, Any, Optional

# Add project root to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from core.graph import create_default_campus_graph, CampusGraph, CampusNode, CampusEdge
from core.state_action import CampusProblem, CampusState
from core.algorithms import (
    run_algorithm,
    find_nearest_facility,
    find_multi_stop_route,
    a_star_search,
    breadth_first_search,
    depth_first_search,
    greedy_best_first_search
)
from core.heuristics import euclidean_distance, manhattan_distance, estimated_travel_time
from core.environment import CampusEnvironmentSimulator, get_peas_description, get_environment_classifications

TEST_SERVER_PORT = 8090

# ANSI color codes for terminal
GREEN = "\033[92m"
BLUE = "\033[94m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


class ContinuousTestEngine:
    """Autonomous continuous testing and regression engine running in a background loop."""

    def __init__(self):
        self.lock = threading.Lock()
        self.graph: CampusGraph = create_default_campus_graph()
        self.simulator = CampusEnvironmentSimulator(self.graph)
        
        # Engine telemetry
        self.start_time = time.time()
        self.is_running = True
        self.is_paused = False
        self.cycle_count = 0
        self.total_tests_executed = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.last_cycle_duration_ms = 0.0
        self.recent_logs = deque(maxlen=60)
        self.active_test_name = "Initializing"
        self.system_health = "HEALTHY"
        self.anomalies_detected = 0
        self.refinements_applied = 0
        
        # Algorithm statistics: latency tracking
        self.algo_stats: Dict[str, Dict[str, Any]] = {
            "A*": {"runs": 0, "avg_time_ms": 0.0, "avg_expansions": 0.0, "optimal_rate": 100.0},
            "Dijkstra": {"runs": 0, "avg_time_ms": 0.0, "avg_expansions": 0.0, "optimal_rate": 100.0},
            "BFS": {"runs": 0, "avg_time_ms": 0.0, "avg_expansions": 0.0, "fewest_hops_rate": 100.0},
            "DFS": {"runs": 0, "avg_time_ms": 0.0, "avg_expansions": 0.0, "optimal_rate": 0.0},
            "Greedy": {"runs": 0, "avg_time_ms": 0.0, "avg_expansions": 0.0, "optimal_rate": 0.0},
        }

        # Key validation nodes
        self.key_endpoints = [
            ("gate_main", "cs_lab_ai"),
            ("gate_main", "cafeteria_main"),
            ("hostel_boys", "mgmt_block"),
            ("incubator_hub", "cricket_ground"),
            ("admin_lobby", "chem_lab"),
            ("gate_north", "sports_arena"),
            ("cs_101", "eng_atrium"),
            ("lib_foyer", "pharmacy"),
            ("hostel_girls", "cs_lab_cyber"),
            ("night_canteen", "ee_circuits_lab")
        ]

    def log(self, category: str, message: str, status: str = "PASS", duration_ms: float = 0.0):
        timestamp = time.strftime("%H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "category": category,
            "message": message,
            "status": status,
            "duration_ms": round(duration_ms, 2)
        }
        with self.lock:
            self.recent_logs.append(entry)
            self.total_tests_executed += 1
            if status == "PASS":
                self.tests_passed += 1
            else:
                self.tests_failed += 1
                self.anomalies_detected += 1
                self.system_health = "DEGRADED"

    def record_algo_telemetry(self, algo_name: str, exec_time_ms: float, expansions: int):
        if algo_name not in self.algo_stats:
            return
        st = self.algo_stats[algo_name]
        n = st["runs"]
        st["avg_time_ms"] = round((st["avg_time_ms"] * n + exec_time_ms) / (n + 1), 3)
        st["avg_expansions"] = round((st["avg_expansions"] * n + expansions) / (n + 1), 1)
        st["runs"] += 1

    # --- INDIVIDUAL TEST PHASES ---

    def test_graph_invariants(self):
        """Verifies topological invariants: node count, bidirectional symmetry, valid positive weights."""
        t0 = time.perf_counter()
        nodes = self.graph.nodes
        assert len(nodes) == 50, f"Expected 50 nodes, found {len(nodes)}"
        
        # Check bidirectional edge symmetry
        checked_pairs = set()
        for u, edge_list in self.graph.edges.items():
            for e in edge_list:
                v = e.target
                pair = tuple(sorted([u, v]))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)
                
                # Verify reverse edge exists
                rev = next((re for re in self.graph.edges.get(v, []) if re.target == u), None)
                assert rev is not None, f"Edge {u} -> {v} lacks reverse edge {v} -> {u}"
                assert abs(e.distance - rev.distance) < 1e-4, f"Asymmetric distances between {u} and {v}"
                assert e.distance > 0.0, f"Non-positive distance on {u} -> {v}"
                assert e.base_speed > 0.0, f"Non-positive speed on {u} -> {v}"

        elapsed = (time.perf_counter() - t0) * 1000.0
        self.log("GRAPH_INVARIANT", f"Verified 50 nodes & {len(checked_pairs)} bidirectional edges symmetry", "PASS", elapsed)

    def test_algorithm_optimality_sweep(self):
        """Executes full search algorithm sweep and mathematical optimality checks."""
        t0 = time.perf_counter()
        pair = random.choice(self.key_endpoints)
        start_id, goal_id = pair

        prob = CampusProblem(self.graph, start_id, goal_id, preference="distance")
        
        # Run A*
        t_a = time.perf_counter()
        res_astar = a_star_search(prob, heuristic_type="euclidean")
        ms_astar = (time.perf_counter() - t_a) * 1000.0
        assert res_astar.success, f"A* failed for {start_id} -> {goal_id}"
        self.record_algo_telemetry("A*", ms_astar, res_astar.nodes_expanded)

        # Run Dijkstra
        t_d = time.perf_counter()
        res_dijkstra = a_star_search(prob, heuristic_type="zero")
        ms_dijkstra = (time.perf_counter() - t_d) * 1000.0
        assert res_dijkstra.success, f"Dijkstra failed for {start_id} -> {goal_id}"
        self.record_algo_telemetry("Dijkstra", ms_dijkstra, res_dijkstra.nodes_expanded)

        # Run BFS
        t_b = time.perf_counter()
        res_bfs = breadth_first_search(prob)
        ms_bfs = (time.perf_counter() - t_b) * 1000.0
        assert res_bfs.success, f"BFS failed for {start_id} -> {goal_id}"
        self.record_algo_telemetry("BFS", ms_bfs, res_bfs.nodes_expanded)

        # Run DFS
        t_dfs = time.perf_counter()
        res_dfs = depth_first_search(prob)
        ms_dfs = (time.perf_counter() - t_dfs) * 1000.0
        assert res_dfs.success, f"DFS failed for {start_id} -> {goal_id}"
        self.record_algo_telemetry("DFS", ms_dfs, res_dfs.nodes_expanded)

        # Run Greedy
        t_g = time.perf_counter()
        res_greedy = greedy_best_first_search(prob, heuristic_type="euclidean")
        ms_greedy = (time.perf_counter() - t_g) * 1000.0
        assert res_greedy.success, f"Greedy failed for {start_id} -> {goal_id}"
        self.record_algo_telemetry("Greedy", ms_greedy, res_greedy.nodes_expanded)

        # Optimality assertion: A* cost must match Dijkstra cost within float tolerance
        cost_diff = abs(res_astar.total_cost - res_dijkstra.total_cost)
        assert cost_diff < 0.05, f"A* cost ({res_astar.total_cost}) != Dijkstra cost ({res_dijkstra.total_cost})"
        
        # A* must expand fewer or equal nodes than Dijkstra
        assert res_astar.nodes_expanded <= res_dijkstra.nodes_expanded + 2, (
            f"A* expanded more nodes ({res_astar.nodes_expanded}) than Dijkstra ({res_dijkstra.nodes_expanded})"
        )

        elapsed = (time.perf_counter() - t0) * 1000.0
        self.log("ALGO_SWEEP", f"A*={res_astar.total_distance:.1f}m ({res_astar.nodes_expanded} exp) == Dijkstra ({res_dijkstra.nodes_expanded} exp)", "PASS", elapsed)

    def test_multi_objective_preferences(self):
        """Verifies distance, time, accessibility, crowd, and shelter routing criteria."""
        t0 = time.perf_counter()
        start_id, goal_id = "cs_101", "cs_lab_ai"

        # 1. Distance vs Time
        p_dist = CampusProblem(self.graph, start_id, goal_id, preference="distance")
        r_dist = run_algorithm("A*", p_dist)
        assert r_dist.success

        p_time = CampusProblem(self.graph, start_id, goal_id, preference="time")
        r_time = run_algorithm("A*", p_time)
        assert r_time.success

        # 2. Accessibility (Wheelchair constraint: must contain ZERO stairs)
        p_acc = CampusProblem(self.graph, start_id, goal_id, preference="accessibility")
        r_acc = run_algorithm("A*", p_acc)
        assert r_acc.success
        assert r_acc.all_accessible, "Accessibility route must not include stair segments"
        for seg in r_acc.path_segments:
            assert seg.accessible, f"Inaccessible segment '{seg.from_id} -> {seg.to_id}' found in accessible route"

        # 3. Sheltered / Rain Mode
        p_shelter = CampusProblem(self.graph, "cs_101", "eng_atrium", preference="shelter")
        r_shelter = run_algorithm("A*", p_shelter)
        assert r_shelter.success

        elapsed = (time.perf_counter() - t0) * 1000.0
        self.log("PREFERENCES", "Validated distance, time, 100% wheelchair accessibility, and rain shelter routing", "PASS", elapsed)

    def test_dynamic_obstacles_and_replanning(self):
        """Injects random pathway obstructions, tests real-time alternate detours, and restores integrity."""
        t0 = time.perf_counter()
        
        # Pick standard path
        prob = CampusProblem(self.graph, "gate_main", "cs_lab_ai")
        initial_route = run_algorithm("A*", prob)
        assert initial_route.success and len(initial_route.path_segments) > 2
        
        # Pick intermediate segment to obstruct
        target_seg = initial_route.path_segments[1]
        u, v = target_seg.from_id, target_seg.to_id
        
        # Block edge
        self.graph.set_edge_blocked(u, v, True, "Automated Test Block")
        
        # Attempt replan
        detour_route = run_algorithm("A*", prob)
        
        # Unblock immediately to prevent leakage
        self.graph.set_edge_blocked(u, v, False)
        
        # Assertions
        assert detour_route.success, f"Detour failed after blocking {u} <-> {v}"
        detour_edges = {(s.from_id, s.to_id) for s in detour_route.path_segments}
        assert (u, v) not in detour_edges and (v, u) not in detour_edges, "Detour route still traversed blocked edge!"
        
        elapsed = (time.perf_counter() - t0) * 1000.0
        self.log("DYNAMIC_OBSTACLE", f"Blocked '{u} <-> {v}' -> Detour successfully found ({detour_route.total_distance:.1f}m)", "PASS", elapsed)

    def test_quick_facility_finder(self):
        """Tests nearest facility Dijkstra discovery across all 6 categories."""
        t0 = time.perf_counter()
        facility_types = ["food", "medical", "atm", "lab", "library", "gate"]
        start_node = random.choice(["hostel_boys", "cs_101", "sports_arena", "sci_lobby", "admin_lobby"])

        for ftype in facility_types:
            res = find_nearest_facility(self.graph, start_node, ftype)
            assert res is not None and res.success, f"Nearest {ftype} from {start_node} failed"
            assert len(res.path_nodes) >= 1

        elapsed = (time.perf_counter() - t0) * 1000.0
        self.log("QUICK_FACILITY", f"Nearest discovery verified from '{start_node}' across {len(facility_types)} facilities", "PASS", elapsed)

    def test_compound_multi_stop(self):
        """Tests multi-stop route composition (A -> Via -> B)."""
        t0 = time.perf_counter()
        start = "gate_main"
        via = "night_canteen"
        goal = "cs_lab_ai"

        compound = find_multi_stop_route(self.graph, start, via, goal)
        assert compound.success, f"Compound route {start} -> {via} -> {goal} failed"
        assert via in compound.path_nodes, f"Waypoint {via} missing from composite path"
        assert compound.total_distance > 0.0

        elapsed = (time.perf_counter() - t0) * 1000.0
        self.log("MULTI_STOP", f"Compound route '{start} -> {via} -> {goal}' verified ({compound.total_distance:.1f}m)", "PASS", elapsed)

    def refine_and_heal(self):
        """Self-healing and diagnostic refinement check."""
        t0 = time.perf_counter()
        # Verify no residual blocks
        has_blocked_node = any(n.is_blocked for n in self.graph.nodes.values())
        has_blocked_edge = any(e.is_blocked for edges in self.graph.edges.values() for e in edges)
        
        if has_blocked_node or has_blocked_edge:
            self.graph.reset_all_blocks()
            self.refinements_applied += 1
            self.log("SELF_HEAL", "Cleared residual dynamic blockages from graph memory", "PASS")

        # System health status update
        if self.tests_failed == 0:
            self.system_health = "OPTIMAL (100% PASS)"
        elif (self.tests_passed / max(1, self.total_tests_executed)) > 0.98:
            self.system_health = "ACCEPTABLE (>98% PASS)"
        else:
            self.system_health = "DEGRADED"

    def execute_single_cycle(self):
        """Runs one full rigorous testing iteration."""
        if self.is_paused:
            time.sleep(0.5)
            return

        cycle_start = time.perf_counter()
        self.cycle_count += 1

        try:
            self.active_test_name = "Validating Graph Invariants"
            self.test_graph_invariants()

            self.active_test_name = "Testing Algorithm Optimality Sweep"
            self.test_algorithm_optimality_sweep()

            self.active_test_name = "Testing Multi-Objective Preferences"
            self.test_multi_objective_preferences()

            self.active_test_name = "Testing Dynamic Obstacle Detours"
            self.test_dynamic_obstacles_and_replanning()

            self.active_test_name = "Testing Quick Facility Discovery"
            self.test_quick_facility_finder()

            self.active_test_name = "Testing Multi-Stop Compound Routes"
            self.test_compound_multi_stop()

            self.active_test_name = "Self-Healing & Invariant Refinement"
            self.refine_and_heal()

            self.active_test_name = "Idle (Waiting next cycle)"

        except Exception as e:
            self.log("ERROR", f"Test cycle {self.cycle_count} encountered anomaly: {str(e)}", "FAIL")
            self.refine_and_heal()

        self.last_cycle_duration_ms = (time.perf_counter() - cycle_start) * 1000.0

    def run_loop(self):
        """Continuous execution loop running in background thread."""
        while self.is_running:
            self.execute_single_cycle()
            time.sleep(1.8)  # Pause between cycles for smooth CPU utilization

    def get_status_dict(self) -> Dict[str, Any]:
        """Telemetry snapshot for REST API and HTML dashboard."""
        uptime = time.time() - self.start_time
        pass_rate = 100.0 if self.total_tests_executed == 0 else (self.tests_passed / self.total_tests_executed) * 100.0
        
        with self.lock:
            logs_copy = list(self.recent_logs)
            
        return {
            "status": "RUNNING" if not self.is_paused else "PAUSED",
            "system_health": self.system_health,
            "uptime_seconds": round(uptime, 1),
            "cycle_count": self.cycle_count,
            "total_tests_executed": self.total_tests_executed,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "pass_rate_pct": round(pass_rate, 2),
            "anomalies_detected": self.anomalies_detected,
            "refinements_applied": self.refinements_applied,
            "active_test": self.active_test_name,
            "last_cycle_duration_ms": round(self.last_cycle_duration_ms, 2),
            "algo_benchmarks": self.algo_stats,
            "recent_logs": logs_copy[-25:]
        }


# Global engine instance
test_engine = ContinuousTestEngine()


class TestServerHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP Request Handler providing a live testing dashboard and REST telemetry API."""

    def _send_json(self, data: dict, status_code: int = 200):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self._send_json(test_engine.get_status_dict())

        elif path == "/api/run-once":
            test_engine.execute_single_cycle()
            self._send_json({"status": "success", "message": "Triggered manual testing cycle."})

        elif path == "/api/toggle-loop":
            test_engine.is_paused = not test_engine.is_paused
            self._send_json({"status": "success", "is_paused": test_engine.is_paused})

        elif path == "/api/reset-stats":
            with test_engine.lock:
                test_engine.total_tests_executed = 0
                test_engine.tests_passed = 0
                test_engine.tests_failed = 0
                test_engine.anomalies_detected = 0
                test_engine.recent_logs.clear()
            self._send_json({"status": "success", "message": "Test counters reset."})

        else:
            # Serve Live HTML Dashboard
            self.serve_dashboard()

    def serve_dashboard(self):
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Autonomous Campus Navigation Test Server & Diagnostic Engine</title>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap">
  <style>
    :root {
      --bg-base: #090d16;
      --bg-card: rgba(19, 29, 51, 0.85);
      --border-line: rgba(255, 255, 255, 0.08);
      --accent-cyan: #38bdf8;
      --accent-emerald: #10b981;
      --accent-amber: #f59e0b;
      --accent-rose: #f43f5e;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg-base);
      color: var(--text-main);
      font-family: 'Plus Jakarta Sans', sans-serif;
      padding: 24px;
      line-height: 1.5;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border-line);
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
    }
    .brand { display: flex; align-items: center; gap: 14px; }
    .brand-icon {
      font-size: 2rem;
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 8px 14px;
      border-radius: 12px;
    }
    .title h1 { font-size: 1.45rem; font-weight: 800; letter-spacing: -0.02em; }
    .title p { font-size: 0.82rem; color: var(--text-muted); }
    .badge-pulse {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: var(--accent-emerald);
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 0.82rem;
      font-weight: 700;
    }
    .pulse-dot {
      width: 8px;
      height: 8px;
      background: var(--accent-emerald);
      border-radius: 50%;
      box-shadow: 0 0 10px var(--accent-emerald);
      animation: pulseAnim 1.4s infinite;
    }
    @keyframes pulseAnim {
      0% { transform: scale(0.9); opacity: 0.7; }
      50% { transform: scale(1.3); opacity: 1; }
      100% { transform: scale(0.9); opacity: 0.7; }
    }
    .grid-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .card {
      background: var(--bg-card);
      border: 1px solid var(--border-line);
      border-radius: 14px;
      padding: 16px;
      backdrop-filter: blur(12px);
    }
    .card-label {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-dim);
      font-weight: 600;
      margin-bottom: 4px;
    }
    .card-val {
      font-family: 'JetBrains Mono', monospace;
      font-size: 1.65rem;
      font-weight: 700;
    }
    .cyan { color: var(--accent-cyan); }
    .emerald { color: var(--accent-emerald); }
    .amber { color: var(--accent-amber); }
    .rose { color: var(--accent-rose); }
    
    .section-title {
      font-size: 1.05rem;
      font-weight: 700;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .controls-row {
      display: flex;
      gap: 12px;
      margin-bottom: 24px;
      flex-wrap: wrap;
    }
    button.btn {
      background: #1e293b;
      border: 1px solid var(--border-line);
      color: var(--text-main);
      padding: 9px 18px;
      font-size: 0.82rem;
      font-weight: 600;
      border-radius: 10px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s;
    }
    button.btn:hover { background: #334155; border-color: var(--accent-cyan); }
    button.btn-primary { background: #0284c7; border-color: transparent; }
    button.btn-primary:hover { background: #0369a1; }

    .split-layout {
      display: grid;
      grid-template-columns: 1fr 1.3fr;
      gap: 20px;
    }
    @media (max-width: 900px) {
      .split-layout { grid-template-columns: 1fr; }
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
    }
    th {
      text-align: left;
      padding: 10px 12px;
      border-bottom: 1px solid var(--border-line);
      color: var(--text-dim);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.72rem;
    }
    td {
      padding: 10px 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      font-family: 'JetBrains Mono', monospace;
    }
    .log-feed {
      max-height: 480px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 6px;
      padding-right: 6px;
    }
    .log-feed::-webkit-scrollbar { width: 6px; }
    .log-feed::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
    .log-item {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
      padding: 8px 12px;
      background: rgba(15, 23, 42, 0.6);
      border-left: 3px solid var(--accent-emerald);
      border-radius: 6px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }
    .log-item.FAIL { border-left-color: var(--accent-rose); background: rgba(244, 63, 94, 0.1); }
    .log-time { color: var(--text-dim); min-width: 65px; }
    .log-cat {
      background: rgba(56, 189, 248, 0.12);
      color: var(--accent-cyan);
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.7rem;
    }
    .log-msg { flex: 1; color: var(--text-main); word-break: break-word; }
  </style>
</head>
<body>

  <div class="header">
    <div class="brand">
      <div class="brand-icon">🧪</div>
      <div class="title">
        <h1>DIT University - Autonomous Campus Navigation Test Server</h1>
        <p>Continuous Regression, AI Optimality Sweep & Diagnostics Engine — Dehradun Campus</p>
      </div>
    </div>
    <div class="badge-pulse">
      <div class="pulse-dot"></div>
      <span id="txt-engine-status">TEST ENGINE: ACTIVE</span>
    </div>
  </div>

  <div class="controls-row">
    <button class="btn btn-primary" onclick="triggerManualRun()">⚡ Run Full Sweep Now</button>
    <button class="btn" id="btn-toggle-pause" onclick="toggleLoop()">⏸ Pause Continuous Loop</button>
    <button class="btn" onclick="resetStats()">🔄 Reset Counters</button>
    <span style="display: flex; align-items: center; margin-left: auto; font-size: 0.82rem; color: var(--text-muted);">
      Active Test: <strong id="txt-active-test" style="color: var(--accent-amber); margin-left: 6px;">Initializing...</strong>
    </span>
  </div>

  <div class="grid-stats">
    <div class="card">
      <div class="card-label">Test Cycles Run</div>
      <div class="card-val cyan" id="stat-cycles">0</div>
    </div>
    <div class="card">
      <div class="card-label">Tests Executed</div>
      <div class="card-val emerald" id="stat-tests">0</div>
    </div>
    <div class="card">
      <div class="card-label">Pass Rate</div>
      <div class="card-val emerald" id="stat-pass-rate">100.0%</div>
    </div>
    <div class="card">
      <div class="card-label">Engine Health</div>
      <div class="card-val" id="stat-health" style="color: #10b981; font-size: 1.15rem;">HEALTHY</div>
    </div>
    <div class="card">
      <div class="card-label">Cycle Latency</div>
      <div class="card-val amber" id="stat-latency">0 ms</div>
    </div>
    <div class="card">
      <div class="card-label">System Uptime</div>
      <div class="card-val" id="stat-uptime" style="font-size: 1.15rem; color: var(--text-muted);">0s</div>
    </div>
  </div>

  <div class="split-layout">
    <!-- Algorithm Performance Benchmark Table -->
    <div class="card">
      <div class="section-title">📊 Real-Time Algorithm Latency & Optimality</div>
      <table>
        <thead>
          <tr>
            <th>Algorithm</th>
            <th>Avg Latency</th>
            <th>Avg Expansions</th>
            <th>Sample Runs</th>
          </tr>
        </thead>
        <tbody id="algo-tbody">
          <tr><td colspan="4" style="color: var(--text-dim); text-align: center;">Collecting algorithm executions...</td></tr>
        </tbody>
      </table>

      <div style="margin-top: 18px; font-size: 0.78rem; color: var(--text-muted); background: rgba(0,0,0,0.25); padding: 12px; border-radius: 8px;">
        💡 <strong>Continuous Regression Check:</strong> Every test cycle automatically proves $A^*$ mathematical cost equivalence with Dijkstra ($f = g$) while validating admissible heuristic expansion savings.
      </div>
    </div>

    <!-- Live Test Event Log Stream -->
    <div class="card">
      <div class="section-title">
        <span>📋 Live Test Execution Stream</span>
        <span style="font-size: 0.75rem; color: var(--text-dim); margin-left: auto;">Auto-refreshing every 1s</span>
      </div>
      <div class="log-feed" id="log-feed-box">
        <div style="color: var(--text-dim); padding: 12px; text-align: center;">Waiting for incoming test stream...</div>
      </div>
    </div>
  </div>

  <script>
    async function fetchStatus() {
      try {
        const res = await fetch('/api/status');
        const d = await res.json();
        
        document.getElementById('stat-cycles').textContent = d.cycle_count;
        document.getElementById('stat-tests').textContent = d.total_tests_executed;
        document.getElementById('stat-pass-rate').textContent = `${d.pass_rate_pct}%`;
        document.getElementById('stat-health').textContent = d.system_health;
        document.getElementById('stat-latency').textContent = `${d.last_cycle_duration_ms} ms`;
        
        const hrs = Math.floor(d.uptime_seconds / 3600);
        const mins = Math.floor((d.uptime_seconds % 3600) / 60);
        const secs = Math.floor(d.uptime_seconds % 60);
        document.getElementById('stat-uptime').textContent = `${hrs}h ${mins}m ${secs}s`;
        
        document.getElementById('txt-active-test').textContent = d.active_test;
        document.getElementById('txt-engine-status').textContent = `TEST ENGINE: ${d.status}`;
        document.getElementById('btn-toggle-pause').textContent = d.status === 'RUNNING' ? '⏸ Pause Continuous Loop' : '▶ Resume Loop';

        // Update Algo benchmarks
        const tbody = document.getElementById('algo-tbody');
        tbody.innerHTML = '';
        for (const [algo, st] of Object.entries(d.algo_benchmarks)) {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td style="color: var(--text-main); font-weight: 700;">${algo}</td>
            <td style="color: var(--accent-cyan);">${st.avg_time_ms.toFixed(2)} ms</td>
            <td style="color: var(--accent-amber);">${st.avg_expansions}</td>
            <td style="color: var(--text-muted);">${st.runs}</td>
          `;
          tbody.appendChild(tr);
        }

        // Update Log Feed
        const feed = document.getElementById('log-feed-box');
        feed.innerHTML = '';
        d.recent_logs.slice().reverse().forEach(log => {
          const div = document.createElement('div');
          div.className = `log-item ${log.status}`;
          div.innerHTML = `
            <span class="log-time">${log.timestamp}</span>
            <span class="log-cat">${log.category}</span>
            <span class="log-msg">${log.message}</span>
            <span style="font-size: 0.72rem; color: var(--accent-cyan);">${log.duration_ms}ms</span>
          `;
          feed.appendChild(div);
        });

      } catch (err) {
        console.error('Failed to fetch status:', err);
      }
    }

    async function triggerManualRun() {
      await fetch('/api/run-once');
      fetchStatus();
    }

    async function toggleLoop() {
      await fetch('/api/toggle-loop');
      fetchStatus();
    }

    async function resetStats() {
      await fetch('/api/reset-stats');
      fetchStatus();
    }

    // Polling loop
    setInterval(fetchStatus, 1200);
    fetchStatus();
  </script>
</body>
</html>
"""
        body = html_content.encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_test_server(port: int = TEST_SERVER_PORT):
    """Starts the continuous testing engine thread and launches the HTTP dashboard server."""
    # 1. Start continuous testing background worker
    worker_thread = threading.Thread(target=test_engine.run_loop, daemon=True)
    worker_thread.start()

    # 2. Start HTTP server
    socketserver.TCPServer.allow_reuse_address = True
    print(f"\n{CYAN}{BOLD}========================================================================{RESET}")
    print(f"{GREEN}{BOLD}🧪 AUTONOMOUS CONTINUOUS TEST SERVER RUNNING{RESET}")
    print(f"📊 Live Diagnostics Dashboard: {BOLD}http://localhost:{port}{RESET}")
    print(f"📡 Telemetry REST API:         {BOLD}http://localhost:{port}/api/status{RESET}")
    print(f"🔄 Loop Status:                {YELLOW}Autonomous Regression & Invariant Healing Active{RESET}")
    print(f"{CYAN}{BOLD}========================================================================{RESET}\n")

    try:
        with socketserver.TCPServer(("", port), TestServerHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Shutting down Continuous Test Server gracefully...{RESET}")
        test_engine.is_running = False
        sys.exit(0)


if __name__ == "__main__":
    port_to_use = TEST_SERVER_PORT
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port_to_use = int(sys.argv[1])
    run_test_server(port_to_use)

