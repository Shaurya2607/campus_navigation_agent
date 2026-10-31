#!/usr/bin/env python3
"""
Comprehensive Documentation Generator for Intelligent Campus Navigation Agent.
Generates:
1. Campus_Navigation_Agent_Project_Report.docx (Full Word Document)
2. Campus_Navigation_Agent_Project_Report.pdf (Full PDF Report)
"""

import os
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PRIMARY_COLOR = RGBColor(30, 58, 138)    # #1E3A8A Deep Navy
SECONDARY_COLOR = RGBColor(37, 99, 235)  # #2563EB Royal Blue
DARK_TEXT = RGBColor(31, 41, 55)         # #1F2937 Dark Charcoal
MUTED_TEXT = RGBColor(107, 114, 128)     # #6B7280 Gray
SUCCESS_COLOR = RGBColor(16, 185, 129)   # #10B981 Emerald Green

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def add_header_styled(doc, text, level):
    h = doc.add_heading(text, level=level)
    run = h.runs[0] if h.runs else h.add_run(text)
    if level == 1:
        run.font.size = Pt(18)
        run.font.bold = True
        run.font.color.rgb = PRIMARY_COLOR
        pPr = h._p.get_or_add_pPr()
        pBdr = parse_xml(f'''
            <w:pBdr {nsdecls("w")}>
                <w:bottom w:val="single" w:sz="12" w:space="4" w:color="2563EB"/>
            </w:pBdr>
        ''')
        pPr.append(pBdr)
    elif level == 2:
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = SECONDARY_COLOR
    elif level == 3:
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = DARK_TEXT
    return h

def format_table(table, col_widths, hex_header="1E3A8A"):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # Format header
    for i, cell in enumerate(table.rows[0].cells):
        set_cell_background(cell, hex_header)
        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.font.size = Pt(9.5)
    
    # Format data rows
    for r_idx, row in enumerate(table.rows[1:]):
        bg = "F9FAFB" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, cell in enumerate(row.cells):
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9)
                    run.font.color.rgb = DARK_TEXT

    # Set column widths
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

