"""
Campus Graph representation for the Intelligent Campus Navigation Agent.
Represents university locations as nodes and pathways as edges.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Tuple
import math
import json


@dataclass
class CampusNode:
    """Represents a campus location (classroom, lab, office, department, gate, etc.)"""
    id: str
    name: str
    building: str
    floor: int
    category: str  # 'Classroom', 'Laboratory', 'Office', 'Department', 'Facility', 'Entrance'
    x: float       # Canvas/map X coordinate (0-1000)
    y: float       # Canvas/map Y coordinate (0-700)
    description: str = ""
    is_blocked: bool = False
    block_reason: str = ""
    lat: float = 0.0
    lng: float = 0.0

    def __post_init__(self):
        if self.lat == 0.0 or self.lng == 0.0:
            # Base coordinates precisely centered on DIT University campus footprint (Mussoorie Diversion Road, Dehradun)
            # Scaled for compact 21-acre campus so nodes stay strictly within campus perimeter
            BASE_LAT = 30.4000
            BASE_LNG = 78.0786
            dy = (self.y - 350.0) * 0.32
            dx = (self.x - 500.0) * 0.22
            self.lat = round(BASE_LAT - (dy / 111139.0), 6)
            self.lng = round(BASE_LNG + (dx / (111139.0 * math.cos(math.radians(BASE_LAT)))), 6)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CampusEdge:
    """Represents a walkable pathway connecting two campus locations."""
    source: str
    target: str
    distance: float          # Distance in meters
    path_type: str           # 'hallway', 'walkway', 'stairs', 'elevator', 'plaza', 'garden'
    accessible: bool = True  # True if wheelchair/mobility accessible (False for stairs)
    crowd_level: float = 1.0 # 1.0 = low (free flowing), 1.8 = moderate, 3.0 = congested
    is_blocked: bool = False
    block_reason: str = ""
    base_speed: float = 1.4  # Average walking speed in m/s (~5 km/h)
    bidirectional: bool = True

    @property
    def travel_time(self) -> float:
        """Estimated base travel time in seconds factoring crowd congestion."""
        # Speed slows down proportionally with crowd level
        effective_speed = max(0.4, self.base_speed / self.crowd_level)
        time = self.distance / effective_speed
        if self.path_type == 'stairs':
            time += 5.0  # Stairs penalty
        elif self.path_type == 'elevator':
            time += 15.0 # Average elevator wait & door cycle
        return round(time, 1)

    def to_dict(self) -> dict:
        data = asdict(self)
        data['travel_time'] = self.travel_time
        return data


class CampusGraph:
    """Graph structure holding all university campus nodes and pathways."""
    def __init__(self):
        self.nodes: Dict[str, CampusNode] = {}
        self.edges: Dict[str, List[CampusEdge]] = {}  # source -> list of outgoing edges

    def add_node(self, node: CampusNode) -> None:
        self.nodes[node.id] = node
        if node.id not in self.edges:
            self.edges[node.id] = []

    def add_edge(self, edge: CampusEdge) -> None:
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise ValueError(f"Both {edge.source} and {edge.target} must exist before adding an edge.")

        self.edges[edge.source].append(edge)

        if edge.bidirectional:
            # Create the reverse edge with same attributes
            rev_edge = CampusEdge(
                source=edge.target,
                target=edge.source,
                distance=edge.distance,
                path_type=edge.path_type,
                accessible=edge.accessible,
                crowd_level=edge.crowd_level,
                is_blocked=edge.is_blocked,
                block_reason=edge.block_reason,
                base_speed=edge.base_speed,
                bidirectional=True
            )
            if edge.target not in self.edges:
                self.edges[edge.target] = []
            self.edges[edge.target].append(rev_edge)

    def get_node(self, node_id: str) -> Optional[CampusNode]:
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id: str, respect_blocks: bool = True, accessible_only: bool = False) -> List[Tuple[CampusNode, CampusEdge]]:
        """Return list of (neighbor_node, edge) for a given node, filtering blocked paths if requested."""
        if node_id not in self.nodes or (respect_blocks and self.nodes[node_id].is_blocked):
            return []

        neighbors = []
        for edge in self.edges.get(node_id, []):
            if respect_blocks and edge.is_blocked:
                continue
            if accessible_only and not edge.accessible:
                continue

            target_node = self.nodes.get(edge.target)
            if not target_node:
                continue
            if respect_blocks and target_node.is_blocked:
                continue

            neighbors.append((target_node, edge))
        return neighbors

    def set_node_blocked(self, node_id: str, blocked: bool, reason: str = "") -> bool:
        if node_id in self.nodes:
            self.nodes[node_id].is_blocked = blocked
            self.nodes[node_id].block_reason = reason if blocked else ""
            return True
        return False

    def set_edge_blocked(self, u: str, v: str, blocked: bool, reason: str = "") -> bool:
        """Block or unblock the edge between u and v in both directions."""
        modified = False
        for edge in self.edges.get(u, []):
            if edge.target == v:
                edge.is_blocked = blocked
                edge.block_reason = reason if blocked else ""
                modified = True
        for edge in self.edges.get(v, []):
            if edge.target == u:
                edge.is_blocked = blocked
                edge.block_reason = reason if blocked else ""
                modified = True
        return modified

    def set_edge_crowd(self, u: str, v: str, crowd_level: float) -> bool:
        """Set crowd multiplier on edge between u and v."""
        modified = False
        for edge in self.edges.get(u, []):
            if edge.target == v:
                edge.crowd_level = crowd_level
                modified = True
        for edge in self.edges.get(v, []):
            if edge.target == u:
                edge.crowd_level = crowd_level
                modified = True
        return modified

    def reset_all_blocks(self) -> None:
        """Clear all blockages from nodes and edges."""
        for node in self.nodes.values():
            node.is_blocked = False
            node.block_reason = ""
        for edge_list in self.edges.values():
            for edge in edge_list:
                edge.is_blocked = False
                edge.block_reason = ""

    def to_dict(self) -> dict:
        """Serialize graph to dictionary for JSON output."""
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [
                edge.to_dict()
                for edge_list in self.edges.values()
                for edge in edge_list
                if edge.source < edge.target  # Avoid duplicate undirected edges in payload
            ]
        }


def create_default_campus_graph() -> CampusGraph:
    """
    Constructs a comprehensive, realistic university campus graph.
    Includes Classrooms, Labs, Offices, Departments, Facilities, and Gates.
    Features indoor multi-floor pathways, elevators, staircases, and outdoor avenues.
    """
    g = CampusGraph()

    # --- 1. Nodes Definition (x in 0-1000, y in 0-700) ---
    # Centered on DIT University, Mussoorie Diversion Road, Dehradun
    nodes_data = [
        # Entrances & Gates
        CampusNode("gate_main", "Main Campus Gate (Mussoorie Diversion Rd)", "Outdoor", 0, "Entrance", 120, 620, "South main vehicular and pedestrian entrance from Mussoorie Diversion Road with security guard outpost"),
        CampusNode("gate_north", "North Transit Gate (Makkawala)", "Outdoor", 0, "Entrance", 880, 80, "North gate connecting towards Makkawala Road and local university transit stops"),
        CampusNode("south_parking", "South Visitor & Student Parking", "Outdoor", 0, "Facility", 220, 640, "Two-wheeler and four-wheeler campus parking lot with EV charging station"),

        # Central Crossroads & Outdoors
        CampusNode("central_plaza", "DIT Central Amphitheatre Quad", "Outdoor", 0, "Facility", 500, 360, "Central open-air amphitheatre and university assembly plaza surrounded by pine greenery"),
        CampusNode("fountain_cross", "Clock Tower Crossway", "Outdoor", 0, "Facility", 520, 240, "Central pedestrian intersection connecting Chanakya, Vedanta, and Vishveshwarya blocks"),
        CampusNode("garden_walk", "Shivalik View Botanical Walkway", "Outdoor", 0, "Facility", 340, 480, "Scenic landscaped foothill walkway with accessible paved pathways"),

        # Chanakya Block - School of Computing & Information Technology (West)
        CampusNode("cs_entrance", "Chanakya Block Main Entrance", "Chanakya Block", 1, "Department", 220, 320, "Grand glass entrance to Chanakya Block housing Computer Science & Information Technology"),
        CampusNode("cs_101", "Chanakya Lecture Theatre C-101", "Chanakya Block", 1, "Classroom", 140, 270, "180-seat smart lecture theatre for computer science core courses"),
        CampusNode("cs_102", "Chanakya Smart Classroom C-102", "Chanakya Block", 1, "Classroom", 140, 370, "Interactive multimedia smart classroom with collaborative group pods"),
        CampusNode("cs_stairs_f1", "Chanakya West Staircase (F1)", "Chanakya Block", 1, "Facility", 200, 230, "Rapid-access concrete staircase (stairs only, non-wheelchair) to 2nd floor"),
        CampusNode("cs_elevator_f1", "Chanakya Central Lift (F1)", "Chanakya Block", 1, "Facility", 260, 240, "Wheelchair accessible passenger elevator serving Floors 1 and 2"),
        CampusNode("cs_stairs_f2", "Chanakya West Staircase (F2)", "Chanakya Block", 2, "Facility", 200, 190, "Second-floor staircase landing in Chanakya computing wing"),
        CampusNode("cs_elevator_f2", "Chanakya Central Lift (F2)", "Chanakya Block", 2, "Facility", 260, 190, "Second-floor elevator vestibule with tactile braille navigation cues"),
        CampusNode("cs_lab_ai", "DIT AI & Deep Learning Research Lab", "Chanakya Block", 2, "Laboratory", 120, 170, "High-performance GPU computing facility for machine learning, data science & robotics"),
        CampusNode("cs_lab_cyber", "Cybersecurity & Cloud Computing Lab", "Chanakya Block", 2, "Laboratory", 120, 110, "Advanced network defense, cyber forensics, and cloud infrastructure testbed"),
        CampusNode("cs_hod_office", "Head of CSE & IT Department Office", "Chanakya Block", 2, "Office", 280, 140, "School of Computing department head executive consultation suite"),

        # Central Administration & Academic Registry (South-West)
        CampusNode("admin_lobby", "Administrative Block Reception", "Admin Building", 1, "Department", 340, 580, "University central reception lobby, help desk, and student enquiry counters"),
        CampusNode("dean_office", "Dean of Academic Affairs Office", "Admin Building", 2, "Office", 340, 640, "Office of Academic Affairs, Vice Chancellor secretariat, and faculty affairs"),
        CampusNode("admissions_office", "DIT Admissions & Registrar Directorate", "Admin Building", 1, "Office", 420, 600, "Central student admissions, registrar records, and fee counter"),

        # Vishveshwarya Block - Engineering & Robotics Complex (Center-North)
        CampusNode("eng_atrium", "Vishveshwarya Grand Atrium", "Vishveshwarya Block", 1, "Department", 480, 150, "Central engineering exhibition atrium showcasing student SAE/Robotics projects"),
        CampusNode("ee_circuits_lab", "Electrical & Embedded Systems Lab", "Vishveshwarya Block", 1, "Laboratory", 390, 110, "VLSI design benches, oscilloscope stations, and embedded microcontrollers"),
        CampusNode("mech_workshop", "Advanced Mechanical & CAD Workshop", "Vishveshwarya Block", 1, "Laboratory", 580, 110, "CNC machine tools, 3D additive manufacturing, and robotics fabrication workshop"),
        CampusNode("eng_hall_204", "Vishveshwarya Lecture Hall V-204", "Vishveshwarya Block", 2, "Classroom", 480, 70, "Acoustically engineered amphitheatre lecture hall on Floor 2"),

        # Vedanta Block - Central Library & Auditorium Hub (Center-East)
        CampusNode("lib_foyer", "VEDA Central Library Foyer", "Vedanta Block", 1, "Facility", 660, 320, "RFID automated gate check-in, circulation desk, and reading catalog access"),
        CampusNode("lib_group_study", "VEDA Collaborative Discussion Pods", "Vedanta Block", 1, "Classroom", 740, 360, "Sound-insulated study rooms for research group collaborations and capstone teams"),
        CampusNode("lib_quiet_hall", "VEDA Silent Research Archive", "Vedanta Block", 2, "Facility", 660, 240, "Quiet study hall with journals, dissertations, and digital library e-terminals"),
        CampusNode("lib_elevator", "Vedanta Block Glass Elevator", "Vedanta Block", 1, "Facility", 700, 280, "Panoramic wheelchair accessible lift connecting VEDA library reading floors"),

        # Charak Block - Sciences & Pharmacy Wing (East)
        CampusNode("sci_lobby", "Charak Wing Entrance Lobby", "Charak Block", 1, "Department", 820, 260, "School of Pharmacy and Applied Sciences departmental exhibition foyer"),
        CampusNode("chem_lab", "Pharmaceutical Chemistry Lab", "Charak Block", 1, "Laboratory", 900, 240, "Chemical formulation fume hoods, synthesis counters, and analytics equipment"),
        CampusNode("physics_lab", "Applied Physics & Optics Lab", "Charak Block", 2, "Laboratory", 900, 340, "Interferometer tables, fiber optics benches, and laser physics instruments"),
        CampusNode("sci_hall_101", "Charak Science Hall CH-101", "Charak Block", 1, "Classroom", 840, 400, "Tiered demonstration lecture theater for pharmaceutical sciences"),

        # Student Activity Center & Food Court (South-East)
        CampusNode("student_union", "DIT Student Activity Center (SAC)", "Student Center", 1, "Facility", 680, 480, "Student clubs headquarters, recreational lounge, and cultural society hub"),
        CampusNode("cafeteria_main", "Central Food Court & Café Coffee Day", "Student Center", 1, "Facility", 780, 520, "Multi-vendor food court featuring CCD, south Indian snacks, and meals hub"),
        CampusNode("health_center", "DIT Health Dispensary & Clinic", "Student Center", 1, "Facility", 860, 580, "Resident doctor medical dispensary, triage beds, and first-aid support"),

        # Sports Pavilion & Auditorium (South-East)
        CampusNode("sports_arena", "DIT Indoor Sports Complex", "Sports Pavilion", 1, "Facility", 640, 620, "Badminton courts, table tennis hall, and fitness gymnasium"),
        CampusNode("auditorium", "Vedanta Grand Auditorium", "Vedanta Block", 1, "Classroom", 480, 480, "1200-seat state-of-the-art university convocation and cultural auditorium"),

        # Innovation Hub & Technology Business Incubator (North-West)
        CampusNode("incubator_hub", "DIT Technology Business Incubator", "Innovation Hub", 1, "Department", 50, 70, "Startup incubation center, pitch room, and entrepreneurial mentoring space"),
        CampusNode("maker_space", "IoT & Rapid Prototyping MakerSpace", "Innovation Hub", 1, "Laboratory", 50, 140, "Laser cutting, PCB milling, 3D printing, and hardware prototyping bench"),

        # Student Residential Hostels (West-South)
        CampusNode("hostel_boys", "Sarabhai & Bhabha Men's Hostel", "Student Housing", 1, "Facility", 50, 460, "Multi-floor boys' hostel block with recreation room and study spaces"),
        CampusNode("hostel_girls", "Sarojini & Kasturba Women's Hostel", "Student Housing", 1, "Facility", 50, 540, "Secure women's hostel residence with biometric gate security and lounge"),
        CampusNode("night_canteen", "DIT Night Canteen & Maggi Point", "Student Housing", 1, "Facility", 120, 500, "Popular late-night student food stall serving hot beverages and snacks"),

        # School of Management & Law (East-South)
        CampusNode("mgmt_block", "School of Management & Law", "Management Wing", 1, "Department", 930, 480, "Case-study classrooms and faculty offices for MBA and Law programs"),
        CampusNode("fintech_lab", "Management Analytics & FinTech Lab", "Management Wing", 1, "Laboratory", 930, 550, "Market simulation terminal room, analytics suites, and computational lab"),
        CampusNode("moot_court", "DIT Law School Moot Court Hall", "Management Wing", 2, "Classroom", 930, 420, "Simulated judicial courtroom for moot court arguments and legal advocacy"),

        # Health Complex & Emergency Bay (East-South)
        CampusNode("pharmacy", "24/7 DIT Campus Pharmacy", "Health Complex", 1, "Facility", 800, 630, "Round-the-clock emergency prescription counter and medical supplies"),
        CampusNode("ambulance_bay", "DIT Emergency Ambulance Bay", "Health Complex", 1, "Facility", 890, 630, "Dedicated 24/7 ambulance dock providing urgent off-campus transfer to Dehradun hospitals"),

        # Athletics & Outdoor Sports
        CampusNode("cricket_ground", "DIT Cricket & Sports Ground", "Sports Pavilion", 0, "Facility", 530, 640, "Lush green cricket pitch, soccer field, and 400m athletic running track"),
        CampusNode("swimming_pool", "DIT Aquatic Center", "Sports Pavilion", 0, "Facility", 630, 670, "Olympic-dimension outdoor swimming pool with coach facility"),

        # Student Amenities & Banking
        CampusNode("bank_atm", "Campus Bank & 24/7 ATM (PNB)", "Student Center", 1, "Facility", 620, 420, "On-campus Punjab National Bank branch and 24-hour ATM kiosk"),
        CampusNode("bookstore", "DIT Book Depot & Stationery Shop", "Vedanta Block", 1, "Facility", 740, 260, "Official university textbooks, engineering drafting supplies, and uniform store")
    ]

    for n in nodes_data:
        g.add_node(n)

    # Helper to calculate Euclidean distance in meters (scaled for DIT campus ~ 1 px ≈ 0.28 meter)
    def calc_dist(id1: str, id2: str) -> float:
        n1 = g.nodes[id1]
        n2 = g.nodes[id2]
        pixel_dist = math.hypot(n1.x - n2.x, n1.y - n2.y)
        return round(pixel_dist * 0.28, 1)

    # --- 2. Pathways & Edges Definition ---
    edges_data = [
        # South Gates & Parking to Admin & Quad
        ("gate_main", "south_parking", "walkway", True, 1.1),
        ("gate_main", "admin_lobby", "walkway", True, 1.2),
        ("south_parking", "garden_walk", "walkway", True, 1.0),
        ("admin_lobby", "dean_office", "stairs", False, 1.0),
        ("admin_lobby", "admissions_office", "hallway", True, 1.4),
        ("admin_lobby", "garden_walk", "walkway", True, 1.0),
        ("admissions_office", "central_plaza", "walkway", True, 1.2),

        # Garden walk & Western connections
        ("garden_walk", "central_plaza", "walkway", True, 1.1),
        ("garden_walk", "cs_entrance", "walkway", True, 1.2),

        # CS Building (Interior & Multi-floor)
        ("cs_entrance", "cs_101", "hallway", True, 1.3),
        ("cs_entrance", "cs_102", "hallway", True, 1.2),
        ("cs_entrance", "cs_stairs_f1", "hallway", True, 1.3),
        ("cs_entrance", "cs_elevator_f1", "hallway", True, 1.1),
        ("cs_stairs_f1", "cs_stairs_f2", "stairs", False, 1.5),      # Stairs not wheelchair accessible!
        ("cs_elevator_f1", "cs_elevator_f2", "elevator", True, 1.0),  # Elevator is accessible
        ("cs_stairs_f2", "cs_lab_ai", "hallway", True, 1.2),
        ("cs_elevator_f2", "cs_lab_ai", "hallway", True, 1.1),
        ("cs_lab_ai", "cs_lab_cyber", "hallway", True, 1.1),
        ("cs_elevator_f2", "cs_hod_office", "hallway", True, 1.0),
        ("cs_stairs_f2", "cs_hod_office", "hallway", True, 1.1),

        # CS to Central Quad & Engineering
        ("cs_entrance", "central_plaza", "plaza", True, 1.5),
        ("cs_hod_office", "eng_atrium", "walkway", True, 1.0), # Skybridge connector
        ("cs_101", "fountain_cross", "walkway", True, 1.1),

        # Central Quad to Nodes
        ("central_plaza", "fountain_cross", "plaza", True, 1.6), # Very busy crossroads
        ("central_plaza", "auditorium", "plaza", True, 1.3),
        ("central_plaza", "lib_foyer", "walkway", True, 1.8),
        ("central_plaza", "student_union", "walkway", True, 1.7),

        # Fountain Cross to Engineering & Library
        ("fountain_cross", "eng_atrium", "walkway", True, 1.3),
        ("fountain_cross", "lib_foyer", "walkway", True, 1.4),

        # Engineering Building
        ("eng_atrium", "ee_circuits_lab", "hallway", True, 1.1),
        ("eng_atrium", "mech_workshop", "hallway", True, 1.2),
        ("eng_atrium", "eng_hall_204", "stairs", False, 1.3), # Mezzanine stairs
        ("eng_atrium", "gate_north", "walkway", True, 1.2),
        ("mech_workshop", "gate_north", "walkway", True, 1.0),

        # Library Complex
        ("lib_foyer", "lib_group_study", "hallway", True, 1.4),
        ("lib_foyer", "lib_elevator", "hallway", True, 1.1),
        ("lib_foyer", "lib_quiet_hall", "stairs", False, 1.0), # Spiral library stairs
        ("lib_elevator", "lib_quiet_hall", "elevator", True, 1.0), # Elevator to quiet zone
        ("lib_foyer", "sci_lobby", "walkway", True, 1.2),
        ("lib_group_study", "student_union", "walkway", True, 1.5),

        # Science Block
        ("sci_lobby", "chem_lab", "hallway", True, 1.1),
        ("sci_lobby", "physics_lab", "stairs", False, 1.0), # Science stairs
        ("sci_lobby", "sci_hall_101", "hallway", True, 1.3),
        ("chem_lab", "gate_north", "walkway", True, 1.1),
        ("physics_lab", "sci_hall_101", "stairs", False, 1.1),

        # Student Union & Food Court
        ("student_union", "cafeteria_main", "hallway", True, 2.6), # Heavy crowd!
        ("cafeteria_main", "health_center", "hallway", True, 1.2),
        ("student_union", "auditorium", "walkway", True, 1.3),
        ("cafeteria_main", "sports_arena", "walkway", True, 1.4),

        # Sports & Auditorium & South Parking
        ("auditorium", "sports_arena", "walkway", True, 1.1),
        ("sports_arena", "south_parking", "walkway", True, 1.0),
        ("health_center", "gate_north", "walkway", True, 1.0),

        # Innovation Hub connections
        ("incubator_hub", "cs_lab_cyber", "walkway", True, 1.0),
        ("incubator_hub", "maker_space", "hallway", True, 1.1),
        ("maker_space", "cs_lab_ai", "hallway", True, 1.1),

        # Residential Housing connections
        ("hostel_boys", "hostel_girls", "walkway", True, 1.2),
        ("hostel_boys", "night_canteen", "walkway", True, 1.3),
        ("hostel_girls", "night_canteen", "walkway", True, 1.3),
        ("night_canteen", "south_parking", "walkway", True, 1.2),
        ("night_canteen", "cs_102", "walkway", True, 1.1),
        ("hostel_boys", "garden_walk", "walkway", True, 1.0),

        # Management & Law Wing connections
        ("mgmt_block", "cafeteria_main", "walkway", True, 1.5),
        ("mgmt_block", "fintech_lab", "hallway", True, 1.1),
        ("mgmt_block", "moot_court", "stairs", False, 1.2), # Stairs up to moot court
        ("mgmt_block", "sci_hall_101", "walkway", True, 1.3),

        # Health Complex & Pharmacy connections
        ("health_center", "pharmacy", "hallway", True, 1.1),
        ("pharmacy", "ambulance_bay", "walkway", True, 1.0),
        ("health_center", "ambulance_bay", "hallway", True, 1.0),

        # Sports Pavilion expansion
        ("sports_arena", "cricket_ground", "walkway", True, 1.1),
        ("auditorium", "cricket_ground", "walkway", True, 1.1),
        ("sports_arena", "swimming_pool", "hallway", True, 1.0),

        # Amenities connections
        ("bank_atm", "student_union", "hallway", True, 1.5),
        ("bank_atm", "central_plaza", "walkway", True, 1.4),
        ("bookstore", "lib_foyer", "hallway", True, 1.2),
        ("bookstore", "lib_group_study", "hallway", True, 1.1),
    ]

    for src, tgt, ptype, acc, crowd in edges_data:
        dist = calc_dist(src, tgt)
        edge = CampusEdge(
            source=src,
            target=tgt,
            distance=dist,
            path_type=ptype,
            accessible=acc,
            crowd_level=crowd,
            is_blocked=False,
            base_speed=1.4
        )
        g.add_edge(edge)

    return g
