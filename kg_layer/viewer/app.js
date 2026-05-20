(function () {
  "use strict";

  const DATASETS = ["draft", "accepted", "selected"];
  const TYPES = ["Paper", "Concept", "Claim", "Evidence"];
  const TYPE_COLORS = {
    Paper: "#52616f",
    Concept: "#1b8a5a",
    Claim: "#b45b20",
    Evidence: "#6b55b6"
  };

  const state = {
    dataset: "selected",
    nodes: [],
    edges: [],
    detailById: new Map(),
    filteredNodes: [],
    filteredEdges: [],
    selected: null,
    typeFilters: new Set(TYPES),
    statusFilters: new Set(),
    search: "",
    transform: { x: 0, y: 0, scale: 1 },
    draggingNode: null,
    panning: null
  };

  const el = {
    dataset: document.getElementById("datasetSelect"),
    search: document.getElementById("searchInput"),
    typeFilters: document.getElementById("typeFilters"),
    statusFilters: document.getElementById("statusFilters"),
    loadStatus: document.getElementById("loadStatus"),
    nodeCount: document.getElementById("nodeCount"),
    edgeCount: document.getElementById("edgeCount"),
    visibleCount: document.getElementById("visibleCount"),
    avgConfidence: document.getElementById("avgConfidence"),
    graph: document.getElementById("graph"),
    viewport: document.getElementById("viewport"),
    edges: document.getElementById("edges"),
    edgeLabels: document.getElementById("edgeLabels"),
    nodes: document.getElementById("nodes"),
    emptyState: document.getElementById("emptyState"),
    detailsBody: document.getElementById("detailsBody"),
    selectionSummary: document.getElementById("selectionSummary"),
    fitButton: document.getElementById("fitButton"),
    resetButton: document.getElementById("resetButton")
  };

  function candidateUrls(dataset, file) {
    return [
      `../data/published/constraints/${dataset}/${file}`,
      `./data/published/constraints/${dataset}/${file}`,
      `../../kg_layer/data/published/constraints/${dataset}/${file}`
    ];
  }

  function perArticleUrls(articleId) {
    const file = `${articleId}.kg.json`;
    return [
      `../data/published/per_article/${file}`,
      `./data/published/per_article/${file}`,
      `../../kg_layer/data/published/per_article/${file}`
    ];
  }

  async function fetchJson(dataset, file) {
    const errors = [];
    for (const url of candidateUrls(dataset, file)) {
      try {
        const response = await fetch(url, { cache: "no-store" });
        if (response.ok) return await response.json();
        errors.push(`${url}: ${response.status}`);
      } catch (error) {
        errors.push(`${url}: ${error.message}`);
      }
    }
    throw new Error(errors.join("; "));
  }

  async function loadDataset(dataset) {
    state.dataset = dataset;
    state.selected = null;
    el.loadStatus.textContent = `Loading ${dataset}...`;
    try {
      const [nodes, edges] = await Promise.all([
        fetchJson(dataset, "constraint.nodes.json"),
        fetchJson(dataset, "constraint.edges.json")
      ]);
      state.nodes = Array.isArray(nodes) ? nodes.map(normalizeNode) : [];
      state.edges = Array.isArray(edges) ? edges.map(normalizeEdge) : [];
      state.detailById = await loadPerArticleDetails(state.nodes);
      state.nodes = state.nodes.map((node) => enrichNode(node));
      const statuses = Array.from(new Set(state.nodes.map((node) => node.status).filter(Boolean))).sort();
      state.statusFilters = new Set(statuses);
      renderStatusFilters(statuses);
      el.loadStatus.textContent = `${dataset}: ${state.nodes.length} nodes, ${state.edges.length} edges`;
    } catch (error) {
      state.nodes = [];
      state.edges = [];
      state.statusFilters = new Set();
      renderStatusFilters([]);
      el.loadStatus.textContent = `Missing or unreadable ${dataset} files`;
      console.warn(error);
    }
    applyFilters();
    fitGraph();
    renderDetails();
  }

  async function loadPerArticleDetails(nodes) {
    const details = new Map();
    const articleIds = Array.from(new Set(nodes.map((node) => node.article_id).filter(Boolean)));
    await Promise.all(articleIds.map(async (articleId) => {
      for (const url of perArticleUrls(articleId)) {
        try {
          const response = await fetch(url, { cache: "no-store" });
          if (!response.ok) continue;
          const objects = await response.json();
          if (Array.isArray(objects)) {
            objects.forEach((object) => {
              if (object && object.id) details.set(String(object.id), object);
            });
          }
          return;
        } catch (error) {
          console.warn(`Could not load details from ${url}`, error);
        }
      }
    }));
    return details;
  }

  function enrichNode(node) {
    const detail = state.detailById.get(node.id) || {};
    const label = node.canonical_label || detail.canonical_label || readableText(detail.supporting_quote_or_span) || node.label || node.id;
    return { ...detail, ...node, label };
  }

  function normalizeNode(node, index) {
    const label = node.canonical_label || node.label || node.title || node.id || `node-${index}`;
    return {
      ...node,
      id: String(node.id || `node-${index}`),
      type: node.type || "Unknown",
      status: node.status || "unknown",
      label,
      x: 0,
      y: 0
    };
  }

  function normalizeEdge(edge, index) {
    return {
      ...edge,
      id: edge.id || `${edge.source_id || edge.source}-${edge.target_id || edge.target}-${index}`,
      source_id: edge.source_id || edge.source,
      target_id: edge.target_id || edge.target,
      relation_type: edge.relation_type || edge.type || "related_to"
    };
  }

  function renderTypeFilters() {
    el.typeFilters.innerHTML = TYPES.map((type) => checkboxHtml("type", type, true)).join("");
    el.typeFilters.querySelectorAll("input").forEach((input) => {
      input.addEventListener("change", () => {
        toggleSetValue(state.typeFilters, input.value, input.checked);
        applyFilters();
      });
    });
  }

  function renderStatusFilters(statuses) {
    el.statusFilters.innerHTML = statuses.length
      ? statuses.map((status) => checkboxHtml("status", status, true)).join("")
      : '<p class="muted">No statuses found.</p>';
    el.statusFilters.querySelectorAll("input").forEach((input) => {
      input.addEventListener("change", () => {
        toggleSetValue(state.statusFilters, input.value, input.checked);
        applyFilters();
      });
    });
  }

  function checkboxHtml(name, value, checked) {
    return `<label><input type="checkbox" name="${name}" value="${escapeHtml(value)}" ${checked ? "checked" : ""}>${escapeHtml(value)}</label>`;
  }

  function toggleSetValue(set, value, enabled) {
    if (enabled) set.add(value);
    else set.delete(value);
  }

  function applyFilters() {
    const query = state.search.trim().toLowerCase();
    state.filteredNodes = state.nodes.filter((node) => {
      const matchesType = state.typeFilters.has(node.type);
      const matchesStatus = state.statusFilters.size === 0 || state.statusFilters.has(node.status);
      const haystack = [
        node.id, node.label, node.type, node.status, node.source_section,
        node.source_document, node.source_citation, node.citation, node.article_id
      ].filter(Boolean).join(" ").toLowerCase();
      return matchesType && matchesStatus && (!query || haystack.includes(query));
    });
    const visibleIds = new Set(state.filteredNodes.map((node) => node.id));
    state.filteredEdges = state.edges.filter((edge) => visibleIds.has(edge.source_id) && visibleIds.has(edge.target_id));
    layoutGraph();
    renderGraph();
    renderMetrics();
  }

  function layoutGraph() {
    const width = el.graph.clientWidth || 900;
    const height = el.graph.clientHeight || 700;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.max(120, Math.min(width, height) * 0.34);
    const byId = new Map(state.filteredNodes.map((node) => [node.id, node]));
    state.filteredNodes.forEach((node, index) => {
      if (node.x || node.y) return;
      const angle = (index / Math.max(1, state.filteredNodes.length)) * Math.PI * 2;
      const ring = radius + (index % 5) * 18;
      node.x = centerX + Math.cos(angle) * ring;
      node.y = centerY + Math.sin(angle) * ring;
    });
    for (let i = 0; i < 120; i += 1) {
      state.filteredEdges.forEach((edge) => {
        const source = byId.get(edge.source_id);
        const target = byId.get(edge.target_id);
        if (!source || !target) return;
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const distance = Math.max(1, Math.hypot(dx, dy));
        const force = (distance - 145) * 0.006;
        source.x += dx * force;
        source.y += dy * force;
        target.x -= dx * force;
        target.y -= dy * force;
      });
      for (let a = 0; a < state.filteredNodes.length; a += 1) {
        for (let b = a + 1; b < state.filteredNodes.length; b += 1) {
          const one = state.filteredNodes[a];
          const two = state.filteredNodes[b];
          const dx = two.x - one.x;
          const dy = two.y - one.y;
          const distance = Math.max(1, Math.hypot(dx, dy));
          const push = Math.min(2.5, 180 / (distance * distance));
          one.x -= dx * push;
          one.y -= dy * push;
          two.x += dx * push;
          two.y += dy * push;
        }
      }
    }
  }

  function renderGraph() {
    const byId = new Map(state.filteredNodes.map((node) => [node.id, node]));
    el.edges.innerHTML = "";
    el.edgeLabels.innerHTML = "";
    el.nodes.innerHTML = "";
    state.filteredEdges.forEach((edge) => {
      const source = byId.get(edge.source_id);
      const target = byId.get(edge.target_id);
      if (!source || !target) return;
      const line = svg("line", {
        class: `edge-line ${isSelected("edge", edge.id) ? "selected" : ""}`,
        x1: source.x, y1: source.y, x2: target.x, y2: target.y
      });
      line.addEventListener("click", () => selectItem("edge", edge));
      el.edges.appendChild(line);
      const label = svg("text", {
        class: "edge-label",
        x: (source.x + target.x) / 2,
        y: (source.y + target.y) / 2 - 6
      });
      label.textContent = edge.relation_type;
      label.addEventListener("click", () => selectItem("edge", edge));
      el.edgeLabels.appendChild(label);
    });
    state.filteredNodes.forEach((node) => {
      const group = svg("g", { class: `node ${isSelected("node", node.id) ? "selected" : ""}`, transform: `translate(${node.x},${node.y})` });
      const circle = svg("circle", { r: nodeRadius(node), fill: TYPE_COLORS[node.type] || "#7b8794" });
      const text = svg("text", { x: nodeRadius(node) + 5, y: 4 });
      text.textContent = truncate(node.label || node.id, 34);
      group.append(circle, text);
      group.addEventListener("pointerdown", (event) => startNodeDrag(event, node));
      group.addEventListener("click", () => selectItem("node", node));
      el.nodes.appendChild(group);
    });
    el.emptyState.hidden = state.filteredNodes.length > 0;
  }

  function nodeRadius(node) {
    if (node.type === "Paper") return 12;
    if (node.type === "Claim") return 10;
    return 8;
  }

  function renderMetrics() {
    const confidences = state.filteredNodes.map((node) => Number(node.confidence)).filter(Number.isFinite);
    const avg = confidences.length ? confidences.reduce((a, b) => a + b, 0) / confidences.length : null;
    el.nodeCount.textContent = state.nodes.length;
    el.edgeCount.textContent = state.edges.length;
    el.visibleCount.textContent = state.filteredNodes.length;
    el.avgConfidence.textContent = avg == null ? "-" : avg.toFixed(2);
  }

  function selectItem(kind, item) {
    state.selected = { kind, item };
    renderGraph();
    renderDetails();
  }

  function renderDetails() {
    if (!state.selected) {
      el.selectionSummary.textContent = "No selection";
      el.detailsBody.innerHTML = '<p class="muted">Select a node or edge to inspect provenance and review metadata.</p>';
      return;
    }
    const item = state.selected.item;
    el.selectionSummary.textContent = state.selected.kind === "node" ? `${item.type} / ${item.status}` : item.relation_type;
    const fields = state.selected.kind === "node"
      ? ["id", "type", "status", "review_status", "confidence", "label", "supporting_quote_or_span", "source_section", "source_document", "source_citation", "citation", "citation_ids", "reviewer", "reviewed_at", "reviewer_notes", "canonical_label", "canonical_id", "aliases", "ontology_mappings", "article_id", "run_id", "iri"]
      : ["id", "source_id", "target_id", "relation_type", "confidence", "provenance.status", "provenance.source_section", "provenance.source_document", "reviewer", "review_notes"];
    el.detailsBody.innerHTML = fields.map((field) => detailRow(field, getPath(item, field))).filter(Boolean).join("");
  }

  function detailRow(label, value) {
    if (value == null || value === "" || (Array.isArray(value) && value.length === 0)) return "";
    const display = Array.isArray(value) ? value.join(", ") : String(value);
    return `<div class="detail-row"><label>${escapeHtml(label)}</label><div>${escapeHtml(display)}</div></div>`;
  }

  function fitGraph() {
    const nodes = state.filteredNodes;
    if (!nodes.length) {
      setTransform(0, 0, 1);
      return;
    }
    const xs = nodes.map((node) => node.x);
    const ys = nodes.map((node) => node.y);
    const minX = Math.min(...xs) - 80;
    const maxX = Math.max(...xs) + 180;
    const minY = Math.min(...ys) - 80;
    const maxY = Math.max(...ys) + 80;
    const scale = Math.min(1.6, Math.max(0.25, Math.min(el.graph.clientWidth / (maxX - minX), el.graph.clientHeight / (maxY - minY))));
    setTransform((el.graph.clientWidth - (minX + maxX) * scale) / 2, (el.graph.clientHeight - (minY + maxY) * scale) / 2, scale);
  }

  function setTransform(x, y, scale) {
    state.transform = { x, y, scale };
    el.viewport.setAttribute("transform", `translate(${x} ${y}) scale(${scale})`);
  }

  function startNodeDrag(event, node) {
    event.stopPropagation();
    state.draggingNode = { node, start: pointerToGraph(event), moved: false };
    el.graph.setPointerCapture(event.pointerId);
  }

  function onPointerMove(event) {
    if (state.draggingNode) {
      const point = pointerToGraph(event);
      state.draggingNode.node.x += point.x - state.draggingNode.start.x;
      state.draggingNode.node.y += point.y - state.draggingNode.start.y;
      state.draggingNode.start = point;
      state.draggingNode.moved = true;
      renderGraph();
    } else if (state.panning) {
      const dx = event.clientX - state.panning.x;
      const dy = event.clientY - state.panning.y;
      state.panning = { x: event.clientX, y: event.clientY };
      setTransform(state.transform.x + dx, state.transform.y + dy, state.transform.scale);
    }
  }

  function pointerToGraph(event) {
    const rect = el.graph.getBoundingClientRect();
    return {
      x: (event.clientX - rect.left - state.transform.x) / state.transform.scale,
      y: (event.clientY - rect.top - state.transform.y) / state.transform.scale
    };
  }

  function svg(tag, attrs) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  }

  function getPath(object, path) {
    return path.split(".").reduce((value, key) => value && value[key], object);
  }

  function isSelected(kind, id) {
    return state.selected && state.selected.kind === kind && state.selected.item.id === id;
  }

  function truncate(value, max) {
    return value.length > max ? `${value.slice(0, max - 1)}...` : value;
  }

  function readableText(value) {
    if (!value) return "";
    return String(value).replace(/\s+/g, " ").trim();
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    }[char]));
  }

  el.dataset.addEventListener("change", () => loadDataset(el.dataset.value));
  el.search.addEventListener("input", () => {
    state.search = el.search.value;
    applyFilters();
  });
  el.fitButton.addEventListener("click", fitGraph);
  el.resetButton.addEventListener("click", () => {
    state.typeFilters = new Set(TYPES);
    state.statusFilters = new Set(Array.from(new Set(state.nodes.map((node) => node.status).filter(Boolean))));
    state.search = "";
    el.search.value = "";
    renderTypeFilters();
    renderStatusFilters(Array.from(state.statusFilters).sort());
    applyFilters();
  });
  el.graph.addEventListener("pointerdown", (event) => {
    if (event.target === el.graph) state.panning = { x: event.clientX, y: event.clientY };
  });
  el.graph.addEventListener("pointermove", onPointerMove);
  el.graph.addEventListener("pointerup", () => {
    state.draggingNode = null;
    state.panning = null;
  });
  el.graph.addEventListener("wheel", (event) => {
    event.preventDefault();
    const nextScale = Math.max(0.2, Math.min(2.5, state.transform.scale * (event.deltaY > 0 ? 0.9 : 1.1)));
    setTransform(state.transform.x, state.transform.y, nextScale);
  }, { passive: false });
  window.addEventListener("resize", fitGraph);

  renderTypeFilters();
  loadDataset(state.dataset);
}());