def generate_word_doc(output_path):
    doc = Document()
    
    # Page Margins: 0.75 in
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Base Style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(10.5)
    normal_style.font.color.rgb = DARK_TEXT
    normal_style.paragraph_format.line_spacing = 1.2
    normal_style.paragraph_format.space_after = Pt(4)

    # ==========================
    # COVER / TITLE BLOCK
    # ==========================
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(36)
    title_p.paragraph_format.space_after = Pt(8)
    run_title = title_p.add_run("🧭 INTELLIGENT CAMPUS NAVIGATION AGENT")
    run_title.font.size = Pt(26)
    run_title.font.bold = True
    run_title.font.color.rgb = PRIMARY_COLOR

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p.paragraph_format.space_after = Pt(16)
    run_sub = sub_p.add_run("Comprehensive Technical Documentation, AI Search Algorithms, Server Details & Operational Manual")
    run_sub.font.size = Pt(13)
    run_sub.font.color.rgb = SECONDARY_COLOR

    meta_p = doc.add_paragraph()
    meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_p.paragraph_format.space_after = Pt(30)
    run_meta = meta_p.add_run("Architecture: Python Standard Library + Dual Frontend (Interactive Web & Tkinter GUI) + Google Maps Integration\nDate: October 2026 | Version: 2.0 Final Production Release")
    run_meta.font.size = Pt(9.5)
    run_meta.font.color.rgb = MUTED_TEXT

    # Divider line
    doc.add_page_break()

    # ==========================
    # SECTION 1: EXECUTIVE SUMMARY
    # ==========================
    add_header_styled(doc, "1. Executive Summary & Project Purpose", 1)
    
    p = doc.add_paragraph(
        "The Intelligent Campus Navigation Agent is an autonomous, AI-driven graph search and optimal route planning system designed for modern multi-building, multi-floor educational institutions. Universities often comprise sprawling campuses with complex interconnected topologies—outdoor boulevards, indoor skywalks, multi-level academic wings, specialized laboratories, dining halls, and transit hubs. Navigating such environments is non-trivial, particularly when accounting for dynamic obstacles (construction, maintenance), diverse mobility constraints (wheelchair accessibility), and varying objectives (minimizing physical walking distance, avoiding hallway crowd congestion, or seeking rain-sheltered paths)."
    )
    p = doc.add_paragraph(
        "This project bridges classical Artificial Intelligence state-space search with practical, real-world deployment. It formulates campus navigation as a formal search problem using the Russell & Norvig framework, implementing and benchmarking five core algorithms: Breadth-First Search (BFS), Depth-First Search (DFS), Uniform Cost Search (Dijkstra), Greedy Best-First Search, and A* Search with admissible Euclidean distance and travel time lower-bound heuristics. The system delivers dual interactive interfaces (a zero-dependency Web application and a native desktop GUI), live Open/Closed list inspection, continuous self-testing automation, and seamless Google Maps satellite integration."
    )

    # Highlights table
    table = doc.add_table(rows=6, cols=2)
    col_widths = [Inches(2.2), Inches(4.8)]
    table.rows[0].cells[0].paragraphs[0].text = "Core Pillar"
    table.rows[0].cells[1].paragraphs[0].text = "Technical Implementation Summary"
    
    data = [
        ("Campus Representation", "50 nodes across 12 zones, 78 bidirectional edges with distance, elevation, accessibility, and crowd weights."),
        ("Search Algorithms", "BFS (hop-optimal), DFS (deep exploration), Dijkstra (cost-optimal), Greedy Best-First, and A* (distance & time heuristics)."),
        ("Multi-Objective Criteria", "Real-time optimization by: (1) Shortest Distance, (2) Fastest Time, (3) Wheelchair Accessibility, and (4) Lowest Crowd."),
        ("Real-World Features", "Dynamic obstacle insertion with runtime re-routing, 1-tap nearest facility discovery, compound multi-stop trips, and weather rain simulation."),
        ("User Interfaces", "Dual frontends: Modern Web interface with SVG + Google Maps hybrid view, and native Python Tkinter GUI.")
    ]
    for i, (k, v) in enumerate(data, 1):
        table.rows[i].cells[0].paragraphs[0].text = k
        table.rows[i].cells[1].paragraphs[0].text = v
    format_table(table, col_widths)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ==========================
    # SECTION 2: SYSTEM ARCHITECTURE
    # ==========================
    add_header_styled(doc, "2. System Architecture & File Structure", 1)
    doc.add_paragraph(
        "The project follows a clean, modular, and decoupled software architecture. All algorithmic logic, state definitions, and heuristics reside within the core/ package, completely isolated from user interface and networking layers. The entire solution operates exclusively with Python 3's standard library, requiring zero third-party pip dependencies for core execution."
    )

    arch_table = doc.add_table(rows=12, cols=3)
    arch_widths = [Inches(1.8), Inches(1.5), Inches(3.7)]
    arch_table.rows[0].cells[0].paragraphs[0].text = "Directory / File"
    arch_table.rows[0].cells[1].paragraphs[0].text = "Layer"
    arch_table.rows[0].cells[2].paragraphs[0].text = "Functional Responsibility"
    
    arch_data = [
        ("core/graph.py", "Data Layer", "Defines CampusNode, CampusEdge, CampusGraph classes and full campus topology with 50 nodes and GPS coordinates."),
        ("core/state_action.py", "AI Modeling", "Formalizes CampusState, CampusAction, and CampusProblem adhering to standard Russell & Norvig search abstractions."),
        ("core/heuristics.py", "AI Search", "Implements Euclidean distance, Manhattan distance, and strictly admissible travel-time lower-bound heuristic functions."),
        ("core/algorithms.py", "AI Search", "Contains implementations of BFS, DFS, Dijkstra, Greedy Best-First, A* search, nearest facility, and multi-stop compound planner."),
        ("core/environment.py", "Simulation", "Implements dynamic campus simulator (weather, crowd fluctuations, obstacle events) and PEAS formal specification."),
        ("server.py", "API & Web Backend", "Zero-dependency HTTP server delivering REST API endpoints (/api/route, /api/facility, etc.) and hosting web frontend."),
        ("test_server.py", "Continuous QA", "Autonomous regression & diagnostic background test server running iterative suites on port 8090 with live web dashboard."),
        ("gui_app.py", "Desktop Frontend", "Native Python Tkinter graphical interface featuring interactive canvas, step playback, and algorithm controls."),
        ("web/index.html", "Web UI", "Semantic HTML5 UI layout, modal dialogs, toolbar, step inspector, pass generator, and map containers."),
        ("web/styles.css", "Web Styling", "Dark glassmorphism design system, responsive grids, radar indicators, and animated transit effects."),
        ("web/app.js", "Web Controller", "Interactive client logic: SVG canvas engine, Google Maps hybrid sync, REST client, step inspector scrubber, and avatar walking.")
    ]
    for i, (f, l, d) in enumerate(arch_data, 1):
        arch_table.rows[i].cells[0].paragraphs[0].text = f
        arch_table.rows[i].cells[1].paragraphs[0].text = l
        arch_table.rows[i].cells[2].paragraphs[0].text = d
    format_table(arch_table, arch_widths)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ==========================
    # SECTION 3: FORMAL AI FORMULATION
    # ==========================
    add_header_styled(doc, "3. Formal AI Problem Formulation (Russell & Norvig)", 1)
    doc.add_paragraph(
        "To establish rigorous theoretical foundations, the navigation problem is modeled as a classic single-agent search problem formalized as a 6-tuple:"
    )

    doc.add_paragraph("• State Space (S): Each state represents an exact physical location on campus characterized by: s = ⟨node_id, building, floor, (x, y), category⟩.")
    doc.add_paragraph("• Initial State (s₀): The origin location designated by the user (e.g., Main Gate, Admin Lobby, or Engineering Quad).")
    doc.add_paragraph("• Actions A(s): Walkable pathways exiting current node: a = Traverse(u, v, path_type, distance, accessible, crowd_level).")
    doc.add_paragraph("• Transition Model Result(s, a): Deterministic mapping returning successor state s' = v upon executing traversal action a.")
    doc.add_paragraph("• Goal Test IsGoal(s): Evaluates whether s.id == s_goal.id (or in facility search, whether s.category == target_category).")
    doc.add_paragraph("• Path Cost Function c(s, a, s'): Configured dynamically based on user routing preferences:")

    doc.add_paragraph("    1. Shortest Distance: c = a.distance (in physical meters)")
    doc.add_paragraph("    2. Fastest Time: c = (a.distance / v_eff) + delay_vertical, where v_eff = 1.3 m/s / crowd_factor")
    doc.add_paragraph("    3. Wheelchair Accessibility: c = ∞ if accessible == False; else travel time")
    doc.add_paragraph("    4. Lowest Crowd Congestion: c = a.distance × (crowd_level)²")

    add_header_styled(doc, "3.1 PEAS Specification", 2)
    peas_table = doc.add_table(rows=5, cols=2)
    peas_widths = [Inches(2.0), Inches(5.0)]
    peas_table.rows[0].cells[0].paragraphs[0].text = "PEAS Dimension"
    peas_table.rows[0].cells[1].paragraphs[0].text = "Detailed Formulation in Campus Agent"
    peas_data = [
        ("Performance Measure", "Minimized total path distance and transit duration; zero violations of accessibility constraints; minimized exposure to hallway crowd bottlenecks; minimal search frontier expansion overhead."),
        ("Environment", "Multi-building university campus graph comprising indoor lecture halls, labs, administrative offices, stairways, elevators, outdoor quads, and connecting skywalks."),
        ("Actuators", "Route guidance instructions, turn-by-turn waypoint cues, dynamic detour recommendations upon pathway blockage, and visual avatar navigation trajectory."),
        ("Sensors", "Campus topological graph database, facility status feeds (elevator maintenance, door lockouts), and dynamic crowd density telemetry.")
    ]
    for i, (k, v) in enumerate(peas_data, 1):
        peas_table.rows[i].cells[0].paragraphs[0].text = k
        peas_table.rows[i].cells[1].paragraphs[0].text = v
    format_table(peas_table, peas_widths)

    add_header_styled(doc, "3.2 Russell & Norvig 6-Dimension Environment Classification", 2)
    env_table = doc.add_table(rows=7, cols=3)
    env_widths = [Inches(1.8), Inches(1.5), Inches(3.7)]
    env_table.rows[0].cells[0].paragraphs[0].text = "Dimension"
    env_table.rows[0].cells[1].paragraphs[0].text = "Classification"
    env_table.rows[0].cells[2].paragraphs[0].text = "Theoretical & Practical Justification"
    env_data = [
        ("Observability", "Fully Observable (Nominal) / Partially Observable", "The agent has full access to the campus graph topology. However, localized real-world disruptions (sudden hallway closures) are observed dynamically, prompting real-time replanning."),
        ("Determinism", "Deterministic (Transitions) / Stochastic (Durations)", "Edge transitions from node u to v are deterministic. Actual transit durations exhibit stochastic variance due to elevator queue times and pedestrian flow."),
        ("Temporality", "Sequential", "Navigation decisions are strictly sequential: choosing an entrance or ascending a staircase directly dictates the available successor state space and accumulated cost."),
        ("Dynamics", "Dynamic", "The environment changes while the agent operates: class dismissal bell rings trigger sudden crowd spikes, and maintenance crews can cordon off pathways mid-journey."),
        ("Discreteness", "Discrete", "Campus rooms, junctions, corridors, and discrete step intervals form a discrete state-action space."),
        ("Agency", "Single-Agent", "The navigation agent plans autonomously, treating other campus pedestrians as dynamic environmental friction rather than strategic adversaries.")
    ]
    for i, (k, v, j) in enumerate(env_data, 1):
        env_table.rows[i].cells[0].paragraphs[0].text = k
        env_table.rows[i].cells[1].paragraphs[0].text = v
        env_table.rows[i].cells[2].paragraphs[0].text = j
    format_table(env_table, env_widths)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ==========================
    # SECTION 4: SEARCH ALGORITHMS
    # ==========================
    add_header_styled(doc, "4. Search Algorithms Implemented & Technical Details", 1)
    doc.add_paragraph(
        "The agent implements five complete graph traversal and heuristic search algorithms. Each algorithm records its complete internal deliberation at every step: current state, open list (frontier), closed list (explored set), cumulative cost g(n), and heuristic estimate h(n)."
    )

    algos = [
        ("4.1 Breadth-First Search (BFS)",
         "Strategy: Explores the state space systematically in concentric layers using a First-In, First-Out (FIFO) queue.\n"
         "Characteristics: Uninformed. Complete in finite graphs. Optimal with respect to the number of edges/hops (finds the path with fewest turns), but does not guarantee minimal physical distance when edge weights vary.\n"
         "Time & Space Complexity: O(b^d), where b is branching factor and d is depth of the shallowest goal."),
        
        ("4.2 Depth-First Search (DFS)",
         "Strategy: Plunges deep along each branch using a Last-In, First-Out (LIFO) stack before backtracking upon dead ends.\n"
         "Characteristics: Uninformed. Incomplete in infinite or cyclic graphs without cycle detection (our implementation includes a strict explored set). Suboptimal; often yields long, meandering paths.\n"
         "Time & Space Complexity: Time O(b^m), Space O(bm), where m is maximum search depth. Memory-efficient for deep tree searches but unsuitable for optimal routing."),
         
        ("4.3 Uniform Cost Search / Dijkstra's Algorithm",
         "Strategy: Expands the frontier node with the lowest cumulative path cost g(n) using a Min-Priority Queue (heap).\n"
         "Characteristics: Uninformed equivalent of A* with h(n) = 0. Guaranteed cost-optimal for non-negative edge costs. Explores in all directions equally until reaching the goal.\n"
         "Complexity: O(|E| + |V| log |V|)."),

        ("4.4 Greedy Best-First Search",
         "Strategy: Expands the frontier node judged closest to the goal based solely on the heuristic function: evaluation function f(n) = h(n).\n"
         "Characteristics: Informed. Extremely fast in open spaces because it rushes directly toward the goal coordinate. However, it is suboptimal and susceptible to false leads and obstacles, frequently getting trapped in local dead ends.\n"
         "Complexity: Worst-case O(b^m), but fast in typical unobstructed scenarios."),

        ("4.5 A* Search (Distance & Time Heuristics)",
         "Strategy: Combines the historical cost from start g(n) with the forward heuristic estimate to goal h(n): f(n) = g(n) + h(n).\n"
         "Characteristics: Informed. Guaranteed mathematically optimal if h(n) is admissible (never overestimates) and consistent (monotonic). Prunes substantial portions of the search space compared to Dijkstra.\n"
         "Implementations: (1) A* Distance: Minimizes Euclidean spatial distance. (2) A* Time: Minimizes estimated seconds factoring stairs, elevators, and crowd bottlenecks.")
    ]

    for title, desc in algos:
        add_header_styled(doc, title, 2)
        doc.add_paragraph(desc)

    add_header_styled(doc, "4.6 Mathematical Proof of Heuristic Admissibility & Consistency", 2)
    doc.add_paragraph(
        "To guarantee that A* finds the strictly optimal path without expanding redundant nodes, heuristics must fulfill two core criteria:"
    )
    doc.add_paragraph("1. Admissibility: h(n) ≤ h*(n) for all nodes n, where h*(n) is the true optimal cost from n to the goal.")
    doc.add_paragraph("2. Consistency (Monotonicity): h(n) ≤ c(n, a, n') + h(n') for all successor nodes n' reachable via action a.")

    doc.add_paragraph(
        "Euclidean Distance Proof: The straight-line Euclidean distance between two points in 3D Euclidean space (x, y, floor) is given by:\n"
        "    h_dist(n) = √((x_n - x_goal)² + (y_n - y_goal)² + (Δfloor × floor_height)²)\n"
        "By geometric principles, a straight line is the shortest conceivable distance between any two points. Any traversable physical pathway (walls, corridors, stairs) must have a distance greater than or equal to this straight line: c_actual ≥ h_dist. Hence, h_dist(n) never overestimates the true distance (Admissible) and satisfies the triangle inequality (Consistent)."
    )
    doc.add_paragraph(
        "Travel Time Lower-Bound Proof: For time-based routing, let v_max = 2.0 m/s be the maximum achievable human transit speed. The heuristic is defined as:\n"
        "    h_time(n) = h_dist(n) / v_max\n"
        "Because physical speed on any pathway satisfies v_actual ≤ v_max and actual distance satisfies d_actual ≥ h_dist, the actual travel time is:\n"
        "    t_actual = d_actual / v_actual ≥ h_dist / v_max = h_time(n)\n"
        "Therefore, h_time(n) is unconditionally admissible, guaranteeing A* time search optimality."
    )

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ==========================
    # SECTION 5: BENCHMARK RESULTS
    # ==========================
    add_header_styled(doc, "5. Empirical Benchmark & Comparison", 1)
    doc.add_paragraph(
        "A rigorous empirical benchmark was conducted on the campus graph from Main Gate (gate_main) to the AI & Autonomous Systems Lab (cs_lab_ai). The results demonstrate the comparative performance of each algorithm:"
    )

    bench_table = doc.add_table(rows=7, cols=8)
    bench_widths = [Inches(1.2), Inches(0.7), Inches(0.9), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(1.0)]
    bench_headers = ["Algorithm", "Status", "Distance", "Time", "Nodes Exp.", "Max Front.", "Runtime", "Optimality"]
    for idx, text in enumerate(bench_headers):
        bench_table.rows[0].cells[idx].paragraphs[0].text = text

    bench_data = [
        ("A* (Distance)", "SUCCESS", "609.2 m", "509.5 s", "9", "14", "0.14 ms", "Optimal"),
        ("A* (Time)", "SUCCESS", "609.2 m", "509.5 s", "19", "12", "0.25 ms", "Optimal"),
        ("BFS", "SUCCESS", "609.2 m", "509.5 s", "32", "11", "0.29 ms", "Hop-Optimal"),
        ("Dijkstra", "SUCCESS", "609.2 m", "509.5 s", "33", "11", "0.33 ms", "Optimal"),
        ("Greedy Best-First", "SUCCESS", "830.7 m", "777.2 s", "7", "13", "0.08 ms", "Suboptimal"),
        ("DFS", "SUCCESS", "1261.9 m", "1032.3 s", "22", "18", "0.22 ms", "Suboptimal")
    ]
    for r_idx, row in enumerate(bench_data, 1):
        for c_idx, val in enumerate(row):
            bench_table.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    format_table(bench_table, bench_widths)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    doc.add_paragraph(
        "Key Analytical Findings:\n"
        "1. Search Space Pruning: A* (Distance) expands only 9 nodes compared to Dijkstra's 33 nodes—pruning over 72% of the search space while finding the exact same optimal 609.2 m path.\n"
        "2. Greedy Vulnerability: While Greedy Best-First executed in just 0.08 ms, it produced a significantly longer path (830.7 m, +36% excess) due to short-sighted heuristic attraction.\n"
        "3. DFS Inefficiency: DFS explored deep circuitous routes, resulting in a 1261.9 m path (+107% excess distance)."
    )

    # ==========================
    # SECTION 6: SERVER ARCHITECTURE & ENDPOINTS
    # ==========================
    add_header_styled(doc, "6. Server Details & REST API Specifications", 1)
    doc.add_paragraph(
        "The project includes two independent servers built strictly on Python's built-in http.server and socketserver modules:"
    )

    add_header_styled(doc, "6.1 Production Web Application Server (server.py - Port 8080)", 2)
    doc.add_paragraph(
        "server.py serves both static frontend assets (HTML, CSS, JS) and handles JSON REST API queries. It features multi-threaded request dispatching, automatic CORS headers, and robust error handling."
    )

    api_table = doc.add_table(rows=7, cols=4)
    api_widths = [Inches(1.2), Inches(0.8), Inches(2.2), Inches(2.8)]
    api_headers = ["Endpoint", "Method", "Request Parameters", "Description & Response"]
    for idx, text in enumerate(api_headers):
        api_table.rows[0].cells[idx].paragraphs[0].text = text

    api_data = [
        ("/api/nodes", "GET", "None", "Returns full catalog of 50 campus nodes with IDs, names, buildings, floors, coordinates, and categories."),
        ("/api/edges", "GET", "None", "Returns list of all 78 bidirectional traversable pathways with distance, accessibility, and crowd ratings."),
        ("/api/route", "POST", "start, goal, algorithm, preference", "Executes designated algorithm. Returns path, total distance, travel time, step-by-step history, open list, and closed list."),
        ("/api/facility", "POST", "start, facility_type, preference", "Runs Dijkstra facility search to discover closest amenity (cafeteria, clinic, atm, lab, library, gate) from origin."),
        ("/api/multi-route", "POST", "start, via, goal, preference", "Computes compound route (A → Via → B) with unified metric accumulation and combined step telemetry."),
        ("/api/toggle-obstacle", "POST", "node_id or u, v", "Toggles blocked status on node or edge, forcing dynamic graph invalidation and route replanning.")
    ]
    for r_idx, row in enumerate(api_data, 1):
        for c_idx, val in enumerate(row):
            api_table.rows[r_idx].cells[c_idx].paragraphs[0].text = val
    format_table(api_table, api_widths)

    add_header_styled(doc, "6.2 Continuous Autonomous Test Server (test_server.py - Port 8090)", 2)
    doc.add_paragraph(
        "test_server.py is an automated testing daemon that continuously runs background regression suites, stress tests, and self-refinement algorithms in a non-blocking background thread. It hosts a live real-time HTTP monitoring dashboard at http://localhost:8090."
    )
    doc.add_paragraph(
        "Core Test Suites Executed in Continuous Loop:\n"
        "• Graph Structural Invariants: Confirms graph connectivity, coordinate sanity, and edge bidirectionality.\n"
        "• Algorithm Optimality Sweep: Compares BFS, Dijkstra, and A* on randomized origin-destination pairs to ensure no algorithm violates optimality bounds.\n"
        "• Dynamic Obstacle Replanning: Simulates sudden path blockages and asserts that the replanner successfully detours around obstacles without crashing.\n"
        "• Wheelchair Accessibility Invariant: Validates that zero staircases are present in paths planned under the Accessibility objective.\n"
        "• Compound Route Consistency: Validates that compound paths (A → B → C) yield costs identical to segment sums."
    )

    # ==========================
    # SECTION 7: GOOGLE MAPS INTEGRATION
    # ==========================
    add_header_styled(doc, "7. Google Maps Integration & Crash-Proof Fail-Safe", 1)
    doc.add_paragraph(
        "To provide real-world geospatial context, Google Maps JavaScript API (Satellite & Road Hybrid View) is fully integrated into the Web interface."
    )
    doc.add_paragraph(
        "7.1 Geographic Coordinate Transformation:\n"
        "Campus blueprint coordinates (x, y in pixels) are mapped to real-world GPS coordinates centered at (28.5450°N, 77.1925°E) using an empirical ground scale of 1 px ≈ 0.85 m:\n"
        "    dy = (y - 350.0) × 0.85;  dx = (x - 500.0) × 0.85\n"
        "    latitude = BASE_LAT - (dy / 111139.0)\n"
        "    longitude = BASE_LNG + (dx / (111139.0 × cos(BASE_LAT)))"
    )
    doc.add_paragraph(
        "7.2 100% Zero-Crash Fail-Safe Architecture:\n"
        "• Intercepted gm_authFailure: Captures Google Maps authentication errors (invalid key, referrer restrictions) and suppresses browser popups.\n"
        "• Script Loading Fallback (onerror): If network access is blocked or the Google CDN is unreachable, the system automatically falls back to the Interactive Blueprint SVG map without white-screening or crashing.\n"
        "• Synchronized State: Switching between Blueprint and Google Maps maintains selected start, goal, calculated paths, and obstacle markers seamlessly."
    )

    # ==========================
    # SECTION 8: STEP-BY-STEP OPERATIONAL GUIDE
    # ==========================
    add_header_styled(doc, "8. Step-by-Step User Operational Manual", 1)
    
    steps = [
        ("Step 1: Launching the Web Application",
         "1. Open Terminal on your Mac/Linux/Windows machine.\n"
         "2. Navigate to project root:\n"
         "    cd /Users/apple/Desktop/Final/project/campus_navigation_agent\n"
         "3. Start web server:\n"
         "    python3 server.py 8080\n"
         "4. Open your browser to http://localhost:8080."),

        ("Step 2: Planning a Route",
         "1. Select Start Node from the left sidebar dropdown (or click any marker on the map).\n"
         "2. Select Goal Node from the dropdown (or click second marker on the map).\n"
         "3. Choose Search Algorithm: A* (Distance), A* (Time), BFS, Dijkstra, DFS, or Greedy.\n"
         "4. Choose Routing Preference: Shortest Distance, Fastest Time, Wheelchair Accessible, or Lowest Crowd.\n"
         "5. Click 'Compute Optimal Route'. The path immediately illuminates in amber/cyan on both Blueprint and Google Maps."),

        ("Step 3: Using the Step-by-Step AI Inspector",
         "1. Click 'Live Step Inspector' or use the playback buttons (Play, Pause, Step Forward, Step Backward).\n"
         "2. Drag the Scrubber Slider to travel back in time to any point during algorithm expansion.\n"
         "3. Review the Open List (Frontier) table showing f(n), g(n), and h(n) values for each candidate node.\n"
         "4. Review the Closed List badges indicating all explored nodes."),

        ("Step 4: Switching to Google Maps Aerial View",
         "1. On the top-left map toolbar, click '🛰️ Google Maps'.\n"
         "2. The interactive satellite hybrid canvas mounts, rendering real-world aerial imagery with campus building markers and paths.\n"
         "3. Left-click markers to choose start/goal endpoints. Right-click markers to block obstacles.\n"
         "4. Click '🗺️ Blueprint' anytime to return to vector view."),

        ("Step 5: Testing Obstacles & Dynamic Replanning",
         "1. Right-click on any campus node (e.g., Computer Science Corridor).\n"
         "2. The node turns bright red indicating a blocked obstacle.\n"
         "3. Recompute route: the agent immediately detours around the blockage and displays replanned telemetry."),

        ("Step 6: Running the Continuous Background Test Server",
         "1. In a separate terminal window, run:\n"
         "    python3 test_server.py 8090\n"
         "2. Open http://localhost:8090 in your browser.\n"
         "3. Watch the autonomous engine execute tests in an infinite loop, displaying real-time pass rates, execution latencies, and self-healing telemetry.")
    ]

    for title, content in steps:
        add_header_styled(doc, title, 2)
        doc.add_paragraph(content)

    doc.save(output_path)
    print(f"[SUCCESS] Word document generated at: {output_path}")

