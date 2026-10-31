/**
 * Intelligent Campus Navigation Agent - Frontend Application Logic
 * Implements SVG campus rendering, live step-by-step search visualization,
 * open/closed list inspection, dynamic obstacles, and multi-objective routing.
 */
const API_BASE_URL = "https://campus-navigation-agent.onrender.com";
// Application State
const state = {
  graph: { nodes: [], edges: [] },
  startNodeId: "gate_main",
  viaNodeId: null,
  goalNodeId: "cs_lab_ai",
  algorithm: "A*",
  preference: "distance",
  heuristic: "euclidean",
  searchResult: null,
  currentStepIdx: 0,
  isPlaying: false,
  playbackSpeed: 1, // 1x, 2x, 5x
  timerId: null,
  isRushHour: false,
  weather: "fair",
  isWalking: false,
  walkTimerId: null,
  activeTab: "open",
  theme: "dark",
  mapView: "blueprint", // 'blueprint' or 'google-maps'
  googleMapsLoaded: false,
  googleMapsError: null,
  googleMap: null,
  gmapMarkers: {},
  gmapPolylines: [],
  gmapRoutePolyline: null,
  gmapAvatarMarker: null,
  gmapInfoWindow: null,
};

const GOOGLE_MAPS_API_KEY = "AIzaSyDRzIaIEFgXFm-boEOQBtmb9xFBCfResyk";

// Building zones for SVG visualization - DIT University Dehradun
const CAMPUS_BUILDING_ZONES = [
  {
    name: "Chanakya Block (CS & IT)",
    x: 95,
    y: 85,
    width: 210,
    height: 320,
    color: "rgba(56, 189, 248, 0.08)",
    stroke: "rgba(56, 189, 248, 0.25)",
  },
  {
    name: "Vishveshwarya Block (Engg)",
    x: 360,
    y: 45,
    width: 260,
    height: 135,
    color: "rgba(168, 85, 247, 0.08)",
    stroke: "rgba(168, 85, 247, 0.25)",
  },
  {
    name: "Administration & Registry",
    x: 310,
    y: 550,
    width: 140,
    height: 125,
    color: "rgba(245, 158, 11, 0.08)",
    stroke: "rgba(245, 158, 11, 0.25)",
  },
  {
    name: "Vedanta Block (VEDA Library)",
    x: 630,
    y: 210,
    width: 145,
    height: 180,
    color: "rgba(16, 185, 129, 0.08)",
    stroke: "rgba(16, 185, 129, 0.25)",
  },
  {
    name: "Charak & Science Block",
    x: 800,
    y: 200,
    width: 135,
    height: 230,
    color: "rgba(236, 72, 153, 0.08)",
    stroke: "rgba(236, 72, 153, 0.25)",
  },
  {
    name: "Food Court & CCD / SAC",
    x: 650,
    y: 450,
    width: 235,
    height: 160,
    color: "rgba(234, 88, 12, 0.08)",
    stroke: "rgba(234, 88, 12, 0.25)",
  },
  {
    name: "DIT Sports Complex",
    x: 505,
    y: 590,
    width: 210,
    height: 95,
    color: "rgba(14, 165, 233, 0.08)",
    stroke: "rgba(14, 165, 233, 0.25)",
  },
  {
    name: "Amphitheatre Quad",
    x: 450,
    y: 210,
    width: 140,
    height: 180,
    color: "rgba(255, 255, 255, 0.04)",
    stroke: "rgba(255, 255, 255, 0.15)",
  },
  {
    name: "Innovation Hub (TBI)",
    x: 25,
    y: 40,
    width: 95,
    height: 140,
    color: "rgba(245, 158, 11, 0.08)",
    stroke: "rgba(245, 158, 11, 0.25)",
  },
  {
    name: "Sarabhai & Sarojini Hostels",
    x: 25,
    y: 430,
    width: 125,
    height: 155,
    color: "rgba(168, 85, 247, 0.08)",
    stroke: "rgba(168, 85, 247, 0.25)",
  },
  {
    name: "School of Management & Law",
    x: 885,
    y: 380,
    width: 105,
    height: 205,
    color: "rgba(20, 184, 166, 0.08)",
    stroke: "rgba(20, 184, 166, 0.25)",
  },
  {
    name: "Health & Medical Complex",
    x: 775,
    y: 595,
    width: 155,
    height: 75,
    color: "rgba(239, 68, 68, 0.08)",
    stroke: "rgba(239, 68, 68, 0.25)",
  },
];

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  loadCampusGraph().then(() => {
    executeSearch();
  });
  loadEnvironmentData();
});

// --- API DATA FETCHING ---
async function loadCampusGraph() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/graph`);
    state.graph = await res.json();
    populateDropdowns();
    renderCampusSvg();
    if (state.googleMap) {
      renderGoogleMapElements();
      highlightGoogleMapRoute();
    }
  } catch (err) {
    console.error("Failed to load campus graph:", err);
  }
}

async function loadEnvironmentData() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/environment`);
    const data = await res.json();
    renderPeasModal(data.peas, data.classifications);
  } catch (err) {
    console.error("Failed to load environment data:", err);
  }
}

// --- POPULATE DROPDOWNS ---
function populateDropdowns() {
  const startSelect = document.getElementById("select-start-node");
  const goalSelect = document.getElementById("select-goal-node");
  const viaSelect = document.getElementById("select-via-node");

  startSelect.innerHTML = "";
  goalSelect.innerHTML = "";
  if (viaSelect)
    viaSelect.innerHTML = '<option value="">None (Direct Route)</option>';

  // Group by category
  const categories = {};
  state.graph.nodes.forEach((n) => {
    if (!categories[n.category]) categories[n.category] = [];
    categories[n.category].push(n);
  });

  for (const [cat, nodes] of Object.entries(categories)) {
    const groupStart = document.createElement("optgroup");
    groupStart.label = cat;
    const groupGoal = document.createElement("optgroup");
    groupGoal.label = cat;
    const groupVia = document.createElement("optgroup");
    groupVia.label = cat;

    nodes
      .sort((a, b) => a.name.localeCompare(b.name))
      .forEach((n) => {
        const opt1 = new Option(`${n.name} (${n.building})`, n.id);
        const opt2 = new Option(`${n.name} (${n.building})`, n.id);
        const opt3 = new Option(`${n.name} (${n.building})`, n.id);
        groupStart.appendChild(opt1);
        groupGoal.appendChild(opt2);
        groupVia.appendChild(opt3);
      });

    startSelect.appendChild(groupStart);
    goalSelect.appendChild(groupGoal);
    if (viaSelect) viaSelect.appendChild(groupVia);
  }

  startSelect.value = state.startNodeId;
  goalSelect.value = state.goalNodeId;
  if (viaSelect) viaSelect.value = state.viaNodeId || "";
}

