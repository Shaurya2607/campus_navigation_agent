#!/usr/bin/env python3
"""
Zero-dependency Python HTTP & REST API Web Server.
Serves the campus navigation interactive web interface and provides REST API endpoints.
Runs natively with standard library Python (no pip packages needed).
"""

import http.server
import socketserver
import json
import urllib.parse
import os
import sys

from core.graph import create_default_campus_graph
from core.state_action import CampusProblem
from core.algorithms import run_algorithm, find_nearest_facility, find_multi_stop_route
from core.environment import CampusEnvironmentSimulator, get_peas_description, get_environment_classifications
from database import load_campus_graph, save_graph, get_database_status

PORT = 8080
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

# Shared state
campus_graph = load_campus_graph()
simulator = CampusEnvironmentSimulator(campus_graph)


class CampusApiHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler serving static assets from web/ and handling REST API calls."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _send_json(self, data: dict, status_code: int = 200):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/graph":
            self._send_json(campus_graph.to_dict())
        elif path == "/api/database-status":
            self._send_json(get_database_status())
        elif path == "/api/environment":
            self._send_json({
                "peas": get_peas_description(),
                "classifications": get_environment_classifications()
            })
        elif path == "/api/reset-blocks":
            campus_graph.reset_all_blocks()
            save_graph(campus_graph)
            self._send_json({"status": "success", "message": "All obstacles cleared."})
        elif path == "/api/status":
            self._send_json({
                "status": "online",
                "nodes_count": len(campus_graph.nodes),
                "edges_count": sum(len(e) for e in campus_graph.edges.values()) // 2
            })
        else:
            # Fallback to static file serving from web/
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            payload = {}

        if path == "/api/search":
            start_id = payload.get("start", "gate_main")
            goal_id = payload.get("goal", "cs_lab_ai")
            algo = payload.get("algorithm", "A*")
            pref = payload.get("preference", "distance")
            heur = payload.get("heuristic", "euclidean")

            try:
                prob = CampusProblem(campus_graph, start_id, goal_id, preference=pref)
                result = run_algorithm(algo, prob, heuristic=heur)
                self._send_json({
                    "status": "success",
                    "result": result.to_dict()
                })
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, 400)

        elif path == "/api/compare-all":
            start_id = payload.get("start", "gate_main")
            goal_id = payload.get("goal", "cs_lab_ai")
            pref = payload.get("preference", "distance")

            algo_configs = [
                ("A* (Distance)", "A*", "euclidean"),
                ("A* (Time)", "A*", "time"),
                ("BFS", "BFS", "euclidean"),
                ("DFS", "DFS", "euclidean"),
                ("Dijkstra", "Dijkstra", "zero"),
                ("Greedy Best-First", "Greedy", "euclidean"),
            ]
            results = {}
            for label, algo_name, heur in algo_configs:
                try:
                    prob = CampusProblem(campus_graph, start_id, goal_id, preference=pref)
                    res = run_algorithm(algo_name, prob, heuristic=heur)
                    results[label] = res.to_dict()
                except Exception as e:
                    results[label] = {"success": False, "error_message": str(e)}

            self._send_json({"status": "success", "results": results})

        elif path == "/api/compare-preferences":
            start_id = payload.get("start", "gate_main")
            goal_id = payload.get("goal", "cs_lab_ai")
            algo = payload.get("algorithm", "A*")

            routes = simulator.find_all_preference_routes(start_id, goal_id, algorithm=algo)
            serialized = {k: v.to_dict() for k, v in routes.items()}
            self._send_json({"status": "success", "routes": serialized})

        elif path == "/api/toggle-block":
            block_type = payload.get("type", "node")
            is_blocked = payload.get("blocked", True)
            reason = payload.get("reason", "Manual obstruction")

            if block_type == "node":
                node_id = payload.get("id")
                success = campus_graph.set_node_blocked(node_id, is_blocked, reason)
            else:
                u = payload.get("source")
                v = payload.get("target")
                success = campus_graph.set_edge_blocked(u, v, is_blocked, reason)

            if success:
                save_graph(campus_graph)
            self._send_json({
                "status": "success" if success else "error",
                "message": f"Updated block status: {is_blocked}",
                "graph": campus_graph.to_dict()
            })

        elif path == "/api/simulate-rush-hour":
            active = payload.get("active", True)
            simulator.simulate_rush_hour(active)
            save_graph(campus_graph)
            self._send_json({
                "status": "success",
                "active": active,
                "message": "Rush hour toggled.",
                "graph": campus_graph.to_dict()
            })

        elif path == "/api/simulate-partial":
            start_id = payload.get("start", "cs_entrance")
            goal_id = payload.get("goal", "lib_group_study")
            hidden = payload.get("hidden_blocks", [["central_plaza", "lib_foyer"]])
            tuples = [(h[0], h[1]) for h in hidden]
            sim_res = simulator.simulate_partially_observable_navigation(start_id, goal_id, tuples)
            self._send_json({"status": "success", "simulation": sim_res})

        elif path == "/api/reset-blocks":
            campus_graph.reset_all_blocks()
            save_graph(campus_graph)
            self._send_json({"status": "success", "message": "All obstacles cleared.", "graph": campus_graph.to_dict()})

        elif path == "/api/nearest":
            start_id = payload.get("start", "gate_main")
            facility_type = payload.get("type", "food")
            pref = payload.get("preference", "distance")
            result = find_nearest_facility(campus_graph, start_id, facility_type, preference=pref)
            if result:
                self._send_json({"status": "success", "result": result.to_dict(), "target": result.goal_id})
            else:
                self._send_json({"status": "error", "message": f"No accessible {facility_type} found."}, 404)

        elif path == "/api/multi-stop":
            start_id = payload.get("start", "gate_main")
            via_id = payload.get("via", "cafeteria_main")
            goal_id = payload.get("goal", "cs_lab_ai")
            algo = payload.get("algorithm", "A*")
            pref = payload.get("preference", "distance")
            result = find_multi_stop_route(campus_graph, start_id, via_id, goal_id, algorithm=algo, preference=pref)
            self._send_json({"status": "success" if result.success else "error", "result": result.to_dict()})

        else:
            self._send_json({"status": "error", "message": f"Unknown endpoint '{path}'"}, 404)


def run_server(port: int = PORT):
    # Allow port reuse immediately
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", port), CampusApiHandler) as httpd:
        print(f"\n========================================================")
        print(f"🚀 DIT University Dehradun - Campus Navigation Web Server!")
        print(f"📍 Location: Mussoorie Diversion Road, Dehradun, Uttarakhand")
        print(f"🌐 Access Web Interface: http://localhost:{port}")
        print(f"📡 REST API Base:        http://localhost:{port}/api/")
        print(f"========================================================\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server gracefully...")
            httpd.server_close()


if __name__ == "__main__":
    port_to_use = PORT
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port_to_use = int(sys.argv[1])
    run_server(port_to_use)
