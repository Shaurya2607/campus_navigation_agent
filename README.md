# 🧭 DIT University Campus Navigation Agent
### Dehradun, Uttarakhand (Mussoorie Diversion Road)

> **An AI-powered graph search and route planning system that computes optimal routes across DIT University classrooms, laboratories, offices, academic blocks (Chanakya, Vishveshwarya, Vedanta, Charak), hostels, and amenities under dynamic real-world conditions.**

---

## 📌 Table of Contents
1. [Project Overview](#-project-overview)
2. [Key Tasks & Feature Checklist](#-key-tasks--feature-checklist)
3. [Formal AI Problem Formulation](#-formal-ai-problem-formulation)
4. [Search Algorithms Implemented](#-search-algorithms-implemented)
5. [Admissible & Consistent Heuristics](#-admissible--consistent-heuristics)
6. [Environment Classification (PEAS & 6 Dimensions)](#-environment-classification)
7. [Advanced Multi-Objective Routing Criteria](#-advanced-multi-objective-routing-criteria)
8. [Live Open List & Closed List Inspector](#-live-open-list--closed-list-inspector)
9. [Project Directory Architecture](#-project-directory-architecture)
10. [Quick Start & Launch Instructions](#-quick-start--launch-instructions)
11. [Benchmark Evaluation Results](#-benchmark-evaluation-results)

---

## 🚀 Project Overview

The **DIT University Campus Navigation Agent** is an end-to-end AI graph traversal and decision-making system tailored for the **DIT University, Dehradun** campus (Mussoorie Diversion Road, Makkawala, Dehradun, Uttarakhand). It maps the multi-building, multi-floor university campus into a connected topological graph, modeling campus locations as **states** and physical corridors, stairs, elevators, and outdoor walkways as **actions**.

The campus model encompasses 50 key locations across authentic DIT University blocks:
- **Chanakya Block** (School of Computing, CS & IT Lecture Theatres, Smart Classrooms, AI & Cybersecurity Labs)
- **Vishveshwarya Block** (Engineering Complex, Mechanical CAD/CAM & Robotics Workshops, VLSI Labs)
- **Vedanta Block** (VEDA Central Library, Reference Archives, 1200-seat Vedanta Grand Auditorium, Bookstore)
- **Central Administration Block** (Reception, Academic Dean, Admissions & Registrar Directorate)
- **Charak Block & Science Wing** (Pharmaceutical Chemistry, Applied Physics, Science Demonstration Theatres)
- **School of Management & Law** (MBA Classrooms, FinTech Terminal Lab, Moot Court Hall)
- **Student Housing** (Sarabhai & Bhabha Men's Residence, Sarojini & Kasturba Women's Residence, Late Night Canteen)
- **Campus Amenities & Sports** (Central Food Court & CCD, Student Activity Center, PNB Bank & ATM, DIT Sports Ground, Indoor Gymnasium, Aquatic Center)
- **Gates & Connectivity** (Main Gate on Mussoorie Diversion Road, North Transit Gate to Makkawala, Shivalik View Walkway)

The system implements classic and informed search algorithms (**BFS**, **DFS**, **A\*** with distance and time heuristics, **Dijkstra / Uniform Cost Search**, and **Greedy Best-First Search**), equipped with a real-time step-by-step inspector tracking the **Open List (Frontier)** and **Closed List (Explored Set)**.

It features both a **modern, responsive Web application** (with dark glassmorphic UI and interactive SVG canvas) and a native **Python Desktop GUI (Tkinter)**.

---

## ✅ Key Tasks & Feature Checklist

| Task # | Specification | Implementation Details |
|---|---|---|
| **1** | **Campus Graph Representation** | 50 nodes across 12 DIT University campus zones (Chanakya Block, Vishveshwarya Block, Vedanta Block, Charak Science Wing, Hostels, Innovation Hub, Management, Health Clinic, VEDA Library, Sports Complex, Food Court, Gates) with spatial coordinates, floors, and edge metadata. |
| **2** | **States & Actions Formalization** | $S = \langle \text{node\_id}, \text{building}, \text{floor}, (x, y) \rangle$, $A(s) = \text{Traverse}(u, v, \text{type}, \text{cost})$. Implements $Result(s, a)$ and $StepCost(s, a)$. |
| **3** | **BFS & DFS Search** | Uninformed FIFO queue search (BFS) for minimal hops and LIFO stack search (DFS) with complete step-by-step trajectory capture. |
| **4** | **A\* Search (Distance & Time)** | Informed heuristic search ($f = g + h$) with strictly admissible Euclidean distance and travel time lower-bound heuristics. |
| **5** | **Environment Classification** | Formal PEAS analysis and classification across Russell & Norvig's 6 dimensions: Fully/Partially Observable, Deterministic/Stochastic, Sequential, Dynamic, Discrete, Single-Agent. |
| **6** | **Obstacles & Blocked Paths** | Dynamic obstacle insertion on nodes and edges (construction, maintenance) with automatic detour routing and runtime replanning. |
| **7** | **Open/Closed List Inspector** | Live step-by-step playback, scrubber slider, priority queue inspection table ($f, g, h$), and explored set badge list. |
| **8** | **Python Graphical / Web Interface** | Dual interfaces provided: (1) Rich dark-glassmorphism Web interface via zero-dependency Python server (`server.py`), and (2) Native Desktop GUI via Python Tkinter (`gui_app.py`). |
| **New** | **Google Maps Satellite & Hybrid View** | Real-world aerial view toggle powered by Google Maps JavaScript API with interactive markers, route overlay, and 100% crash-proof fail-safe architecture. |
| **Adv.** | **Multi-Objective Routing** | Route selection optimized by: **Distance** (meters), **Time** (seconds), **Accessibility** (wheelchair-friendly, zero stairs), or **Crowd Level** (bypassing bottlenecks). |
| **New** | **Quick AI Nearest Facility** | One-tap Dijkstra discovery of the nearest Cafeteria, Health Clinic, ATM, Research Lab, Library, or Exit Gate from the current user position. |
| **New** | **Multi-Stop Compound Routing** | Compound routing with intermediate stopovers ($A \to \text{Via} \to B$), stitching optimal paths with cumulative metric telemetry. |
| **New** | **Weather Simulation (Rain Mode)** | Autonomously detects rain and diverts traversal to covered indoor hallways, skybridges, and elevators, avoiding unsheltered open plazas. |
| **New** | **Live Pedestrian Walking Simulation** | Animated traveler beacon avatar navigating physically along waypoints in real time with interactive status. |
| **New** | **Fitness Telemetry & Pass Export** | Step counter ($\approx \text{dist}/0.75\text{m}$) and calorie burning calculator, plus a 1-click printable campus navigation pass. |

---

## 📐 Formal AI Problem Formulation

Following the standard Russell & Norvig search framework:

1. **State Space ($S$)**:
   Each state $s \in S$ represents an exact physical location on campus:
   $$s = \langle \text{id}, \text{name}, \text{building}, \text{floor}, x, y, \text{category} \rangle$$
2. **Initial State ($s_0$)**:
   The user's starting point (e.g., `gate_main` or `admin_lobby`).
3. **Actions ($A(s)$)**:
   Walkable pathways originating from $s$:
   $$a = \text{Traverse}(s, s', \text{path\_type}, \text{distance}, \text{accessible}, \text{crowd\_level})$$
4. **Transition Model ($Result(s, a)$)**:
   Deterministic mapping yielding target state $s'$.
5. **Goal Test ($IsGoal(s)$)**:
   Evaluates whether $s.\text{id} == s_{\text{goal}}.\text{id}$.
6. **Path Cost ($c(s, a, s')$)**:
   Parameterized by user routing preference:
   - **Distance**: $c = a.\text{distance}$
   - **Time**: $c = \frac{a.\text{distance}}{\text{speed} / \text{crowd}} + \text{delay}_{\text{stairs/elevator}}$
   - **Accessibility**: $c = \infty$ if not accessible (stairs); else travel time
   - **Crowd Level**: $c = a.\text{distance} \times (\text{crowd\_level})^2$

---

## 🔍 Search Algorithms Implemented

```
                               ┌── Breadth-First Search (FIFO queue)
                               ├── Depth-First Search (LIFO stack)
Search Algorithms ─────────────┼── Uniform Cost Search / Dijkstra (f = g)
                               ├── Greedy Best-First Search (f = h)
                               └── A* Search (f = g + h) ──┬── Distance Heuristic
                                                           └── Time Heuristic
```

1. **Breadth-First Search (BFS)**:
   Explores shallowest unvisited nodes in concentric frontiers. Guarantees the fewest number of turns/hops.
2. **Depth-First Search (DFS)**:
   Explores deepest branches first. Memory-efficient but does not guarantee shortest or lowest-cost path.
3. **A\* Search (Distance Heuristic)**:
   Uses straight-line Euclidean distance to goal. Guarantees mathematical optimality while exploring significantly fewer nodes than uninformed methods.
4. **A\* Search (Time Heuristic)**:
   Evaluates path duration in seconds factoring crowd congestion and vertical floor transitions.
5. **Dijkstra / Uniform Cost Search**:
   Equivalent to A* with $h(n) = 0$. Expands nodes in order of cumulative path cost $g(n)$.
6. **Greedy Best-First Search**:
   Expands nodes closest to the goal according to heuristic $h(n)$ alone. Very fast, but vulnerable to dead ends and local optima.

---

## 🧮 Admissible & Consistent Heuristics

To ensure A* search produces an optimal solution, heuristic functions must be **admissible** (never overestimate the true cost to reach the goal: $h(n) \le h^*(n)$) and **consistent** (satisfy the triangle inequality $h(n) \le c(n, a, n') + h(n')$).

### 1. Euclidean Distance Heuristic
$$h_{\text{dist}}(n) = \sqrt{(x_n - x_{\text{goal}})^2 + (y_n - y_{\text{goal}})^2 + \Delta \text{floor}^2} \times \text{scale}$$
Because straight-line Euclidean distance is the shortest possible path between any two points in physical space, $h_{\text{dist}}(n) \le h^*(n)$ unconditionally holds.

### 2. Travel Time Lower-Bound Heuristic
$$h_{\text{time}}(n) = \frac{h_{\text{dist}}(n)}{v_{\text{max}}}$$
Where $v_{\text{max}} = 2.0\text{ m/s}$ (maximum sprint speed). Since actual walking speed on any pathway $v_{\text{actual}} \le v_{\text{max}}$, the minimum conceivable travel time is $\frac{\text{straight-line distance}}{v_{\text{max}}}$. Thus, $h_{\text{time}}(n) \le h^*(n)$ is guaranteed strictly admissible.

---

## 🌍 Environment Classification

### PEAS Specification
- **Performance Measure**: Minimized travel distance and transit time; 100% adherence to mobility constraints; minimal crowd congestion exposure; minimum computational node expansions.
- **Environment**: Multi-building university campus graph (indoor classrooms, labs, offices, corridors, stairs, elevators, outdoor avenues).
- **Actuators**: Route trajectory instructions, turn-by-turn guidance, dynamic detour re-planning.
- **Sensors**: Campus Wi-Fi / BLE beacon positioning, facility status feeds (door locks, elevator maintenance), crowd occupancy sensors.

### Russell & Norvig 6-Dimension Environment Classification

| Dimension | Classification | Theoretical & Practical Analysis |
|---|---|---|
| **Observability** | **Fully Observable** (Nominal) / **Partially Observable** (Real-world) | With campus GIS database access, the agent possesses full graph topology. In real-world deployment, sudden local disruptions (e.g., closed hallway) are only discovered when within sensor range, triggering dynamic replanning. |
| **Determinism** | **Deterministic** (Nominal) / **Stochastic** (Transit) | Edge transitions $(u \to v)$ are deterministic. However, travel durations exhibit stochastic variance due to elevator door cycles and corridor pedestrian density. |
| **Temporality** | **Sequential** | Decisions are strictly sequential: choosing to enter a building or ascend a staircase directly constrains the future state space and cumulative cost. |
| **Dynamics** | **Dynamic** | The environment changes while the agent plans: class bells cause sudden hallway crowd spikes, and maintenance crews can cordon off pathways mid-journey. |
| **Discreteness** | **Discrete** | Graph locations (classrooms, labs, junctions) and navigation time steps form a discrete state-action space. |
| **Agency** | **Single-Agent** with Multi-Agent Background | The navigation agent operates autonomously, treating human crowds as dynamic environmental impedance. |

---

## 👥 Advanced Multi-Objective Routing Criteria

Users can switch optimization objectives in real time:

1. **📏 Shortest Distance**: Minimizes total physical meters traversed across the campus.
2. **⏱️ Fastest Travel Time**: Prioritizes direct level walkways and factors in stair climbing penalties vs. elevator waiting times.
3. **♿ Wheelchair Accessibility (ADA Compliant)**:
   - Completely filters out staircases (`accessible: False`).
   - Automatically re-routes travelers through wheelchair-accessible ramps and elevators (`accessible: True`).
4. **👥 Lowest Crowd Level**:
   - Heavily penalizes congested hallways and peak dining halls ($c = \text{dist} \times \text{crowd}^2$).
   - Directs users along scenic garden walkways and quiet corridors during class-change intervals.

---

## 🔬 Live Open List & Closed List Inspector

During algorithm execution or playback, the agent exposes its inner deliberations:

- **Open List (Frontier)**: A real-time priority queue table displaying every node awaiting expansion along with its:
  - $f(n)$: Estimated total path cost ($f = g + h$)
  - $g(n)$: Actual cost incurred from start to node $n$
  - $h(n)$: Heuristic estimate from node $n$ to goal
- **Closed List (Explored Set)**: The set of all nodes that have already been expanded, ensuring no redundant work or infinite loops.
- **Live Playback Controls**: Play, pause, step forward, step backward, scrub slider (0 to $N$), and adjustable playback speeds ($1\times, 2\times, 5\times$).

---

## 📁 Project Directory Architecture

```
campus_navigation_agent/
├── core/
│   ├── __init__.py               # Package exports
│   ├── graph.py                  # CampusGraph, CampusNode, CampusEdge, default campus topology
│   ├── state_action.py           # Formal AI State, Action, CampusProblem definitions
│   ├── heuristics.py             # Admissible Euclidean, Manhattan, and Time heuristics
│   ├── algorithms.py             # BFS, DFS, A*, Dijkstra, Greedy Best-First implementations
│   └── environment.py            # PEAS formulation, 6-D classification, dynamic simulation
├── web/
│   ├── index.html                # Semantic HTML5 UI with SVG map canvas and inspector modals
│   ├── styles.css                # Dark glassmorphic design system and responsive styles
│   └── app.js                    # Interactive SVG rendering, playback engine, and API client
├── server.py                     # Zero-dependency standard library Python HTTP & REST API server
├── gui_app.py                    # Standalone Tkinter desktop graphical interface
├── test_server.py                # Autonomous continuous test server & live diagnostic dashboard (Port 8090)
├── test_navigation.py            # Unit test suite (9 tests, 100% pass rate)
├── campus_data.json              # Full JSON topology export of the university campus
├── run.sh                        # 1-click execution launcher
└── README.md                     # Comprehensive project documentation
```

---


## MongoDB setup

The web server now reads campus nodes and pathways from MongoDB.

1. Install dependencies from the project folder:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and set your MongoDB Atlas connection string in `MONGO_URI`. Keep `.env` private and do not commit it.
3. Import the project's current graph once:
   ```bash
   python seed_mongodb.py
   ```
   The importer refuses to run if either campus collection already contains records; it does not delete existing data.
4. Start the app:
   ```bash
   python server.py 8080
   ```
5. Verify the database connection and record counts at `http://localhost:8080/api/database-status`.

MongoDB collections: `campus_nodes` and `campus_edges`. The server loads them at startup and saves node/pathway state changes (such as obstacles and rush-hour crowd levels). The one-time importer uses the graph already defined in `core/graph.py`; its locations and coordinates should be independently verified before real-world navigation.

## ⚡ Quick Start & Launch Instructions

All components run with **Python 3 standard library** (no external `pip` packages required!).

### 1. Launch the Interactive Web Application (Recommended)
```bash
cd campus_navigation_agent
python3 server.py 8080
```
Open **[http://localhost:8080](http://localhost:8080)** in your web browser.

### 2. Launch the Desktop Tkinter GUI
```bash
python3 gui_app.py
```

### 3. Launch Continuous Autonomous Test Server (Loop & Live Diagnostics)
```bash
python3 test_server.py 8090
```
Open **[http://localhost:8090](http://localhost:8090)** to view the live auto-refreshing test dashboard.

### 4. Run the Unit Test Suite
```bash
python3 test_navigation.py
```

### 5. Interactive 1-Click Launcher
```bash
./run.sh
```

---

## 📊 Benchmark Evaluation Results

Benchmark run from **Main Campus Gate** (`gate_main`) to **AI & Autonomous Systems Lab** (`cs_lab_ai`):

| Algorithm | Status | Path Distance | Travel Time | Nodes Expanded | Max Frontier | Runtime | Optimality Guarantee |
|---|---|---|---|---|---|---|---|
| **A\* (Distance)** | **SUCCESS** | **609.2 m** | **509.5 s** | **9** | **14** | **0.14 ms** | **Optimal** |
| **A\* (Time)** | **SUCCESS** | **609.2 m** | **509.5 s** | **19** | **12** | **0.25 ms** | **Optimal** |
| **BFS** | **SUCCESS** | 609.2 m | 509.5 s | 32 | 11 | 0.29 ms | Fewest Hops |
| **Dijkstra** | **SUCCESS** | 609.2 m | 509.5 s | 33 | 11 | 0.33 ms | Optimal |
| **Greedy Best-First**| **SUCCESS** | 830.7 m | 777.2 s | 7 | 13 | 0.08 ms | Suboptimal |
| **DFS** | **SUCCESS** | 1261.9 m | 1032.3 s | 22 | 18 | 0.22 ms | Suboptimal |

### Key Observations:
- **A\* Efficiency**: A* finds the optimal 609.2m route in only **9 node expansions**, pruning over **72%** of the search space compared to Dijkstra (33 expansions) and BFS (32 expansions).
- **Accessibility Routing**: When switching to **Accessibility** preference, the agent autonomously avoids the rapid-access staircase (`cs_stairs_f1` / `cs_stairs_f2`) and routes via the elevator (`cs_elevator_f1` / `cs_elevator_f2`), guaranteeing 100% wheelchair compliance.