// --- SVG CAMPUS MAP RENDERING ---
function renderCampusSvg() {
  const zonesLayer = document.getElementById("svg-zones-layer");
  const edgesLayer = document.getElementById("svg-edges-layer");
  const nodesLayer = document.getElementById("svg-nodes-layer");
  const routeLayer = document.getElementById("svg-route-layer");

  zonesLayer.innerHTML = "";
  edgesLayer.innerHTML = "";
  nodesLayer.innerHTML = "";
  routeLayer.innerHTML = "";

  // 1. Draw Building Zones
  CAMPUS_BUILDING_ZONES.forEach((z) => {
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", z.x);
    rect.setAttribute("y", z.y);
    rect.setAttribute("width", z.width);
    rect.setAttribute("height", z.height);
    rect.setAttribute("rx", 12);
    rect.setAttribute("fill", z.color);
    rect.setAttribute("stroke", z.stroke);
    rect.setAttribute("stroke-width", "1.5");
    zonesLayer.appendChild(rect);

    const txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
    txt.setAttribute("x", z.x + 12);
    txt.setAttribute("y", z.y + 20);
    txt.setAttribute("fill", "rgba(255, 255, 255, 0.45)");
    txt.setAttribute("font-size", "10px");
    txt.setAttribute("font-weight", "700");
    txt.setAttribute("letter-spacing", "0.04em");
    txt.textContent = z.name.toUpperCase();
    zonesLayer.appendChild(txt);
  });

  // 2. Draw Edges
  state.graph.edges.forEach((e) => {
    const n1 = state.graph.nodes.find((n) => n.id === e.source);
    const n2 = state.graph.nodes.find((n) => n.id === e.target);
    if (!n1 || !n2) return;

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", n1.x);
    line.setAttribute("y1", n1.y);
    line.setAttribute("x2", n2.x);
    line.setAttribute("y2", n2.y);
    line.setAttribute("id", `edge-${e.source}-${e.target}`);

    let cls = "svg-edge";
    if (e.is_blocked) cls += " blocked";
    else if (!e.accessible) cls += " stairs";
    else if (e.path_type === "elevator") cls += " elevator";
    line.setAttribute("class", cls);

    // Click to toggle edge block
    line.addEventListener("click", (ev) => {
      ev.stopPropagation();
      toggleBlock("edge", e.source, e.target, !e.is_blocked);
    });

    // Tooltip
    const title = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "title",
    );
    title.textContent = `${n1.name} ⟷ ${n2.name}\nType: ${e.path_type}\nDistance: ${e.distance}m\nCrowd: ${e.crowd_level}x\nAccessible: ${e.accessible ? "Yes" : "No"}${e.is_blocked ? "\n[BLOCKED: " + e.block_reason + "]" : ""}\n(Click to toggle obstacle)`;
    line.appendChild(title);

    edgesLayer.appendChild(line);
  });

  // 3. Draw Nodes
  state.graph.nodes.forEach((n) => {
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("class", "svg-node-group");
    g.setAttribute("id", `node-group-${n.id}`);
    g.setAttribute("transform", `translate(${n.x}, ${n.y})`);

    // Outer glow / circle
    const circle = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "circle",
    );
    circle.setAttribute("r", "11");
    circle.setAttribute("class", getNodeClass(n));
    circle.setAttribute("id", `node-circle-${n.id}`);

    // Category Icon
    const icon = document.createElementNS("http://www.w3.org/2000/svg", "text");
    icon.setAttribute("y", "3.5");
    icon.setAttribute("text-anchor", "middle");
    icon.setAttribute("font-size", "9px");
    icon.setAttribute("fill", "#ffffff");
    icon.setAttribute("pointer-events", "none");
    icon.textContent = getNodeCategoryIcon(n.category);

    // Label
    const label = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "text",
    );
    label.setAttribute("class", "svg-node-label");
    label.setAttribute("y", "22");
    label.textContent =
      n.name.length > 18 ? n.name.substring(0, 16) + "…" : n.name;

    // Node Tooltip
    const title = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "title",
    );
    title.textContent = `${n.name} (${n.building}, F${n.floor})\nCategory: ${n.category}${n.is_blocked ? "\n[BLOCKED: " + n.block_reason + "]" : ""}\nLeft-click: Set Start/Goal | Right-click: Block`;
    g.appendChild(title);

    g.appendChild(circle);
    g.appendChild(icon);
    g.appendChild(label);

    // Node interactions
    g.addEventListener("click", (ev) => {
      ev.stopPropagation();
      handleNodeLeftClick(n.id);
    });

    g.addEventListener("contextmenu", (ev) => {
      ev.preventDefault();
      toggleBlock("node", n.id, null, !n.is_blocked);
    });

    nodesLayer.appendChild(g);
  });

  highlightFinalRoute();
}

function getNodeClass(n) {
  if (n.is_blocked) return "svg-node-circle is-blocked";
  if (n.id === state.startNodeId) return "svg-node-circle start-node";
  if (n.id === state.goalNodeId) return "svg-node-circle goal-node";
  return "svg-node-circle";
}

function getNodeCategoryIcon(cat) {
  switch (cat) {
    case "Classroom":
      return "🏫";
    case "Laboratory":
      return "🔬";
    case "Office":
      return "💼";
    case "Department":
      return "🏛️";
    case "Entrance":
      return "🚪";
    default:
      return "📍";
  }
}

function handleNodeLeftClick(nodeId) {
  if (!state.startNodeId || (state.startNodeId && state.goalNodeId)) {
    state.startNodeId = nodeId;
    state.goalNodeId = null;
  } else if (state.startNodeId && !state.goalNodeId) {
    if (state.startNodeId === nodeId) return;
    state.goalNodeId = nodeId;
    executeSearch();
  }

  document.getElementById("select-start-node").value = state.startNodeId || "";
  document.getElementById("select-goal-node").value = state.goalNodeId || "";
  updateNodeVisualStates();
}

// --- SEARCH EXECUTION ---
async function executeSearch() {
  if (!state.startNodeId || !state.goalNodeId) return;

  const algo = state.algorithm === "A*_Time" ? "A*" : state.algorithm;
  const heur =
    state.algorithm === "A*_Time" || state.preference === "time"
      ? "time"
      : "euclidean";
  const isMultiStop = Boolean(
    state.viaNodeId &&
    state.viaNodeId !== state.startNodeId &&
    state.viaNodeId !== state.goalNodeId,
  );

  const endpoint = isMultiStop ? "/api/multi-stop" : "/api/search";
  const reqBody = isMultiStop
    ? {
        start: state.startNodeId,
        via: state.viaNodeId,
        goal: state.goalNodeId,
        algorithm: algo,
        preference: state.preference,
      }
    : {
        start: state.startNodeId,
        goal: state.goalNodeId,
        algorithm: algo,
        preference: state.preference,
        heuristic: heur,
      };

  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(reqBody),
    });

    const data = await res.json();
    if (data.status === "success" && data.result.success) {
      state.searchResult = data.result;
      state.currentStepIdx =
        data.result.steps.length > 0 ? data.result.steps.length - 1 : 0;
      updateMetricsDisplay(data.result);
      setupStepper(data.result.steps.length);
      renderStep(state.currentStepIdx);
      renderTurnByTurnLegs(data.result.path_segments);
      highlightFinalRoute();
    } else {
      state.searchResult = data.result || null;
      handleSearchFailure(
        (data.result && data.result.error_message) ||
          data.message ||
          "Route not found",
      );
      if (data.result && data.result.steps && data.result.steps.length > 0) {
        setupStepper(data.result.steps.length);
        state.currentStepIdx = data.result.steps.length - 1;
        renderStep(state.currentStepIdx);
      }
    }
  } catch (err) {
    console.error("Search error:", err);
  }
}

async function findNearest(facilityType) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/nearest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        start: state.startNodeId,
        type: facilityType,
        preference: state.preference,
      }),
    });
    const data = await res.json();
    if (data.status === "success") {
      state.viaNodeId = null;
      const viaSel = document.getElementById("select-via-node");
      if (viaSel) viaSel.value = "";

      state.goalNodeId = data.target;
      document.getElementById("select-goal-node").value = state.goalNodeId;
      state.searchResult = data.result;
      state.currentStepIdx =
        data.result.steps.length > 0 ? data.result.steps.length - 1 : 0;
      updateMetricsDisplay(data.result);
      setupStepper(data.result.steps.length);
      renderStep(state.currentStepIdx);
      renderTurnByTurnLegs(data.result.path_segments);
      highlightFinalRoute();
      updateNodeVisualStates();
      const targetNode = state.graph.nodes.find((n) => n.id === data.target);
      document.getElementById("current-action-display").textContent =
        `🎯 Located nearest ${facilityType}: ${targetNode ? targetNode.name : data.target}`;
    } else {
      alert(data.message || `No accessible ${facilityType} found.`);
    }
  } catch (err) {
    console.error("Failed to find nearest:", err);
  }
}