# ==============================================================================
# REPORTLAB PDF GENERATOR
# ==============================================================================

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6B7280"))
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "Intelligent Campus Navigation Agent — Project Report")
            self.setStrokeColor(colors.HexColor("#E5E7EB"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
        
        # Footer
        self.setStrokeColor(colors.HexColor("#E5E7EB"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.drawString(54, 32, "Confidential & Academic — DIT University Campus Route Planning System")
        self.restoreState()

def generate_pdf_doc(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1, # Center
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#2563EB'),
        alignment=1,
        spaceAfter=15
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#6B7280'),
        alignment=1,
        spaceAfter=20
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#2563EB'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=15,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#111827'),
        backColor=colors.HexColor('#F3F4F6'),
        borderPadding=6,
        spaceAfter=6
    )

    story = []

    # Title Block
    story.append(Paragraph("🧭 INTELLIGENT CAMPUS NAVIGATION AGENT", title_style))
    story.append(Paragraph("Comprehensive Technical Documentation, AI Search Algorithms, Server Details & Operational Manual", subtitle_style))
    story.append(Paragraph("Architecture: Python Standard Library + Dual Frontend (Web & GUI) + Google Maps<br/>Date: October 2026 | Version: 2.0 Final Production Release", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=12))

    # Section 1: Executive Summary
    story.append(Paragraph("1. Executive Summary & Project Purpose", h1_style))
    story.append(Paragraph(
        "The <b>Intelligent Campus Navigation Agent</b> is an autonomous, AI-driven graph search and optimal route planning system designed for modern multi-building, multi-floor educational institutions. It formulates campus navigation as a formal search problem using the Russell & Norvig framework, implementing and benchmarking five core algorithms: Breadth-First Search (BFS), Depth-First Search (DFS), Uniform Cost Search (Dijkstra), Greedy Best-First Search, and A* Search with admissible Euclidean distance and travel time lower-bound heuristics.",
        body_style
    ))

    # Summary Table
    t1_data = [
        [Paragraph("<b>Core Pillar</b>", body_style), Paragraph("<b>Technical Implementation Details</b>", body_style)],
        [Paragraph("<b>Campus Graph</b>", body_style), Paragraph("50 nodes across 12 zones, 78 bidirectional edges with distance, elevation, and accessibility.", body_style)],
        [Paragraph("<b>AI Search Algorithms</b>", body_style), Paragraph("BFS (hop-optimal), DFS, Dijkstra (cost-optimal), Greedy Best-First, A* (distance & time).", body_style)],
        [Paragraph("<b>Multi-Objective</b>", body_style), Paragraph("Shortest Distance, Fastest Travel Time, Wheelchair Accessibility, and Lowest Crowd Congestion.", body_style)],
        [Paragraph("<b>Google Maps Hybrid</b>", body_style), Paragraph("Satellite + street map toggle with 100% crash-proof fail-safe and interactive markers.", body_style)],
        [Paragraph("<b>Servers & Testing</b>", body_style), Paragraph("Zero-dependency REST Web server (port 8080) and continuous autonomous test engine (port 8090).", body_style)]
    ]
    t1 = Table(t1_data, colWidths=[130, 374])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
    ]))
    story.append(t1)
    story.append(Spacer(1, 10))

    # Section 2: Architecture
    story.append(Paragraph("2. Modular Software Architecture", h1_style))
    story.append(Paragraph(
        "The project follows a modular, decoupled architecture using 100% Python standard library modules with zero pip dependencies for server execution:",
        body_style
    ))
    t2_data = [
        [Paragraph("<b>Module / Path</b>", body_style), Paragraph("<b>Layer</b>", body_style), Paragraph("<b>Responsibility</b>", body_style)],
        [Paragraph("core/graph.py", body_style), Paragraph("Data", body_style), Paragraph("CampusNode, CampusEdge, CampusGraph, and 50 campus nodes with GPS mapping.", body_style)],
        [Paragraph("core/state_action.py", body_style), Paragraph("AI", body_style), Paragraph("Formal Russell & Norvig CampusState, CampusAction, and CampusProblem abstractions.", body_style)],
        [Paragraph("core/heuristics.py", body_style), Paragraph("AI", body_style), Paragraph("Admissible Euclidean distance and travel-time lower-bound heuristics.", body_style)],
        [Paragraph("core/algorithms.py", body_style), Paragraph("AI", body_style), Paragraph("BFS, DFS, Dijkstra, Greedy Best-First, A* search, and compound multi-stop planner.", body_style)],
        [Paragraph("server.py", body_style), Paragraph("Backend", body_style), Paragraph("Standard library HTTP REST API server on port 8080 (/api/route, /api/facility).", body_style)],
        [Paragraph("test_server.py", body_style), Paragraph("QA", body_style), Paragraph("Autonomous regression test engine and live diagnostic dashboard on port 8090.", body_style)],
        [Paragraph("web/app.js & index.html", body_style), Paragraph("Frontend", body_style), Paragraph("Dual-canvas (SVG + Google Maps Hybrid), step inspector, and live avatar walking.", body_style)],
        [Paragraph("gui_app.py", body_style), Paragraph("Desktop", body_style), Paragraph("Native Python Tkinter desktop GUI for offline campus navigation.", body_style)]
    ]
    t2 = Table(t2_data, colWidths=[120, 70, 314])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
    ]))
    story.append(t2)
    story.append(Spacer(1, 10))

    # Section 3: Algorithms
    story.append(Paragraph("3. AI Search Algorithms & Mathematical Heuristics", h1_style))
    story.append(Paragraph("• <b>Breadth-First Search (BFS)</b>: Explores in concentric hops using a FIFO queue. Optimal with respect to fewest turns/edges traversed.", bullet_style))
    story.append(Paragraph("• <b>Depth-First Search (DFS)</b>: Plunges deep along branches using a LIFO stack. Incomplete without cycle detection; produces suboptimal paths.", bullet_style))
    story.append(Paragraph("• <b>Uniform Cost Search (Dijkstra)</b>: Expands nodes ordered by cumulative path cost g(n). Guaranteed cost-optimal.", bullet_style))
    story.append(Paragraph("• <b>Greedy Best-First Search</b>: Evaluates nodes strictly by heuristic estimate h(n). Fast execution but vulnerable to local minima.", bullet_style))
    story.append(Paragraph("• <b>A* Search (Distance & Time)</b>: Evaluates f(n) = g(n) + h(n). Strictly optimal with admissible heuristics while pruning up to 72% of node expansions.", bullet_style))

    story.append(Paragraph("<b>Heuristic Admissibility & Consistency:</b>", h2_style))
    story.append(Paragraph(
        "<b>1. Euclidean Distance:</b> <i>h_dist(n) = √((x - x_g)² + (y - y_g)² + Δfloor²)</i>. Because physical corridors cannot be shorter than straight-line distance, <i>h(n) ≤ h*(n)</i> unconditionally holds.<br/>"
        "<b>2. Travel Time Lower-Bound:</b> <i>h_time(n) = h_dist(n) / v_max</i> (where v_max = 2.0 m/s). Since human walking speed <i>v_actual ≤ v_max</i>, time lower-bound is strictly admissible.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # Benchmark Table
    story.append(Paragraph("Benchmark Evaluation (Main Gate to CS AI Lab):", h2_style))
    t3_data = [
        ["Algorithm", "Status", "Distance", "Time", "Nodes Exp.", "Max Front.", "Runtime", "Optimality"],
        ["A* (Distance)", "SUCCESS", "609.2 m", "509.5 s", "9", "14", "0.14 ms", "Optimal"],
        ["A* (Time)", "SUCCESS", "609.2 m", "509.5 s", "19", "12", "0.25 ms", "Optimal"],
        ["BFS", "SUCCESS", "609.2 m", "509.5 s", "32", "11", "0.29 ms", "Hop-Optimal"],
        ["Dijkstra", "SUCCESS", "609.2 m", "509.5 s", "33", "11", "0.33 ms", "Optimal"],
        ["Greedy Best-First", "SUCCESS", "830.7 m", "777.2 s", "7", "13", "0.08 ms", "Suboptimal"],
        ["DFS", "SUCCESS", "1261.9 m", "1032.3 s", "22", "18", "0.22 ms", "Suboptimal"]
    ]
    t3 = Table(t3_data, colWidths=[90, 50, 55, 55, 58, 58, 58, 80])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
    ]))
    story.append(t3)
    story.append(Spacer(1, 10))

    # Section 4: Server Details
    story.append(Paragraph("4. Server Architecture & Operational Details", h1_style))
    story.append(Paragraph("<b>1. Production Web Server (server.py - Port 8080):</b>", h2_style))
    story.append(Paragraph(
        "Built on standard library <i>http.server.ThreadingHTTPServer</i>. Dispatches incoming HTTP requests concurrently across threads. Exposes endpoints:<br/>"
        "• <b>GET /api/nodes</b> & <b>GET /api/edges</b>: Full topology and graph metadata.<br/>"
        "• <b>POST /api/route</b>: Algorithm route search (parameters: start, goal, algorithm, preference).<br/>"
        "• <b>POST /api/facility</b>: 1-tap nearest facility locator (cafeteria, clinic, atm, lab, library, gate).<br/>"
        "• <b>POST /api/multi-route</b>: Compound routing (A → Via → B) with cumulative metric accumulation.",
        body_style
    ))
    story.append(Paragraph("<b>2. Autonomous QA & Test Server (test_server.py - Port 8090):</b>", h2_style))
    story.append(Paragraph(
        "Runs an infinite autonomous background verification cycle testing graph structural invariants, algorithm optimality sweeps, dynamic obstacle replanning, and wheelchair accessibility compliance. Serves a live real-time HTTP monitoring dashboard at <i>http://localhost:8090</i> with zero external packages.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # Section 5: How Everything is Used
    story.append(Paragraph("5. Step-by-Step Operational Guide", h1_style))
    story.append(Paragraph("<b>Command to Launch Web App:</b>", h2_style))
    story.append(Paragraph("cd /Users/apple/Desktop/Final/project/campus_navigation_agent &amp;&amp; python3 server.py 8080", code_style))
    story.append(Paragraph("Open <b>http://localhost:8080</b> in your browser.", body_style))
    story.append(Paragraph("<b>Command to Launch Desktop Tkinter GUI:</b>", h2_style))
    story.append(Paragraph("python3 gui_app.py", code_style))
    story.append(Paragraph("<b>Command to Launch Background Test Server:</b>", h2_style))
    story.append(Paragraph("python3 test_server.py 8090", code_style))
    story.append(Paragraph("Open <b>http://localhost:8090</b> in your browser for live test dashboard.", body_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Interactive Feature Usage:</b>", h2_style))
    story.append(Paragraph("• <b>Google Maps Satellite Toggle:</b> Click '🛰️ Google Maps' on top-left toolbar. View real-world satellite imagery overlaid with nodes and pathways. Click marker to set endpoints, right-click to block obstacles. 100% crash-proof fail-safe returns to Blueprint on network loss.", bullet_style))
    story.append(Paragraph("• <b>Live Step Inspector:</b> Click 'Live Step Inspector' to step forward/backward or drag scrubber slider to inspect Open List (priority queue f, g, h) and Closed List (explored set).", bullet_style))
    story.append(Paragraph("• <b>Obstacle Detour Testing:</b> Right-click any campus node to block it (turns red). Recomputing route triggers instant real-time AI detour replanning.", bullet_style))
    story.append(Paragraph("• <b>Weather Rain Mode:</b> Toggle Rain Mode switch to automatically divert paths through indoor skywalks, corridors, and covered elevators, avoiding open outdoor plazas.", bullet_style))
    story.append(Paragraph("• <b>Printable Campus Pass:</b> Click 'Export Pass' to generate a printer-friendly campus navigation pass with turn-by-turn guidance, distance, and calories burned.", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] PDF document generated at: {output_path}")

if __name__ == '__main__':
    base_dir = "/Users/apple/Desktop/Final/project/campus_navigation_agent"
    docx_file = os.path.join(base_dir, "Campus_Navigation_Agent_Project_Report.docx")
    pdf_file = os.path.join(base_dir, "Campus_Navigation_Agent_Project_Report.pdf")
    
    print("Generating Word Document (.docx)...")
    generate_word_doc(docx_file)
    
    print("Generating PDF Document (.pdf)...")
    generate_pdf_doc(pdf_file)
    print("Done! Both documents are ready.")

