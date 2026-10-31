#!/usr/bin/env python3
"""
Native Python Desktop Graphical Interface (Tkinter) for Campus Navigation Agent.
Provides an interactive canvas map, node/edge obstacle toggling, algorithm stepping,
and live Open List / Closed List inspection tables.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math
import time

from core.graph import create_default_campus_graph, CampusNode, CampusEdge
from core.state_action import CampusProblem
from core.algorithms import run_algorithm, SearchResult, find_nearest_facility

CAMPUS_BUILDING_ZONES = [
    {"name": "Chanakya Block (CS & IT)", "x": 95, "y": 85, "width": 210, "height": 320},
    {"name": "Vishveshwarya Block (Engg)", "x": 360, "y": 45, "width": 260, "height": 135},
    {"name": "Administration & Registry", "x": 310, "y": 550, "width": 140, "height": 125},
    {"name": "Vedanta Block (VEDA Library)", "x": 630, "y": 210, "width": 145, "height": 180},
    {"name": "Charak & Science Block", "x": 800, "y": 200, "width": 135, "height": 230},
    {"name": "Food Court & CCD / SAC", "x": 650, "y": 450, "width": 235, "height": 160},
    {"name": "DIT Sports Complex", "x": 505, "y": 590, "width": 210, "height": 95},
    {"name": "Amphitheatre Quad", "x": 450, "y": 210, "width": 140, "height": 180},
    {"name": "Innovation Hub (TBI)", "x": 25, "y": 40, "width": 95, "height": 140},
    {"name": "Sarabhai & Sarojini Hostels", "x": 25, "y": 430, "width": 125, "height": 155},
    {"name": "School of Management & Law", "x": 885, "y": 380, "width": 105, "height": 205},
    {"name": "Health & Medical Complex", "x": 775, "y": 595, "width": 155, "height": 75},
]


class CampusNavigatorGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("DIT University Dehradun - Campus Navigation Agent (Desktop GUI)")
        self.root.geometry("1300x840")
        self.root.minsize(1050, 700)

        # Style & Color Palette
        self.bg_color = "#0f172a"        # Dark slate
        self.panel_bg = "#1e293b"        # Card slate
        self.accent_color = "#38bdf8"    # Sky blue
        self.highlight_color = "#10b981" # Emerald green
        self.obstacle_color = "#ef4444"  # Rose red
        self.text_color = "#f8fafc"
        self.muted_text = "#94a3b8"

        self.root.configure(bg=self.bg_color)

        # Graph Data
        self.graph = create_default_campus_graph()
        self.start_node_id = "gate_main"
        self.goal_node_id = "cs_lab_ai"
        self.current_result: SearchResult = None

        # Playback animation state
        self.animation_step_idx = 0
        self.is_animating = False
        self.anim_timer = None

        self._build_ui()
        self._refresh_node_dropdowns()
        self.redraw_campus_map()

    def _build_ui(self):
        # Master Layout: Left Sidebar (Controls & Inspectors) + Right (Interactive Map & Logs)
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Left Control Panel
        left_frame = tk.Frame(main_paned, bg=self.panel_bg, width=420)
        left_frame.pack_propagate(False)
        main_paned.add(left_frame, weight=1)

        # Right Map & Output Panel
        right_frame = tk.Frame(main_paned, bg=self.bg_color)
        main_paned.add(right_frame, weight=3)

        # --- LEFT PANEL CONTENTS ---
        title_lbl = tk.Label(
            left_frame,
            text="DIT CAMPUS NAVIGATOR",
            font=("Helvetica", 15, "bold"),
            bg=self.panel_bg,
            fg=self.accent_color
        )
        title_lbl.pack(anchor="w", padx=16, pady=(16, 2))

        loc_lbl = tk.Label(
            left_frame,
            text="DIT University, Dehradun",
            font=("Helvetica", 9, "bold"),
            bg=self.panel_bg,
            fg="#38bdf8"
        )
        loc_lbl.pack(anchor="w", padx=16, pady=(0, 4))

        subtitle_lbl = tk.Label(
            left_frame,
            text="AI Search & Multi-Objective Route Planner",
            font=("Helvetica", 9),
            bg=self.panel_bg,
            fg=self.muted_text
        )
        subtitle_lbl.pack(anchor="w", padx=16, pady=(0, 16))

        # Start & Goal Location Selection
        nav_box = tk.LabelFrame(left_frame, text="Route Endpoints", bg=self.panel_bg, fg=self.text_color, font=("Helvetica", 10, "bold"))
        nav_box.pack(fill=tk.X, padx=14, pady=6)

        tk.Label(nav_box, text="Start Location:", bg=self.panel_bg, fg=self.muted_text).grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.start_combo = ttk.Combobox(nav_box, state="readonly", width=28)
        self.start_combo.grid(row=0, column=1, padx=8, pady=4)
        self.start_combo.bind("<<ComboboxSelected>>", self._on_start_changed)

        tk.Label(nav_box, text="Destination:", bg=self.panel_bg, fg=self.muted_text).grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.goal_combo = ttk.Combobox(nav_box, state="readonly", width=28)
        self.goal_combo.grid(row=1, column=1, padx=8, pady=4)
        self.goal_combo.bind("<<ComboboxSelected>>", self._on_goal_changed)

        # Algorithm & Preferences Selection
        algo_box = tk.LabelFrame(left_frame, text="Algorithm & Routing Criteria", bg=self.panel_bg, fg=self.text_color, font=("Helvetica", 10, "bold"))
        algo_box.pack(fill=tk.X, padx=14, pady=6)

        tk.Label(algo_box, text="Algorithm:", bg=self.panel_bg, fg=self.muted_text).grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.algo_var = tk.StringVar(value="A*")
        self.algo_combo = ttk.Combobox(algo_box, textvariable=self.algo_var, state="readonly",
                                       values=["A*", "BFS", "DFS", "Dijkstra", "Greedy"], width=20)
        self.algo_combo.grid(row=0, column=1, padx=8, pady=4)
        self.algo_combo.bind("<<ComboboxSelected>>", self._on_algo_changed)

        tk.Label(algo_box, text="Preference:", bg=self.panel_bg, fg=self.muted_text).grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.pref_var = tk.StringVar(value="distance")
        self.pref_combo = ttk.Combobox(algo_box, textvariable=self.pref_var, state="readonly",
                                       values=["distance", "time", "accessibility", "crowd", "shelter"], width=20)
        self.pref_combo.grid(row=1, column=1, padx=8, pady=4)
        self.pref_combo.bind("<<ComboboxSelected>>", self._on_pref_changed)

        # Quick Nearest Facility Finder Box
        quick_box = tk.LabelFrame(left_frame, text="Quick AI: Find Nearest", bg=self.panel_bg, fg=self.accent_color, font=("Helvetica", 9, "bold"))
        quick_box.pack(fill=tk.X, padx=14, pady=4)

        qf_row1 = tk.Frame(quick_box, bg=self.panel_bg)
        qf_row1.pack(fill=tk.X, padx=4, pady=2)
        qf_row2 = tk.Frame(quick_box, bg=self.panel_bg)
        qf_row2.pack(fill=tk.X, padx=4, pady=2)

        tk.Button(qf_row1, text="🍽️ Food", font=("Helvetica", 8), bg="#334155", fg="white",
                  command=lambda: self.quick_find("food")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Button(qf_row1, text="🏥 Clinic", font=("Helvetica", 8), bg="#334155", fg="white",
                  command=lambda: self.quick_find("medical")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Button(qf_row1, text="🏧 ATM", font=("Helvetica", 8), bg="#334155", fg="white",
                  command=lambda: self.quick_find("atm")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        tk.Button(qf_row2, text="🔬 Lab", font=("Helvetica", 8), bg="#334155", fg="white",
                  command=lambda: self.quick_find("lab")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Button(qf_row2, text="📚 Library", font=("Helvetica", 8), bg="#334155", fg="white",
                  command=lambda: self.quick_find("library")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Button(qf_row2, text="🚪 Exit", font=("Helvetica", 8), bg="#334155", fg="white",
                  command=lambda: self.quick_find("gate")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Action Buttons
        btn_frame = tk.Frame(left_frame, bg=self.panel_bg)
        btn_frame.pack(fill=tk.X, padx=14, pady=8)

        self.btn_search = tk.Button(
            btn_frame, text="🔍 Find Optimal Route", font=("Helvetica", 10, "bold"),
            bg="#2563eb", fg="white", activebackground="#1d4ed8", activeforeground="white",
            relief=tk.FLAT, command=self.execute_search
        )
        self.btn_search.pack(fill=tk.X, pady=4)

        play_frame = tk.Frame(btn_frame, bg=self.panel_bg)
        play_frame.pack(fill=tk.X, pady=2)

        self.btn_animate = tk.Button(
            play_frame, text="▶ Play Search", font=("Helvetica", 9),
            bg="#059669", fg="white", command=self.toggle_animation
        )
        self.btn_animate.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.btn_step = tk.Button(
            play_frame, text="⏭ Next Step", font=("Helvetica", 9),
            bg="#0284c7", fg="white", command=self.step_forward
        )
        self.btn_step.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        self.btn_reset_blocks = tk.Button(
            btn_frame, text="🧹 Reset All Obstacles", font=("Helvetica", 9),
            bg="#475569", fg="white", command=self.reset_obstacles
        )
        self.btn_reset_blocks.pack(fill=tk.X, pady=4)

        self.btn_rain = tk.Button(
            btn_frame, text="🌧️ Rain Mode: OFF (Sheltered)", font=("Helvetica", 9),
            bg="#0369a1", fg="white", command=self.toggle_rain_mode
        )
        self.btn_rain.pack(fill=tk.X, pady=2)

        # Live Open List & Closed List Inspector
        inspector_box = tk.LabelFrame(left_frame, text="Live Search Inspector (Open / Closed)", bg=self.panel_bg, fg=self.text_color, font=("Helvetica", 10, "bold"))
        inspector_box.pack(fill=tk.BOTH, expand=True, padx=14, pady=6)

        # Notebook tabs for Open List and Closed List
        nb = ttk.Notebook(inspector_box)
        nb.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Open List tab
        tab_open = tk.Frame(nb, bg=self.panel_bg)
        nb.add(tab_open, text="Open List (Frontier)")

        self.open_tree = ttk.Treeview(tab_open, columns=("id", "f", "g", "h"), show="headings", height=6)
        self.open_tree.heading("id", text="Node")
        self.open_tree.heading("f", text="f(n)")
        self.open_tree.heading("g", text="g(n)")
        self.open_tree.heading("h", text="h(n)")
        self.open_tree.column("id", width=120)
        self.open_tree.column("f", width=50)
        self.open_tree.column("g", width=50)
        self.open_tree.column("h", width=50)
        self.open_tree.pack(fill=tk.BOTH, expand=True)

        # Closed List tab
        tab_closed = tk.Frame(nb, bg=self.panel_bg)
        nb.add(tab_closed, text="Closed List (Explored)")

        self.closed_listbox = tk.Listbox(tab_closed, bg="#0f172a", fg=self.text_color, font=("Courier", 9))
        self.closed_listbox.pack(fill=tk.BOTH, expand=True)

        # --- RIGHT PANEL CONTENTS: Campus Map Canvas + Metrics Bar ---
        # Top Metrics Bar
        self.metrics_bar = tk.Frame(right_frame, bg=self.panel_bg, height=50)
        self.metrics_bar.pack(fill=tk.X, padx=8, pady=(0, 6))

        self.lbl_status = tk.Label(
            self.metrics_bar,
            text="Ready. Click any node to select endpoints or right-click to block/unblock obstacles.",
            bg=self.panel_bg, fg=self.text_color, font=("Helvetica", 10)
        )
        self.lbl_status.pack(side=tk.LEFT, padx=12, pady=8)

        # Canvas for Campus Map
        self.canvas = tk.Canvas(right_frame, bg="#0a0f1d", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Button-2>", self._on_canvas_right_click) # Mac trackpad/two-finger
        self.canvas.bind("<Button-3>", self._on_canvas_right_click) # Windows/Linux right-click
        self.canvas.bind("<Configure>", lambda e: self.redraw_campus_map())
        self.canvas.bind("<Motion>", self._on_canvas_motion)

    def _refresh_node_dropdowns(self):
        sorted_nodes = sorted(self.graph.nodes.values(), key=lambda n: (n.building, n.name))
        labels = [f"{n.name} ({n.id})" for n in sorted_nodes]
        self.node_id_by_label = {f"{n.name} ({n.id})": n.id for n in sorted_nodes}

        self.start_combo['values'] = labels
        self.goal_combo['values'] = labels

        # Set default values
        start_lbl = next((l for l in labels if self.start_node_id in l), labels[0])
        goal_lbl = next((l for l in labels if self.goal_node_id in l), labels[1])
        self.start_combo.set(start_lbl)
        self.goal_combo.set(goal_lbl)

    def _on_start_changed(self, event):
        val = self.start_combo.get()
        if val in self.node_id_by_label:
            self.start_node_id = self.node_id_by_label[val]
            if self.current_result:
                self.execute_search()
            else:
                self.redraw_campus_map()

    def _on_goal_changed(self, event):
        val = self.goal_combo.get()
        if val in self.node_id_by_label:
            self.goal_node_id = self.node_id_by_label[val]
            if self.current_result:
                self.execute_search()
            else:
                self.redraw_campus_map()

    def _on_algo_changed(self, event):
        if self.current_result:
            self.execute_search()

    def _on_pref_changed(self, event):
        if self.current_result:
            self.execute_search()

    def execute_search(self):
        algo = self.algo_var.get()
        pref = self.pref_var.get()
        heur = "time" if pref == "time" else "euclidean"

        try:
            prob = CampusProblem(self.graph, self.start_node_id, self.goal_node_id, preference=pref)
            self.current_result = run_algorithm(algo, prob, heuristic=heur)
            self.animation_step_idx = len(self.current_result.steps) - 1

            if self.current_result.success:
                steps = int(round(self.current_result.total_distance / 0.75))
                cal = self.current_result.total_distance * 0.045
                msg = (f"✔ Route Found! Distance: {self.current_result.total_distance:.1f}m | "
                       f"Time: {self.current_result.total_time:.1f}s | "
                       f"👟 {steps} steps | 🔥 {cal:.1f} kcal | "
                       f"Nodes: {self.current_result.nodes_expanded} | "
                       f"Accessible: {'Yes' if self.current_result.all_accessible else 'No'}")
                self.lbl_status.config(text=msg, fg=self.highlight_color)
            else:
                self.lbl_status.config(text=f"❌ No path found: {self.current_result.error_message}", fg=self.obstacle_color)

            self.update_inspector_step(self.animation_step_idx)
            self.redraw_campus_map()

        except Exception as e:
            messagebox.showerror("Search Error", str(e))

    def toggle_rain_mode(self):
        current_pref = self.pref_var.get()
        if current_pref == "shelter":
            self.pref_var.set("distance")
            self.btn_rain.config(text="🌧️ Rain Mode: OFF (Fair)", bg="#0369a1")
        else:
            self.pref_var.set("shelter")
            self.btn_rain.config(text="🌧️ Rain Mode: ON (Sheltered)", bg="#0284c7")
        self.execute_search()

    def quick_find(self, facility_type: str):
        pref = self.pref_var.get()
        res = find_nearest_facility(self.graph, self.start_node_id, facility_type, preference=pref)
        if res and res.success:
            self.goal_node_id = res.goal_id
            self._sync_dropdowns_to_state()
            self.current_result = res
            self.animation_step_idx = len(res.steps) - 1
            dest_name = self.graph.nodes[res.goal_id].name if res.goal_id in self.graph.nodes else res.goal_id
            msg = (f"🎯 Nearest {facility_type.title()} Found: {dest_name} | "
                   f"Distance: {res.total_distance:.1f}m | Time: {res.total_time:.1f}s")
            self.lbl_status.config(text=msg, fg=self.highlight_color)
            self.update_inspector_step(self.animation_step_idx)
            self.redraw_campus_map()
        else:
            messagebox.showinfo("Not Found", f"No accessible {facility_type} located from current start position.")

    def update_inspector_step(self, step_idx: int):
        if not self.current_result or not self.current_result.steps:
            return

        idx = max(0, min(step_idx, len(self.current_result.steps) - 1))
        step = self.current_result.steps[idx]

        # Update Open List tree
        for item in self.open_tree.get_children():
            self.open_tree.delete(item)

        for op in step.open_list:
            node_lbl = op.get('name', op.get('id', ''))
            f_val = op.get('f', '-')
            g_val = op.get('g', '-')
            h_val = op.get('h', '-')
            self.open_tree.insert("", tk.END, values=(node_lbl, f_val, g_val, h_val))

        # Update Closed List listbox
        self.closed_listbox.delete(0, tk.END)
        for c_id in step.closed_list:
            c_node = self.graph.get_node(c_id)
            c_name = c_node.name if c_node else c_id
            self.closed_listbox.insert(tk.END, f"{c_id} ({c_name})")

    def toggle_animation(self):
        if not self.current_result or not self.current_result.steps:
            self.execute_search()

        if self.is_animating:
            self.is_animating = False
            self.btn_animate.config(text="▶ Play Search", bg="#059669")
            if self.anim_timer:
                self.root.after_cancel(self.anim_timer)
        else:
            self.is_animating = True
            self.btn_animate.config(text="⏸ Pause", bg="#d97706")
            self.animation_step_idx = 0
            self._animate_next_frame()

    def _animate_next_frame(self):
        if not self.is_animating or not self.current_result:
            return

        if self.animation_step_idx < len(self.current_result.steps):
            self.update_inspector_step(self.animation_step_idx)
            self.redraw_campus_map(step_override=self.animation_step_idx)
            self.animation_step_idx += 1
            self.anim_timer = self.root.after(250, self._animate_next_frame)
        else:
            self.is_animating = False
            self.btn_animate.config(text="▶ Replay", bg="#059669")
            self.redraw_campus_map()

    def step_forward(self):
        if not self.current_result or not self.current_result.steps:
            self.execute_search()
            self.animation_step_idx = 0

        if self.animation_step_idx < len(self.current_result.steps) - 1:
            self.animation_step_idx += 1
            self.update_inspector_step(self.animation_step_idx)
            self.redraw_campus_map(step_override=self.animation_step_idx)

    def reset_obstacles(self):
        self.graph.reset_all_blocks()
        self.lbl_status.config(text="All obstacles cleared.", fg=self.text_color)
        if self.current_result:
            self.execute_search()
        else:
            self.redraw_campus_map()

    def redraw_campus_map(self, step_override: int = None):
        self.canvas.delete("all")
        width = self.canvas.winfo_width() or 800
        height = self.canvas.winfo_height() or 600

        scale_x = width / 1050.0
        scale_y = height / 750.0

        # Step inspection sets
        step_closed = set()
        step_open = set()
        current_step_node = None

        if self.current_result and self.current_result.steps:
            idx = step_override if step_override is not None else self.animation_step_idx
            idx = max(0, min(idx, len(self.current_result.steps) - 1))
            st = self.current_result.steps[idx]
            step_closed = set(st.closed_list)
            step_open = {op["id"] for op in st.open_list}
            current_step_node = st.current_node

        # Path nodes set
        final_path_edges = set()
        if self.current_result and self.current_result.success:
            for seg in self.current_result.path_segments:
                final_path_edges.add((seg.from_id, seg.to_id))
                final_path_edges.add((seg.to_id, seg.from_id))

        # 0. Draw Building Zones
        for z in CAMPUS_BUILDING_ZONES:
            zx1 = z["x"] * scale_x
            zy1 = z["y"] * scale_y
            zx2 = (z["x"] + z["width"]) * scale_x
            zy2 = (z["y"] + z["height"]) * scale_y
            self.canvas.create_rectangle(
                zx1, zy1, zx2, zy2,
                fill="#131d33", outline="#1e293b", width=1.5
            )
            self.canvas.create_text(
                zx1 + 10, zy1 + 12,
                text=z["name"].upper(),
                anchor="w",
                fill="#475569",
                font=("Helvetica", 8, "bold")
            )

        # 1. Draw Edges
        drawn_edges = set()
        for u, edge_list in self.graph.edges.items():
            for e in edge_list:
                pair = tuple(sorted([e.source, e.target]))
                if pair in drawn_edges:
                    continue
                drawn_edges.add(pair)

                n1 = self.graph.nodes[e.source]
                n2 = self.graph.nodes[e.target]
                x1, y1 = n1.x * scale_x, n1.y * scale_y
                x2, y2 = n2.x * scale_x, n2.y * scale_y

                # Style based on condition
                is_on_final_path = (e.source, e.target) in final_path_edges
                if e.is_blocked:
                    color = "#ef4444" # Red for blocked
                    dash = (4, 4)
                    width_line = 3
                elif is_on_final_path:
                    color = "#10b981" # Glowing green
                    dash = ()
                    width_line = 5
                elif not e.accessible:
                    color = "#f59e0b" # Orange stairs
                    dash = (2, 2)
                    width_line = 2
                else:
                    color = "#334155" # Subtle gray walkway
                    dash = ()
                    width_line = 2

                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width_line, dash=dash)

        # 2. Draw Nodes
        node_radius = 12
        for node in self.graph.nodes.values():
            nx = node.x * scale_x
            ny = node.y * scale_y

            # Determine color
            if node.is_blocked:
                fill_color = "#ef4444" # Obstacle red
                border_color = "#ffffff"
            elif node.id == self.start_node_id:
                fill_color = "#3b82f6" # Start blue
                border_color = "#ffffff"
            elif node.id == self.goal_node_id:
                fill_color = "#10b981" # Goal emerald
                border_color = "#ffffff"
            elif node.id == current_step_node:
                fill_color = "#f59e0b" # Current active gold
                border_color = "#ffffff"
            elif node.id in step_open:
                fill_color = "#06b6d4" # Cyan open list
                border_color = "#0f172a"
            elif node.id in step_closed:
                fill_color = "#8b5cf6" # Purple explored
                border_color = "#0f172a"
            else:
                fill_color = "#1e293b" # Slate
                border_color = "#475569"

            # Draw circle
            self.canvas.create_oval(
                nx - node_radius, ny - node_radius,
                nx + node_radius, ny + node_radius,
                fill=fill_color, outline=border_color, width=2,
                tags=("node", node.id)
            )

            # Node label text
            label_text = node.name.split()[0] # Short name
            self.canvas.create_text(
                nx, ny + node_radius + 9,
                text=label_text, fill=self.text_color, font=("Helvetica", 8, "bold")
            )

    def _on_canvas_click(self, event):
        """Left click selects start or goal."""
        clicked_id = self._find_clicked_node(event.x, event.y)
        if not clicked_id:
            return

        if self.start_node_id and not self.goal_node_id:
            self.goal_node_id = clicked_id
        elif not self.start_node_id:
            self.start_node_id = clicked_id
        else:
            # Alternate selection
            self.start_node_id = self.goal_node_id
            self.goal_node_id = clicked_id

        self._sync_dropdowns_to_state()
        if self.current_result:
            self.execute_search()
        else:
            self.redraw_campus_map()

    def _on_canvas_right_click(self, event):
        """Right click blocks/unblocks a node or adjacent edge."""
        clicked_id = self._find_clicked_node(event.x, event.y)
        if clicked_id:
            node = self.graph.get_node(clicked_id)
            new_state = not node.is_blocked
            self.graph.set_node_blocked(clicked_id, new_state, "Manual Block")
            status_txt = f"{'Blocked' if new_state else 'Unblocked'} {node.name}"
            self.lbl_status.config(text=status_txt, fg=self.obstacle_color if new_state else self.highlight_color)
            if self.current_result:
                self.execute_search()
            else:
                self.redraw_campus_map()

    def _on_canvas_motion(self, event):
        """Hovering over node shows name and coordinates in status bar if not searching."""
        clicked_id = self._find_clicked_node(event.x, event.y)
        if clicked_id:
            node = self.graph.get_node(clicked_id)
            status_str = f"📍 {node.name} ({node.building}, Floor {node.floor}) | Left-click: Set endpoint | Right-click: Block"
            self.canvas.config(cursor="hand2")
            if not self.is_animating:
                self.lbl_status.config(text=status_str, fg=self.accent_color)
        else:
            self.canvas.config(cursor="")

    def _find_clicked_node(self, cx, cy) -> str:
        width = self.canvas.winfo_width() or 800
        height = self.canvas.winfo_height() or 600
        scale_x = width / 1050.0
        scale_y = height / 750.0

        for node in self.graph.nodes.values():
            nx = node.x * scale_x
            ny = node.y * scale_y
            if math.hypot(cx - nx, cy - ny) <= 18:
                return node.id
        return None

    def _sync_dropdowns_to_state(self):
        for lbl, nid in self.node_id_by_label.items():
            if nid == self.start_node_id:
                self.start_combo.set(lbl)
            if nid == self.goal_node_id:
                self.goal_combo.set(lbl)


def main():
    root = tk.Tk()
    app = CampusNavigatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