function updateMetricsDisplay(result) {
  document.getElementById("metric-dist").textContent =
    `${result.total_distance.toFixed(1)} m`;
  document.getElementById("metric-time").textContent =
    `${result.total_time.toFixed(1)} s`;
  document.getElementById("metric-expanded").textContent =
    result.nodes_expanded;
  document.getElementById("metric-exec").textContent =
    `${result.execution_time_ms.toFixed(2)} ms`;

  const stepsVal =
    result.steps_count !== undefined
      ? result.steps_count
      : Math.round(result.total_distance / 0.75);
  const calVal =
    result.calories_burned !== undefined
      ? result.calories_burned
      : result.total_distance * 0.045;
  const stepsElem = document.getElementById("metric-steps");
  if (stepsElem) stepsElem.textContent = `${stepsVal} steps`;
  const calElem = document.getElementById("metric-calories");
  if (calElem) calElem.textContent = `${calVal.toFixed(1)} kcal`;

  // Accessibility Badge
  const accBadge = document.getElementById("badge-accessibility");
  if (result.all_accessible) {
    accBadge.className = "status-badge success";
    accBadge.textContent = "♿ 100% Wheelchair Accessible";
  } else {
    accBadge.className = "status-badge fail";
    accBadge.textContent = "⚠️ Includes Stairs (Non-accessible)";
  }

  // Crowd Badge
  const crowdBadge = document.getElementById("badge-crowd");
  crowdBadge.textContent = `👥 Peak Crowd: ${result.max_crowd_level.toFixed(1)}x`;
  if (result.max_crowd_level > 2.0) {
    crowdBadge.style.background = "rgba(244, 63, 94, 0.15)";
    crowdBadge.style.color = "var(--accent-rose)";
  } else {
    crowdBadge.style.background = "rgba(56, 189, 248, 0.15)";
    crowdBadge.style.color = "var(--accent-cyan)";
  }

  document.getElementById("current-action-display").textContent = result.success
    ? `✔ Found route in ${result.nodes_expanded} expansions (${result.execution_time_ms.toFixed(2)}ms)`
    : "❌ No accessible route exists";
}

function handleSearchFailure(msg) {
  document.getElementById("metric-dist").textContent = "N/A";
  document.getElementById("metric-time").textContent = "N/A";
  document.getElementById("metric-expanded").textContent = "0";
  document.getElementById("metric-exec").textContent = "0.0 ms";
  const stepsElem = document.getElementById("metric-steps");
  if (stepsElem) stepsElem.textContent = "0 steps";
  const calElem = document.getElementById("metric-calories");
  if (calElem) calElem.textContent = "0.0 kcal";
  document.getElementById("current-action-display").textContent = `❌ ${msg}`;
  document.getElementById("route-legs-container").innerHTML =
    `<div style="color: var(--accent-rose); padding: 12px; font-size: 0.8rem; text-align: center;">${msg}</div>`;

  const routeLayer = document.getElementById("svg-route-layer");
  if (routeLayer) routeLayer.innerHTML = "";
}

// --- STEP-BY-STEP INSPECTOR & ANIMATION ---
function setupStepper(totalSteps) {
  const scrubber = document.getElementById("step-scrubber");
  scrubber.min = 0;
  scrubber.max = Math.max(0, totalSteps - 1);
  scrubber.value = state.currentStepIdx;
  updateCounterText();
}

function updateCounterText() {
  const total = state.searchResult ? state.searchResult.steps.length : 0;
  const current = total === 0 ? 0 : state.currentStepIdx + 1;
  document.getElementById("step-counter-text").textContent =
    `Step ${current} / ${total}`;
}

function renderStep(idx) {
  if (
    !state.searchResult ||
    !state.searchResult.steps ||
    state.searchResult.steps.length === 0
  )
    return;

  const step = state.searchResult.steps[idx];
  if (!step) return;

  updateCounterText();
  document.getElementById("step-scrubber").value = idx;

  // 1. Highlight Nodes on SVG map
  const openSet = new Set(step.open_list.map((o) => o.id));
  const closedSet = new Set(step.closed_list);

  state.graph.nodes.forEach((n) => {
    const circle = document.getElementById(`node-circle-${n.id}`);
    if (!circle) return;

    if (n.is_blocked) {
      circle.setAttribute("class", "svg-node-circle is-blocked");
    } else if (n.id === state.startNodeId) {
      circle.setAttribute("class", "svg-node-circle start-node");
    } else if (n.id === state.goalNodeId) {
      circle.setAttribute("class", "svg-node-circle goal-node");
    } else if (n.id === step.current_node) {
      circle.setAttribute("class", "svg-node-circle current-expand");
    } else if (openSet.has(n.id)) {
      circle.setAttribute("class", "svg-node-circle in-open");
    } else if (closedSet.has(n.id)) {
      circle.setAttribute("class", "svg-node-circle in-closed");
    } else {
      circle.setAttribute("class", "svg-node-circle");
    }
  });

  // 2. Populate Open List Table
  const tbody = document.getElementById("open-list-tbody");
  tbody.innerHTML = "";
  if (step.open_list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="color: var(--text-dim); text-align: center;">Frontier is empty</td></tr>`;
  } else {
    step.open_list.forEach((item) => {
      const tr = document.createElement("tr");
      const fVal = item.f !== undefined ? item.f : "-";
      const gVal = item.g !== undefined ? item.g : "-";
      const hVal = item.h !== undefined ? item.h : "-";
      tr.innerHTML = `
        <td style="color: var(--text-main); font-weight:600;">${item.name || item.id}</td>
        <td style="color: var(--accent-cyan); font-weight:700;">${fVal}</td>
        <td style="color: var(--text-muted);">${gVal}</td>
        <td style="color: var(--text-muted);">${hVal}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  // 3. Populate Closed List
  const closedContainer = document.getElementById("closed-list-tags");
  closedContainer.innerHTML = "";
  if (step.closed_list.length === 0) {
    closedContainer.innerHTML = `<span style="color: var(--text-dim); font-size: 0.75rem;">None</span>`;
  } else {
    step.closed_list.forEach((id) => {
      const nodeObj = state.graph.nodes.find((n) => n.id === id);
      const span = document.createElement("span");
      span.className = "status-badge";
      span.style.background = "rgba(139, 92, 246, 0.2)";
      span.style.color = "#c084fc";
      span.textContent = nodeObj ? nodeObj.name : id;
      closedContainer.appendChild(span);
    });
  }

  document.getElementById("current-action-display").textContent =
    `Step ${idx + 1}: ${step.action_taken || "Processing"} (f=${step.f_val.toFixed(1)}, g=${step.g_val.toFixed(1)})`;

  if (state.googleMap && state.mapView === "google-maps") {
    updateGoogleMapStep(step.current_node);
  }
}

// --- HIGHLIGHT FINAL ROUTE ---
function highlightFinalRoute() {
  const routeLayer = document.getElementById("svg-route-layer");
  if (routeLayer) routeLayer.innerHTML = "";

  if (
    !state.searchResult ||
    !state.searchResult.success ||
    !state.searchResult.path_segments
  ) {
    if (state.gmapRoutePolyline) {
      state.gmapRoutePolyline.setMap(null);
      state.gmapRoutePolyline = null;
    }
    return;
  }

  state.searchResult.path_segments.forEach((seg) => {
    const n1 = state.graph.nodes.find((n) => n.id === seg.from_id);
    const n2 = state.graph.nodes.find((n) => n.id === seg.to_id);
    if (!n1 || !n2) return;

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", n1.x);
    line.setAttribute("y1", n1.y);
    line.setAttribute("x2", n2.x);
    line.setAttribute("y2", n2.y);
    line.setAttribute("class", "svg-edge route-path");
    routeLayer.appendChild(line);
  });

  highlightGoogleMapRoute();
}

// --- RENDER TURN-BY-TURN BREAKDOWN ---
function renderTurnByTurnLegs(segments) {
  const container = document.getElementById("route-legs-container");
  container.innerHTML = "";

  if (!segments || segments.length === 0) {
    container.innerHTML = `<div style="color: var(--text-dim); font-size: 0.78rem; text-align: center; padding: 14px;">No active route.</div>`;
    return;
  }

  segments.forEach((seg, i) => {
    const item = document.createElement("div");
    item.className = "route-leg-item";
    const accIcon = seg.accessible ? "♿" : "⚠️";
    item.innerHTML = `
      <div>
        <div style="font-weight: 700; color: var(--text-main);">${i + 1}. ${seg.from_name} ➔ ${seg.to_name}</div>
        <div style="color: var(--text-dim); font-size: 0.7rem; margin-top: 2px;">Via ${seg.path_type} • ${accIcon} ${seg.accessible ? "Accessible" : "Stairs"}</div>
      </div>
      <div style="text-align: right; font-family: var(--font-mono);">
        <div style="color: var(--accent-cyan); font-weight: 600;">${seg.distance.toFixed(0)}m</div>
        <div style="color: var(--text-muted); font-size: 0.7rem;">${seg.travel_time.toFixed(0)}s</div>
      </div>
    `;
    container.appendChild(item);
  });
}

// --- ANIMATION CONTROLLER ---
function togglePlayPause() {
  if (state.isPlaying) {
    pauseAnimation();
  } else {
    playAnimation();
  }
}

function playAnimation() {
  if (!state.searchResult || !state.searchResult.steps) return;
  state.isPlaying = true;
  document.getElementById("btn-play-pause").textContent = "⏸";

  if (state.currentStepIdx >= state.searchResult.steps.length - 1) {
    state.currentStepIdx = 0;
  }

  const intervalMs = Math.max(50, 400 / state.playbackSpeed);
  state.timerId = setInterval(() => {
    if (state.currentStepIdx < state.searchResult.steps.length - 1) {
      state.currentStepIdx++;
      renderStep(state.currentStepIdx);
    } else {
      pauseAnimation();
      highlightFinalRoute();
    }
  }, intervalMs);
}

function pauseAnimation() {
  state.isPlaying = false;
  document.getElementById("btn-play-pause").textContent = "▶";
  if (state.timerId) {
    clearInterval(state.timerId);
    state.timerId = null;
  }
}

// --- OBSTACLE & DYNAMIC CONTROLS ---
async function toggleBlock(type, u, v, blocked) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/toggle-block`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: type,
        id: u,
        source: u,
        target: v,
        blocked: blocked,
        reason: "Maintenance & Obstruction",
      }),
    });
    const data = await res.json();
    if (data.status === "success") {
      state.graph = data.graph;
      renderCampusSvg();
      executeSearch();
    }
  } catch (err) {
    console.error("Failed to toggle block:", err);
  }
}

async function addRandomObstacle() {
  // Pick an unblocked edge
  const unblockedEdges = state.graph.edges.filter((e) => !e.is_blocked);
  if (unblockedEdges.length === 0) return;
  const picked =
    unblockedEdges[Math.floor(Math.random() * unblockedEdges.length)];
  await toggleBlock("edge", picked.source, picked.target, true);
}

async function resetAllObstacles() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/reset-blocks`, {
      method: "POST",
    });
    const data = await res.json();
    if (data.status === "success") {
      state.graph = data.graph;
      renderCampusSvg();
      executeSearch();
    }
  } catch (err) {
    console.error("Failed to reset obstacles:", err);
  }
}

async function toggleRushHour() {
  state.isRushHour = !state.isRushHour;
  document.getElementById("rush-status-text").textContent = state.isRushHour
    ? "ON"
    : "OFF";
  document
    .getElementById("btn-toggle-rush")
    .classList.toggle("active", state.isRushHour);

  try {
    const res = await fetch(`${API_BASE_URL}/api/simulate-rush-hour`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ active: state.isRushHour }),
    });
    const data = await res.json();
    if (data.status === "success") {
      state.graph = data.graph;
      renderCampusSvg();
      executeSearch();
    }
  } catch (err) {
    console.error("Failed to toggle rush hour:", err);
  }
}

// --- WEATHER SIMULATION ---
function toggleWeather() {
  state.weather = state.weather === "fair" ? "rain" : "fair";
  const isRain = state.weather === "rain";
  const statusElem = document.getElementById("weather-status-text");
  if (statusElem) statusElem.textContent = isRain ? "Rain (Sheltered)" : "Fair";
  const iconElem = document.getElementById("weather-icon");
  if (iconElem) iconElem.textContent = isRain ? "🌧️" : "☀️";
  const btn = document.getElementById("btn-toggle-weather");
  if (btn) btn.classList.toggle("active", isRain);

  // If rain mode, automatically switch preference to sheltered
  const prefGroup = document.getElementById("pref-grid");
  if (prefGroup) {
    if (isRain) {
      state.preference = "shelter";
      prefGroup.querySelectorAll(".pref-card").forEach((c) => {
        c.classList.toggle("active", c.dataset.pref === "shelter");
      });
    } else {
      state.preference = "distance";
      prefGroup.querySelectorAll(".pref-card").forEach((c) => {
        c.classList.toggle("active", c.dataset.pref === "distance");
      });
    }
  }
  executeSearch();
}

// --- LIVE PEDESTRIAN WALKING SIMULATION ---
function simulateWalk() {
  if (
    !state.searchResult ||
    !state.searchResult.success ||
    !state.searchResult.path_nodes ||
    state.searchResult.path_nodes.length === 0
  ) {
    alert(
      "Please calculate a valid route before simulating pedestrian walking.",
    );
    return;
  }

  if (state.isWalking) {
    stopWalkingSimulation();
    return;
  }

  state.isWalking = true;
  const btn = document.getElementById("btn-simulate-walk");
  if (btn) {
    btn.style.background = "#d97706";
    btn.innerHTML = "<span>⏹ Stop Walk</span>";
  }

  const pathNodes = state.searchResult.path_nodes;
  let currentIdx = 0;
  const agentLayer = document.getElementById("svg-agent-layer");

  function moveAvatar() {
    if (!state.isWalking || currentIdx >= pathNodes.length) {
      stopWalkingSimulation();
      return;
    }

    const nodeId = pathNodes[currentIdx];
    const nodeObj = state.graph.nodes.find((n) => n.id === nodeId);
    if (!nodeObj) return;

    if (agentLayer) {
      agentLayer.innerHTML = `
        <circle cx="${nodeObj.x}" cy="${nodeObj.y}" r="20" fill="rgba(56, 189, 248, 0.25)" stroke="#38bdf8" stroke-width="2">
          <animate attributeName="r" values="14;24;14" dur="1.2s" repeatCount="indefinite" />
        </circle>
        <circle cx="${nodeObj.x}" cy="${nodeObj.y}" r="8" fill="#38bdf8" />
        <text x="${nodeObj.x}" y="${nodeObj.y - 14}" text-anchor="middle" font-size="14px">🚶</text>
      `;
    }

    document.getElementById("current-action-display").textContent =
      `🚶 Walking at waypoint ${currentIdx + 1}/${pathNodes.length}: ${nodeObj.name} (${nodeObj.building})`;

    if (state.googleMap && state.mapView === "google-maps") {
      updateGoogleMapAvatar(nodeObj);
    }

    currentIdx++;
    state.walkTimerId = setTimeout(moveAvatar, 1400 / state.playbackSpeed);
  }

  moveAvatar();
}

function stopWalkingSimulation() {
  state.isWalking = false;
  if (state.walkTimerId) {
    clearTimeout(state.walkTimerId);
    state.walkTimerId = null;
  }
  if (state.gmapAvatarMarker) {
    state.gmapAvatarMarker.setMap(null);
    state.gmapAvatarMarker = null;
  }
  const btn = document.getElementById("btn-simulate-walk");
  if (btn) {
    btn.style.background = "#059669";
    btn.innerHTML = "<span>🚶 Walk Route</span>";
  }
  const agentLayer = document.getElementById("svg-agent-layer");
  if (agentLayer) agentLayer.innerHTML = "";
}

// --- FILTER CAMPUS NODES ---
function filterCampusNodes(filterText) {
  const query = filterText.toLowerCase().trim();
  const startSelect = document.getElementById("select-start-node");
  const goalSelect = document.getElementById("select-goal-node");
  const viaSelect = document.getElementById("select-via-node");

  [startSelect, goalSelect, viaSelect].forEach((select) => {
    if (!select) return;
    Array.from(select.options).forEach((opt) => {
      if (!opt.value) return;
      const match = opt.text.toLowerCase().includes(query);
      opt.style.display = match ? "" : "none";
    });
  });
}

// --- EXPORT DIRECTIONS PASS ---
function openExportModal() {
  if (!state.searchResult || !state.searchResult.success) {
    alert("Please compute an active route first before exporting.");
    return;
  }

  const modal = document.getElementById("modal-export");
  modal.classList.add("open");

  const r = state.searchResult;
  const startNode = state.graph.nodes.find((n) => n.id === state.startNodeId);
  const goalNode = state.graph.nodes.find((n) => n.id === state.goalNodeId);
  const viaNode = state.viaNodeId
    ? state.graph.nodes.find((n) => n.id === state.viaNodeId)
    : null;

  let content = `==========================================================\n`;
  content += `🧭 DIT UNIVERSITY DEHRADUN - CAMPUS NAVIGATION PASS\n`;
  content += `==========================================================\n`;
  content += `Date & Time:    ${new Date().toLocaleString()}\n`;
  content += `Campus:         DIT University, Mussoorie Diversion Road, Dehradun\n`;
  content += `Departure:      ${startNode ? startNode.name : state.startNodeId} (${startNode ? startNode.building : ""})\n`;
  if (viaNode) {
    content += `Stopover (Via): ${viaNode.name} (${viaNode.building})\n`;
  }
  content += `Destination:    ${goalNode ? goalNode.name : state.goalNodeId} (${goalNode ? goalNode.building : ""})\n`;
  content += `Routing Method: ${r.algorithm} | Criteria: ${state.preference.toUpperCase()}\n`;
  content += `----------------------------------------------------------\n`;
  content += `Total Distance: ${r.total_distance.toFixed(1)} meters (~${r.steps_count || Math.round(r.total_distance / 0.75)} steps)\n`;
  content += `Travel Time:    ${r.total_time.toFixed(1)} seconds (~${(r.total_time / 60).toFixed(1)} minutes)\n`;
  content += `Calorie Burn:   ${(r.calories_burned || r.total_distance * 0.045).toFixed(1)} kcal\n`;
  content += `Accessibility:  ${r.all_accessible ? "100% Wheelchair Accessible (Zero stairs)" : "Non-accessible (Includes staircases)"}\n`;
  content += `Peak Crowding:  ${r.max_crowd_level.toFixed(1)}x\n`;
  content += `----------------------------------------------------------\n`;
  content += `TURN-BY-TURN WAYPOINT INSTRUCTIONS:\n`;

  r.path_segments.forEach((seg, idx) => {
    const accTag = seg.accessible ? "[Accessible]" : "[Stairs Warning]";
    content += `${idx + 1}. ${seg.from_name} ➔ ${seg.to_name}\n`;
    content += `   Via: ${seg.path_type} | Dist: ${seg.distance.toFixed(0)}m | Time: ${seg.travel_time.toFixed(0)}s | ${accTag}\n`;
  });

  content += `==========================================================\n`;
  content += `Campus Security & Proctor: +91 135 714 4000 | Emergency: 1800-120-1010\n`;
  content += `Have a safe and pleasant journey across DIT University campus!\n`;

  document.getElementById("export-pass-content").textContent = content;
}

function copyDirections() {
  const text = document.getElementById("export-pass-content").textContent;
  navigator.clipboard
    .writeText(text)
    .then(() => {
      alert("Directions pass copied to clipboard!");
    })
    .catch(() => {
      alert("Failed to copy. Please select and copy manually.");
    });
}

function printDirections() {
  const content = document.getElementById("export-pass-content").textContent;
  const printWindow = window.open("", "_blank");
  printWindow.document.write(
    `<pre style="font-family: monospace; font-size: 13px; line-height: 1.5; padding: 20px;">${content}</pre>`,
  );
  printWindow.document.close();
  printWindow.print();
}

// --- BENCHMARK MODAL ---
async function openBenchmarkModal() {
  const modal = document.getElementById("modal-benchmark");
  modal.classList.add("open");

  const tbody = document.getElementById("benchmark-tbody");
  tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--accent-cyan); padding: 18px;">Running benchmark simulation across all algorithms...</td></tr>`;

  try {
    const res = await fetch(`${API_BASE_URL}/api/compare-all`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        start: state.startNodeId,
        goal: state.goalNodeId,
        preference: state.preference,
      }),
    });
    const data = await res.json();
    tbody.innerHTML = "";

    for (const [algo, r] of Object.entries(data.results)) {
      const tr = document.createElement("tr");
      let statusCls = "status-badge fail";
      let statusTxt = "Failed";
      if (r.success) {
        if (algo.startsWith("A*") || algo.startsWith("Dijkstra")) {
          statusCls = "status-badge success";
          statusTxt = "Optimal";
        } else if (algo.startsWith("BFS")) {
          statusCls = "status-badge";
          statusTxt = "Fewest Hops";
        } else {
          statusCls = "status-badge";
          statusTxt = "Suboptimal";
        }
      }
      const dist = r.success ? `${r.total_distance.toFixed(1)}m` : "N/A";
      const time = r.success ? `${r.total_time.toFixed(1)}s` : "N/A";
      const expanded = r.success ? r.nodes_expanded : "-";
      const maxOpen = r.success ? r.max_frontier_size : "-";
      const exec = r.success ? `${r.execution_time_ms.toFixed(3)}ms` : "-";

      tr.innerHTML = `
        <td style="font-weight: 700; color: var(--text-main);">${algo}</td>
        <td><span class="${statusCls}">${statusTxt}</span></td>
        <td style="font-family: var(--font-mono);">${dist}</td>
        <td style="font-family: var(--font-mono);">${time}</td>
        <td style="font-family: var(--font-mono); color: var(--accent-amber); font-weight: 700;">${expanded}</td>
        <td style="font-family: var(--font-mono);">${maxOpen}</td>
        <td style="font-family: var(--font-mono); color: var(--accent-cyan);">${exec}</td>
      `;
      tbody.appendChild(tr);
    }
  } catch (err) {
    console.error("Benchmark error:", err);
  }
}

// --- PEAS & ENVIRONMENT MODAL ---
function renderPeasModal(peas, envClassifications) {
  const peasBox = document.getElementById("peas-container");
  peasBox.innerHTML = "";

  for (const [key, items] of Object.entries(peas)) {
    const card = document.createElement("div");
    card.style.background = "var(--bg-primary)";
    card.style.padding = "12px";
    card.style.borderRadius = "10px";
    card.style.border = "1px solid var(--border-subtle)";

    const h = document.createElement("div");
    h.style.fontWeight = "700";
    h.style.fontSize = "0.85rem";
    h.style.color = "var(--accent-cyan)";
    h.style.marginBottom = "6px";
    h.textContent = key.replace("_", " ");

    const ul = document.createElement("ul");
    ul.style.fontSize = "0.75rem";
    ul.style.color = "var(--text-muted)";
    ul.style.paddingLeft = "16px";
    ul.style.lineHeight = "1.4";

    items.forEach((it) => {
      const li = document.createElement("li");
      li.textContent = it;
      ul.appendChild(li);
    });

    card.appendChild(h);
    card.appendChild(ul);
    peasBox.appendChild(card);
  }

  const envBox = document.getElementById("env-classification-container");
  envBox.innerHTML = "";

  envClassifications.forEach((item) => {
    const row = document.createElement("div");
    row.style.background = "var(--bg-primary)";
    row.style.padding = "12px 14px";
    row.style.borderRadius = "10px";
    row.style.border = "1px solid var(--border-subtle)";

    row.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
        <span style="font-weight: 700; color: var(--text-main); font-size: 0.85rem;">${item.dimension}</span>
        <span class="status-badge" style="background: rgba(16, 185, 129, 0.15); color: var(--accent-emerald);">${item.type}</span>
      </div>
      <div style="font-size: 0.78rem; color: var(--text-dim); line-height: 1.4;">${item.details}</div>
    `;
    envBox.appendChild(row);
  });
}

async function runPartialObservabilitySim() {
  const out = document.getElementById("partial-sim-output");
  out.textContent = "Simulating agent movement with local sensor horizon...";

  try {
    const res = await fetch(`${API_BASE_URL}/api/simulate-partial`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        start: "cs_entrance",
        goal: "lib_group_study",
        hidden_blocks: [["central_plaza", "lib_foyer"]],
      }),
    });
    const data = await res.json();
    if (data.status === "success") {
      const sim = data.simulation;
      let text = `✔ Simulation Completed!\nTraversed Path: ${sim.final_traversed_path.join(" ➔ ")}\nTotal Distance: ${sim.total_distance}m | Total Time: ${sim.total_time}s\n\nReplanning Events:\n`;
      sim.replan_events.forEach((ev) => {
        text += `• ${ev.event}: ${ev.description || "Detour: " + ev.new_path.join(" ➔ ")}\n`;
      });
      out.textContent = text;
      // Refresh map
      loadCampusGraph();
    }
  } catch (err) {
    out.textContent = "Simulation error: " + err.message;
  }
}

// --- EVENT LISTENERS ---
function initEventListeners() {
  // Endpoint Selectors
  document
    .getElementById("select-start-node")
    .addEventListener("change", (e) => {
      state.startNodeId = e.target.value;
      updateNodeVisualStates();
      executeSearch();
    });

  document
    .getElementById("select-goal-node")
    .addEventListener("change", (e) => {
      state.goalNodeId = e.target.value;
      updateNodeVisualStates();
      executeSearch();
    });

  const viaSelect = document.getElementById("select-via-node");
  if (viaSelect) {
    viaSelect.addEventListener("change", (e) => {
      state.viaNodeId = e.target.value || null;
      executeSearch();
    });
  }

  // Quick Nearest Facility Finder Buttons
  document.querySelectorAll(".btn-quick-find").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const facility = e.currentTarget.dataset.facility;
      if (facility) findNearest(facility);
    });
  });

  // Algorithm Chips
  const algoGroup = document.getElementById("algo-chip-group");
  algoGroup.addEventListener("click", (e) => {
    const btn = e.target.closest(".chip-btn");
    if (!btn) return;
    algoGroup
      .querySelectorAll(".chip-btn")
      .forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    state.algorithm = btn.dataset.algo;
    executeSearch();
  });

  // Preference Cards
  const prefGroup = document.getElementById("pref-grid");
  prefGroup.addEventListener("click", (e) => {
    const card = e.target.closest(".pref-card");
    if (!card) return;
    prefGroup
      .querySelectorAll(".pref-card")
      .forEach((c) => c.classList.remove("active"));
    card.classList.add("active");
    state.preference = card.dataset.pref;
    executeSearch();
  });

  // Action Buttons
  document
    .getElementById("btn-run-search")
    .addEventListener("click", executeSearch);
  document
    .getElementById("btn-play-pause")
    .addEventListener("click", togglePlayPause);

  document.getElementById("btn-step-next").addEventListener("click", () => {
    pauseAnimation();
    if (
      state.searchResult &&
      state.currentStepIdx < state.searchResult.steps.length - 1
    ) {
      state.currentStepIdx++;
      renderStep(state.currentStepIdx);
    }
  });

  document.getElementById("btn-step-prev").addEventListener("click", () => {
    pauseAnimation();
    if (state.searchResult && state.currentStepIdx > 0) {
      state.currentStepIdx--;
      renderStep(state.currentStepIdx);
    }
  });

  document.getElementById("btn-step-reset").addEventListener("click", () => {
    pauseAnimation();
    state.currentStepIdx = 0;
    renderStep(0);
  });

  document.getElementById("step-scrubber").addEventListener("input", (e) => {
    pauseAnimation();
    state.currentStepIdx = parseInt(e.target.value, 10);
    renderStep(state.currentStepIdx);
  });

  document.getElementById("btn-speed-toggle").addEventListener("click", (e) => {
    if (state.playbackSpeed === 1) state.playbackSpeed = 2;
    else if (state.playbackSpeed === 2) state.playbackSpeed = 5;
    else state.playbackSpeed = 1;
    e.target.textContent = `${state.playbackSpeed}x`;
    if (state.isPlaying) {
      pauseAnimation();
      playAnimation();
    }
  });

  // Inspector Tabs
  document.getElementById("tab-open-list").addEventListener("click", () => {
    document.getElementById("tab-open-list").classList.add("active");
    document.getElementById("tab-closed-list").classList.remove("active");
    document.getElementById("open-list-view").style.display = "block";
    document.getElementById("closed-list-view").style.display = "none";
  });

  document.getElementById("tab-closed-list").addEventListener("click", () => {
    document.getElementById("tab-closed-list").classList.add("active");
    document.getElementById("tab-open-list").classList.remove("active");
    document.getElementById("closed-list-view").style.display = "block";
    document.getElementById("open-list-view").style.display = "none";
  });

  // Header quick actions
  document
    .getElementById("btn-toggle-rush")
    .addEventListener("click", toggleRushHour);
  const weatherBtn = document.getElementById("btn-toggle-weather");
  if (weatherBtn) weatherBtn.addEventListener("click", toggleWeather);
  document
    .getElementById("btn-random-obstacle")
    .addEventListener("click", addRandomObstacle);
  document
    .getElementById("btn-reset-map")
    .addEventListener("click", resetAllObstacles);

  // Walk Simulation
  const walkBtn = document.getElementById("btn-simulate-walk");
  if (walkBtn) walkBtn.addEventListener("click", simulateWalk);

  // Quick Location Search Filter
  const filterInput = document.getElementById("input-filter-nodes");
  if (filterInput) {
    filterInput.addEventListener("input", (e) =>
      filterCampusNodes(e.target.value),
    );
  }

  // Modals
  document
    .getElementById("btn-open-benchmark")
    .addEventListener("click", openBenchmarkModal);
  const exportBtn = document.getElementById("btn-open-export");
  if (exportBtn) exportBtn.addEventListener("click", openExportModal);
  const copyBtn = document.getElementById("btn-copy-directions");
  if (copyBtn) copyBtn.addEventListener("click", copyDirections);
  const printBtn = document.getElementById("btn-print-directions");
  if (printBtn) printBtn.addEventListener("click", printDirections);

  document.getElementById("btn-open-peas").addEventListener("click", () => {
    document.getElementById("modal-peas").classList.add("open");
  });

  document.querySelectorAll(".btn-close-modal").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modalId = btn.dataset.close;
      document.getElementById(modalId).classList.remove("open");
    });
  });

  document.querySelectorAll(".modal-overlay").forEach((modal) => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("open");
    });
  });

  document
    .getElementById("btn-run-partial-sim")
    .addEventListener("click", runPartialObservabilitySim);

  // View Mode Toggle (Blueprint vs Google Maps)
  const btnBlueprint = document.getElementById("btn-view-blueprint");
  if (btnBlueprint) {
    btnBlueprint.addEventListener("click", () => switchMapView("blueprint"));
  }
  const btnGoogleMaps = document.getElementById("btn-view-google-maps");
  if (btnGoogleMaps) {
    btnGoogleMaps.addEventListener("click", () => switchMapView("google-maps"));
  }

  // Pre-load Google Maps SDK quietly in background
  setTimeout(loadGoogleMapsScript, 1000);

  // Dark / Light Theme Toggle
  document.getElementById("btn-theme-toggle").addEventListener("click", () => {
    state.theme = state.theme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", state.theme);
    document.getElementById("theme-icon").textContent =
      state.theme === "dark" ? "🌙" : "☀️";
  });
}

function updateNodeVisualStates() {
  state.graph.nodes.forEach((n) => {
    const circle = document.getElementById(`node-circle-${n.id}`);
    if (circle) circle.setAttribute("class", getNodeClass(n));
  });
  if (state.googleMap) {
    updateGoogleMapMarkersState();
  }
}

// ============================================================================
// GOOGLE MAPS INTEGRATION & HYBRID VIEWPORT MODULE
// ============================================================================

function switchMapView(mode) {
  state.mapView = mode;
  const svgElem = document.getElementById("campus-svg");
  const gmapContainer = document.getElementById("google-map-container");
  const btnBlueprint = document.getElementById("btn-view-blueprint");
  const btnGmap = document.getElementById("btn-view-google-maps");

  if (mode === "google-maps") {
    if (btnBlueprint) btnBlueprint.classList.remove("active");
    if (btnGmap) btnGmap.classList.add("active");
    if (svgElem) svgElem.style.display = "none";
    if (gmapContainer) gmapContainer.style.display = "block";

    if (!state.googleMapsLoaded) {
      loadGoogleMapsScript();
    } else if (state.googleMap && window.google && window.google.maps) {
      setTimeout(() => {
        try {
          google.maps.event.trigger(state.googleMap, "resize");
          highlightGoogleMapRoute();
        } catch (err) {
          console.warn("Resize Google Map caught:", err);
        }
      }, 60);
    }
  } else {
    if (btnBlueprint) btnBlueprint.classList.add("active");
    if (btnGmap) btnGmap.classList.remove("active");
    if (svgElem) svgElem.style.display = "block";
    if (gmapContainer) gmapContainer.style.display = "none";
  }
}

// Global hook for InfoWindow buttons
window.setMapEndpoint = function (nodeId, type) {
  if (type === "start") {
    state.startNodeId = nodeId;
    const select = document.getElementById("select-start-node");
    if (select) select.value = nodeId;
  } else {
    state.goalNodeId = nodeId;
    const select = document.getElementById("select-goal-node");
    if (select) select.value = nodeId;
  }
  updateNodeVisualStates();
  executeSearch();
  if (state.gmapInfoWindow) state.gmapInfoWindow.close();
};

function loadGoogleMapsScript() {
  if (window.google && window.google.maps) {
    state.googleMapsLoaded = true;
    initGoogleMapInstance();
    return;
  }

  // Gracefully handle auth/quota failures without throwing alert crashes
  window.gm_authFailure = function () {
    console.warn(
      "Google Maps Auth Callback: Authentication issue detected. Safely remaining in Blueprint Canvas mode.",
    );
    state.googleMapsError =
      "Google Maps key authentication notice: Please check billing or domain restrictions.";
    const statusPill = document.getElementById("gmap-status-pill");
    if (statusPill) {
      statusPill.textContent =
        "⚠️ Google Maps Notice: Active on Blueprint Canvas";
      statusPill.style.borderColor = "var(--accent-rose)";
    }
    setTimeout(() => {
      switchMapView("blueprint");
    }, 1800);
  };

  window.initGoogleMapSuccess = function () {
    state.googleMapsLoaded = true;
    initGoogleMapInstance();
  };

  if (document.getElementById("google-maps-sdk")) return;

  const script = document.createElement("script");
  script.id = "google-maps-sdk";
  script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&callback=initGoogleMapSuccess&loading=async`;
  script.async = true;
  script.defer = true;
  script.onerror = function () {
    console.warn(
      "Network offline or Google Maps SDK blocked. Seamlessly retaining Blueprint mode.",
    );
    state.googleMapsError =
      "Offline or Google Maps blocked. Using Blueprint Mode.";
    switchMapView("blueprint");
  };
  document.head.appendChild(script);
}

function getNodeLatLng(node) {
  if (node.lat && node.lng) {
    return { lat: Number(node.lat), lng: Number(node.lng) };
  }
  const BASE_LAT = 30.4;
  const BASE_LNG = 78.0786;
  const dy = (node.y - 350.0) * 0.32;
  const dx = (node.x - 500.0) * 0.22;
  const lat = BASE_LAT - dy / 111139.0;
  const lng =
    BASE_LNG + dx / (111139.0 * Math.cos((BASE_LAT * Math.PI) / 180.0));
  return { lat: parseFloat(lat.toFixed(6)), lng: parseFloat(lng.toFixed(6)) };
}

function initGoogleMapInstance() {
  const mount = document.getElementById("google-map-mount");
  if (!mount || !window.google || !window.google.maps) return;

  try {
    if (!state.googleMap) {
      state.googleMap = new google.maps.Map(mount, {
        center: { lat: 30.4, lng: 78.0786 },
        zoom: 18,
        mapTypeId: "hybrid", // Real high-res satellite imagery + labeled walkways
        tilt: 0,
        streetViewControl: false,
        fullscreenControl: true,
        mapTypeControl: true,
        mapTypeControlOptions: {
          style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
          position: google.maps.ControlPosition.TOP_LEFT,
        },
        zoomControl: true,
        zoomControlOptions: {
          position: google.maps.ControlPosition.RIGHT_CENTER,
        },
      });

      state.gmapInfoWindow = new google.maps.InfoWindow();

      state.googleMap.addListener("click", () => {
        if (state.gmapInfoWindow) state.gmapInfoWindow.close();
      });
    }

    renderGoogleMapElements();
    highlightGoogleMapRoute();
  } catch (err) {
    console.warn("Error initializing Google Maps instance:", err);
    switchMapView("blueprint");
  }
}

function getGoogleMapMarkerIcon(node, isExpanding = false) {
  if (!window.google || !window.google.maps) return null;

  if (isExpanding) {
    return {
      path: google.maps.SymbolPath.CIRCLE,
      scale: 12,
      fillColor: "#f59e0b",
      fillOpacity: 1,
      strokeColor: "#ffffff",
      strokeWeight: 2.5,
    };
  }
  if (node.is_blocked) {
    return {
      path: google.maps.SymbolPath.CIRCLE,
      scale: 9,
      fillColor: "#ef4444",
      fillOpacity: 1,
      strokeColor: "#ffffff",
      strokeWeight: 2,
    };
  }
  if (node.id === state.startNodeId) {
    return {
      path: google.maps.SymbolPath.CIRCLE,
      scale: 11,
      fillColor: "#0284c7",
      fillOpacity: 1,
      strokeColor: "#ffffff",
      strokeWeight: 2.5,
    };
  }
  if (node.id === state.goalNodeId) {
    return {
      path: google.maps.SymbolPath.CIRCLE,
      scale: 11,
      fillColor: "#10b981",
      fillOpacity: 1,
      strokeColor: "#ffffff",
      strokeWeight: 2.5,
    };
  }

  let catColor = "#38bdf8";
  if (node.category === "Laboratory") catColor = "#a855f7";
  else if (node.category === "Classroom") catColor = "#3b82f6";
  else if (node.category === "Office") catColor = "#f59e0b";
  else if (node.category === "Facility") catColor = "#10b981";

  return {
    path: google.maps.SymbolPath.CIRCLE,
    scale: 6.5,
    fillColor: catColor,
    fillOpacity: 0.9,
    strokeColor: "#ffffff",
    strokeWeight: 1.5,
  };
}

function renderGoogleMapElements() {
  if (!state.googleMap || !window.google || !window.google.maps) return;

  // Clear existing polylines
  state.gmapPolylines.forEach((p) => p.setMap(null));
  state.gmapPolylines = [];

  // Draw graph edges on Google Maps
  state.graph.edges.forEach((e) => {
    const n1 = state.graph.nodes.find((n) => n.id === e.source);
    const n2 = state.graph.nodes.find((n) => n.id === e.target);
    if (!n1 || !n2) return;

    let strokeColor = "#94a3b8";
    let strokeOpacity = 0.45;
    let strokeWeight = 2;

    if (e.is_blocked) {
      strokeColor = "#ef4444";
      strokeOpacity = 0.85;
      strokeWeight = 3;
    } else if (!e.accessible) {
      strokeColor = "#f59e0b";
      strokeOpacity = 0.65;
    }

    const poly = new google.maps.Polyline({
      path: [getNodeLatLng(n1), getNodeLatLng(n2)],
      strokeColor: strokeColor,
      strokeOpacity: strokeOpacity,
      strokeWeight: strokeWeight,
      map: state.googleMap,
    });

    // Right-click edge to toggle block on Google Maps
    poly.addListener("rightclick", () => {
      toggleBlock("edge", e.source, e.target, !e.is_blocked);
    });

    state.gmapPolylines.push(poly);
  });

  // Create or update node markers
  state.graph.nodes.forEach((node) => {
    const pos = getNodeLatLng(node);
    let marker = state.gmapMarkers[node.id];

    if (!marker) {
      marker = new google.maps.Marker({
        position: pos,
        map: state.googleMap,
        title: `${node.name} (${node.building}, F${node.floor})`,
        icon: getGoogleMapMarkerIcon(node),
      });

      marker.addListener("click", () => {
        handleNodeLeftClick(node.id);
        if (state.gmapInfoWindow) {
          const content = `
            <div style="color: #0f172a; font-family: 'Plus Jakarta Sans', sans-serif; font-size: 12px; min-width: 170px; line-height: 1.45; padding: 4px;">
              <div style="font-weight: 700; font-size: 13px; color: #0284c7;">${node.name}</div>
              <div style="color: #64748b; font-size: 11px;">${node.building} • Floor ${node.floor} (${node.category})</div>
              ${node.is_blocked ? '<div style="color: #ef4444; font-weight: bold; margin-top: 3px;">⚠️ [BLOCKED OBSTACLE]</div>' : ""}
              <div style="display: flex; gap: 6px; margin-top: 8px;">
                <button style="flex: 1; padding: 4px 8px; font-size: 11px; background: #0284c7; color: white; border: none; border-radius: 4px; cursor: pointer;" onclick="window.setMapEndpoint('${node.id}', 'start')">Set Start</button>
                <button style="flex: 1; padding: 4px 8px; font-size: 11px; background: #10b981; color: white; border: none; border-radius: 4px; cursor: pointer;" onclick="window.setMapEndpoint('${node.id}', 'goal')">Set Goal</button>
              </div>
            </div>
          `;
          state.gmapInfoWindow.setContent(content);
          state.gmapInfoWindow.open(state.googleMap, marker);
        }
      });

      marker.addListener("rightclick", () => {
        toggleBlock("node", node.id, null, !node.is_blocked);
      });

      state.gmapMarkers[node.id] = marker;
    } else {
      marker.setPosition(pos);
      marker.setIcon(getGoogleMapMarkerIcon(node));
    }
  });
}

function updateGoogleMapMarkersState() {
  if (!state.googleMap || !window.google || !window.google.maps) return;
  state.graph.nodes.forEach((node) => {
    const marker = state.gmapMarkers[node.id];
    if (marker) {
      marker.setIcon(getGoogleMapMarkerIcon(node));
    }
  });
}

function highlightGoogleMapRoute() {
  if (!state.googleMap || !window.google || !window.google.maps) return;

  if (state.gmapRoutePolyline) {
    state.gmapRoutePolyline.setMap(null);
    state.gmapRoutePolyline = null;
  }

  if (
    !state.searchResult ||
    !state.searchResult.success ||
    !state.searchResult.path_nodes ||
    state.searchResult.path_nodes.length === 0
  ) {
    return;
  }

  const coords = [];
  const bounds = new google.maps.LatLngBounds();

  state.searchResult.path_nodes.forEach((nodeId) => {
    const nodeObj = state.graph.nodes.find((n) => n.id === nodeId);
    if (nodeObj) {
      const pos = getNodeLatLng(nodeObj);
      coords.push(pos);
      bounds.extend(pos);
    }
  });

  if (coords.length > 0) {
    state.gmapRoutePolyline = new google.maps.Polyline({
      path: coords,
      strokeColor: "#10b981",
      strokeOpacity: 0.95,
      strokeWeight: 6,
      map: state.googleMap,
    });

    if (state.mapView === "google-maps" && !bounds.isEmpty()) {
      state.googleMap.fitBounds(bounds, 60);
    }
  }

  updateGoogleMapMarkersState();
}

function updateGoogleMapStep(currentStepNodeId) {
  if (!state.googleMap || !window.google || !window.google.maps) return;
  state.graph.nodes.forEach((n) => {
    const marker = state.gmapMarkers[n.id];
    if (!marker) return;
    if (n.id === currentStepNodeId) {
      marker.setIcon(getGoogleMapMarkerIcon(n, true));
      marker.setZIndex(999);
    } else {
      marker.setIcon(getGoogleMapMarkerIcon(n, false));
      marker.setZIndex(1);
    }
  });
}

function updateGoogleMapAvatar(nodeObj) {
  if (!state.googleMap || !window.google || !window.google.maps) return;
  const pos = getNodeLatLng(nodeObj);
  if (!state.gmapAvatarMarker) {
    state.gmapAvatarMarker = new google.maps.Marker({
      position: pos,
      map: state.googleMap,
      label: {
        text: "🚶",
        fontSize: "18px",
      },
      icon: {
        path: google.maps.SymbolPath.CIRCLE,
        scale: 14,
        fillColor: "#38bdf8",
        fillOpacity: 0.35,
        strokeColor: "#38bdf8",
        strokeWeight: 2,
      },
      zIndex: 9999,
    });
  } else {
    state.gmapAvatarMarker.setPosition(pos);
  }
}
