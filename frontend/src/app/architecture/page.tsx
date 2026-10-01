"use client";

import { useEffect, useMemo, useState, type CSSProperties, type KeyboardEvent } from "react";
import RepoLensSidebar from "@/components/RepoLensSidebar";
import { getRepositoryAnalysis, type RepositoryAnalysis } from "@/lib/api";

type ArchitectureModule = {
  file?: string;
  module_name?: string;
  type?: string;
  layer?: string;
  incoming_dependencies?: string[];
  outgoing_dependencies?: string[];
  incoming_count?: number;
  outgoing_count?: number;
  total_connections?: number;
  [key: string]: unknown;
};
type GraphNode = { id: string; label: string; type?: string };
type GraphEdge = { source: string; target: string };
type ArchitectureData = {
  production_modules?: ArchitectureModule[];
  layer_summary?: Record<string, number>;
  graph?: { nodes?: GraphNode[]; edges?: GraphEdge[] };
  graph_summary?: { node_count?: number; edge_count?: number; isolated_node_count?: number };
};
type Point = { x: number; y: number; z: number };

type Tone = { main: string; soft: string; glow: string };

// Static star field: deterministic, allocation-free after module load.
// It gives the architecture view a galaxy/constellation identity without a
// physics engine, requestAnimationFrame loop, or random layout jitter.
const GALAXY_STARS = Array.from({ length: 72 }, (_, index) => ({
  x: 3 + ((index * 47) % 94),
  y: 6 + ((index * 71) % 88),
  r: index % 11 === 0 ? 1.7 : index % 5 === 0 ? 1.15 : 0.72,
  opacity: 0.18 + ((index * 13) % 38) / 100,
  delay: `${-(index % 9) * 0.55}s`,
}));

function asArchitectureData(value: RepositoryAnalysis["architecture"]): ArchitectureData {
  return (value ?? {}) as ArchitectureData;
}

function tone(layer = ""): Tone {
  const value = layer.toLowerCase();
  if (value.includes("presentation") || value.includes("api")) {
    return { main: "#8cf5c7", soft: "rgba(140,245,199,.11)", glow: "rgba(140,245,199,.26)" };
  }
  if (value.includes("domain") || value.includes("service")) {
    return { main: "#7aa2ff", soft: "rgba(122,162,255,.11)", glow: "rgba(122,162,255,.25)" };
  }
  if (value.includes("data") || value.includes("storage")) {
    return { main: "#c0b2ff", soft: "rgba(192,178,255,.10)", glow: "rgba(192,178,255,.23)" };
  }
  return { main: "#9ca9ba", soft: "rgba(156,169,186,.09)", glow: "rgba(156,169,186,.18)" };
}



function buildPositions(nodes: GraphNode[], edges: GraphEdge[], modules: ArchitectureModule[]): Map<string, Point> {
  const moduleMap = new Map(modules.map((item) => [item.file ?? item.module_name ?? "", item]));
  const degree = new Map<string, number>();
  nodes.forEach((node) => degree.set(node.id, 0));
  edges.forEach((edge) => {
    degree.set(edge.source, (degree.get(edge.source) ?? 0) + 1);
    degree.set(edge.target, (degree.get(edge.target) ?? 0) + 1);
  });

  // Stable ordering only. The coordinates below are deterministic and do not
  // depend on a physics simulation, randomness, browser size, or render timing.
  const ordered = [...nodes].sort((a, b) => {
    const layerA = String(moduleMap.get(a.id)?.layer ?? "source");
    const layerB = String(moduleMap.get(b.id)?.layer ?? "source");
    return layerA.localeCompare(layerB)
      || (degree.get(b.id) ?? 0) - (degree.get(a.id) ?? 0)
      || a.id.localeCompare(b.id);
  });

  const total = ordered.length;
  const positions = new Map<string, Point>();
  if (!total) return positions;

  const cx = 540;
  const cy = 320;
  const nodeGap = total <= 12 ? 118 : total <= 24 ? 92 : 76;

  // Keep the first ring outside the visual footprint of the repository core.
  // Additional rings give the graph enough circumference to avoid stacked nodes.
  const ringCounts = total <= 8
    ? [total]
    : total <= 14
      ? [7, total - 7]
      : total <= 24
        ? [8, 6, total - 14]
        : total <= 40
          ? [10, 9, 9, total - 28]
          : [12, 12, 12, Math.max(1, total - 36)];

  const radii = total <= 14 ? [185, 310, 420, 500] : [180, 290, 395, 485];
  let cursor = 0;

  ringCounts.forEach((count, ringIndex) => {
    if (cursor >= total) return;
    const actual = Math.min(count, total - cursor);
    const radius = radii[Math.min(ringIndex, radii.length - 1)];
    // Rotate each ring so nodes never form a repeated vertical stack.
    const phase = ringIndex % 2 === 0 ? -Math.PI / 2 : -Math.PI / 2 + Math.PI / actual;

    for (let i = 0; i < actual; i += 1) {
      const node = ordered[cursor + i];
      const angle = phase + (i / actual) * Math.PI * 2;
      positions.set(node.id, {
        x: cx + Math.cos(angle) * radius,
        y: cy + Math.sin(angle) * radius * 0.58,
        z: 1 - ringIndex * 0.08,
      });
    }
    cursor += actual;
  });

  // Deterministic collision relaxation. This is calculated once with a fixed
  // iteration count; it is not a runtime physics engine. It guarantees that
  // nodes with an unfortunate angular alignment are pushed apart.
  const nodeRadius = total > 40 ? 13 : total > 24 ? 19 : 23;
  const minDistance = Math.max(nodeGap, nodeRadius * 2 + 30);
  const coreClearance = 132;
  const bounds = { minX: 70, maxX: 1010, minY: 82, maxY: 558 };

  for (let iteration = 0; iteration < 18; iteration += 1) {
    let changed = false;
    const points = ordered.map((node) => ({ node, point: positions.get(node.id)! }));

    for (let i = 0; i < points.length; i += 1) {
      for (let j = i + 1; j < points.length; j += 1) {
        const a = points[i].point;
        const b = points[j].point;
        let dx = b.x - a.x;
        let dy = b.y - a.y;
        let distance = Math.hypot(dx, dy);
        if (distance >= minDistance) continue;

        if (distance < 0.001) {
          dx = 1;
          dy = 0;
          distance = 1;
        }
        const push = (minDistance - distance) / distance * 0.5;
        a.x -= dx * push;
        a.y -= dy * push;
        b.x += dx * push;
        b.y += dy * push;
        changed = true;
      }
    }

    for (const { point } of points) {
      const dx = point.x - cx;
      const dy = point.y - cy;
      const distance = Math.hypot(dx, dy) || 1;
      if (distance < coreClearance) {
        const scale = coreClearance / distance;
        point.x = cx + dx * scale;
        point.y = cy + dy * scale;
        changed = true;
      }

      point.x = Math.max(bounds.minX, Math.min(bounds.maxX, point.x));
      point.y = Math.max(bounds.minY, Math.min(bounds.maxY, point.y));
    }

    if (!changed) break;
  }

  return positions;
}

function shortLabel(value: string, max = 23): string {
  if (value.length <= max) return value;
  return `${value.slice(0, max - 1)}…`;
}

function ArchitectureScene({
  nodes,
  edges,
  modules,
  selected,
  focus,
  onSelect,
}: {
  nodes: GraphNode[];
  edges: GraphEdge[];
  modules: ArchitectureModule[];
  selected: string | null;
  focus: string | null;
  onSelect: (node: GraphNode) => void;
}) {
  const moduleMap = useMemo(
    () => new Map(modules.map((item) => [item.file ?? item.module_name ?? "", item])),
    [modules],
  );
  const positions = useMemo(() => buildPositions(nodes, edges, modules), [nodes, edges, modules]);
  const visibleIds = useMemo(() => new Set(nodes.map((node) => node.id)), [nodes]);
  const visibleEdges = useMemo(
    () => edges.filter((edge) => visibleIds.has(edge.source) && visibleIds.has(edge.target)),
    [edges, visibleIds],
  );
  const activeNeighbors = useMemo(() => {
    const result = new Set<string>();
    if (!focus) return result;
    visibleEdges.forEach((edge) => {
      if (edge.source === focus) result.add(edge.target);
      if (edge.target === focus) result.add(edge.source);
    });
    return result;
  }, [visibleEdges, focus]);

  const denseGraph = visibleEdges.length > 260;

  function handleNodeKey(event: KeyboardEvent<SVGGElement>, node: GraphNode) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      event.stopPropagation();
      onSelect(node);
    }
  }

  return (
    <div className="rl-arch-canvas">
      <div className="rl-arch-canvas-top">
        <div>
          <span className="rl-kicker">CODEBASE CONSTELLATION</span>
          <p>Every node and relationship is resolved from repository evidence.</p>
        </div>
        <div className="rl-live"><span /> DETERMINISTIC{denseGraph ? <b> · DENSE GRAPH</b> : null}</div>
      </div>

      <div className="rl-arch-space">
        <div className="rl-depth-plane rl-depth-plane-back" />
        <div className="rl-depth-plane rl-depth-plane-mid" />
        <div className="rl-depth-plane rl-depth-plane-front" />
        <div className="rl-arch-core"><div className="rl-core-pulse" /><span>REPO</span><small>SOURCE</small></div>

        <svg
          viewBox="0 0 1080 640"
          className="rl-arch-svg"
          aria-label="Interactive repository architecture graph"
          role="img"
        >
          <defs>
            <radialGradient id="rlNebulaBlue" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#78a8ff" stopOpacity=".18" />
              <stop offset="55%" stopColor="#5d7dff" stopOpacity=".055" />
              <stop offset="100%" stopColor="#5d7dff" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="rlNebulaMint" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#79efc1" stopOpacity=".12" />
              <stop offset="58%" stopColor="#4fe0bd" stopOpacity=".035" />
              <stop offset="100%" stopColor="#4fe0bd" stopOpacity="0" />
            </radialGradient>
            <linearGradient id="rlGalaxyCore" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#e6f3ff" />
              <stop offset="38%" stopColor="#8cc7ff" />
              <stop offset="100%" stopColor="#72e6c3" />
            </linearGradient>
            <linearGradient id="rlEdgeSignal" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stopColor="#7aa2ff" stopOpacity=".12" />
              <stop offset=".5" stopColor="#8cf5c7" stopOpacity=".82" />
              <stop offset="1" stopColor="#c0b2ff" stopOpacity=".14" />
            </linearGradient>
            <filter id="rlNodeGlow" x="-100%" y="-100%" width="300%" height="300%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>

          <g className="rl-galaxy-field" aria-hidden="true">
            <ellipse cx="540" cy="320" rx="430" ry="225" className="rl-galaxy-nebula" fill="url(#rlNebulaBlue)" />
            <ellipse cx="540" cy="320" rx="290" ry="160" className="rl-galaxy-nebula rl-galaxy-nebula-mint" fill="url(#rlNebulaMint)" />
            <ellipse cx="540" cy="320" rx="420" ry="185" className="rl-galaxy-orbit" />
            <ellipse cx="540" cy="320" rx="320" ry="140" className="rl-galaxy-orbit rl-galaxy-orbit-inner" />
            {GALAXY_STARS.map((star, index) => (
              <circle
                key={`star-${index}`}
                cx={`${star.x}%`}
                cy={`${star.y}%`}
                r={star.r}
                fill={index % 7 === 0 ? "#9fe9ff" : index % 5 === 0 ? "#b9b1ff" : "#dce9ff"}
                opacity={star.opacity}
                style={{ animationDelay: star.delay }}
                className="rl-galaxy-star"
              />
            ))}
          </g>

          {visibleEdges.map((edge, index) => {
            const source = positions.get(edge.source);
            const target = positions.get(edge.target);
            if (!source || !target) return null;
            const connected = selected === edge.source || selected === edge.target || focus === edge.source || focus === edge.target;
            const muted = Boolean(focus) && !connected && !activeNeighbors.has(edge.source) && !activeNeighbors.has(edge.target);
            const midX = (source.x + target.x) / 2;
            const midY = (source.y + target.y) / 2;
            const dx = target.x - source.x;
            const dy = target.y - source.y;
            const length = Math.max(1, Math.hypot(dx, dy));
            const curve = ((index % 5) - 2) * 22;
            const controlX = midX - (dy / length) * curve;
            const controlY = midY + (dx / length) * curve;
            return (
              <path
                key={`${edge.source}-${edge.target}-${index}`}
                d={`M ${source.x} ${source.y} Q ${controlX} ${controlY} ${target.x} ${target.y}`}
                className={connected && !denseGraph ? "rl-edge rl-edge-active" : "rl-edge"}
                stroke={connected ? "url(#rlEdgeSignal)" : "rgba(160,176,196,.13)"}
                opacity={muted ? .035 : connected ? .9 : denseGraph ? .19 : .34}
              />
            );
          })}

          {nodes.map((node, index) => {
            const point = positions.get(node.id);
            if (!point) return null;
            const item = moduleMap.get(node.id);
            const colors = tone(item?.layer);
            const isSelected = selected === node.id;
            const isActive = isSelected || focus === node.id || activeNeighbors.has(node.id);
            const muted = Boolean(focus) && !isActive;
            const nodeRadius = nodes.length > 60 ? 13 : nodes.length > 40 ? 16 : nodes.length > 24 ? 19 : 23;
            const hitRadius = nodeRadius + 30;
            const label = shortLabel(node.label, 22);
            const dx = point.x - 540;
            const dy = point.y - 320;
            const horizontal = Math.abs(dx) >= Math.abs(dy);
            // Labels always expand away from the repository core. Do not use
            // array index parity here: the label side must be determined by
            // the node's actual quadrant so selection never pulls a card back
            // across the graph toward REPO.
            const nodeOnRight = dx >= 0;
            const nodeBelow = dy >= 0;
            const labelWidth = 176;
            const labelOnSide = horizontal;
            const labelX = labelOnSide ? (nodeOnRight ? 30 : -206) : -88;
            const labelY = labelOnSide ? -24 : (nodeBelow ? 34 : -82);
            const labelAnchor = labelOnSide ? (nodeOnRight ? "start" : "end") : "middle";
            const labelTextX = labelOnSide ? (nodeOnRight ? 42 : -42) : 0;
            return (
              <g
                key={node.id}
                transform={`translate(${point.x} ${point.y})`}
                className={`rl-node ${isSelected ? "is-selected" : ""}`}
                opacity={muted ? .3 : 1}
                tabIndex={0}
                role="button"
                aria-label={`Select ${node.label}`}
                onClick={(event) => {
                  event.stopPropagation();
                  onSelect(node);
                }}
                onKeyDown={(event) => handleNodeKey(event, node)}
              >
                <circle r={hitRadius} fill="transparent" pointerEvents="all" className="rl-node-hit" />
                <circle r={isActive ? nodeRadius + 4 : nodeRadius} fill={colors.soft} stroke={isSelected ? colors.main : "rgba(238,245,255,.30)"} strokeWidth={isSelected ? 2.2 : 1.1} pointerEvents="none" />
                <circle r={isActive ? Math.max(5, nodeRadius * .32) : Math.max(4, nodeRadius * .26)} fill={colors.main} filter={isActive ? "url(#rlNodeGlow)" : undefined} pointerEvents="none" />
                <circle r={isActive ? nodeRadius + 8 : nodeRadius + 5} fill="none" stroke={colors.main} strokeOpacity={isSelected ? ".42" : ".10"} strokeDasharray="2 8" pointerEvents="none" />
                <text y="3" textAnchor="middle" fill="#07100d" fontSize="7" fontWeight="900" pointerEvents="none">
                  {String(index + 1).padStart(2, "0")}
                </text>
                <g className="rl-node-label" pointerEvents="none">
                  <rect className="rl-node-label-bg" x={labelX} y={labelY} width={labelWidth} height="48" rx="10" fill="rgba(7,10,16,.97)" stroke={colors.main} strokeOpacity={isSelected ? ".58" : ".16"} />
                  <text x={labelTextX} y={labelY + 20} textAnchor={labelAnchor} fill="#f3f8ff" fontSize="9" fontWeight={isSelected ? "700" : "500"} fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
                    {label}
                  </text>
                  <text x={labelTextX} y={labelY + 35} textAnchor={labelAnchor} fill={colors.main} fontSize="7" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
                    {item?.layer ?? "source"}
                  </text>
                </g>
                <title>{node.label} — {node.id}</title>
              </g>
            );
          })}
        </svg>
      </div>

      <div className="rl-arch-canvas-bottom">
        <span><i className="rl-dot mint" /> api / interface</span>
        <span><i className="rl-dot blue" /> service / domain</span>
        <span><i className="rl-dot lilac" /> data / storage</span>
        <span className="rl-canvas-hint">HOVER TO IDENTIFY · CLICK TO INSPECT · TRACE TO ISOLATE IMPACT</span>
      </div>
    </div>
  );
}

function Inspector({ node, module, connected }: { node: GraphNode | null; module: ArchitectureModule | null; connected: string[] }) {
  if (!node || !module) {
    return (
      <aside className="rl-inspector rl-inspector-empty">
        <span className="rl-kicker">MODULE INSPECTOR</span>
        <h2>Choose a module.</h2>
        <p>Selection is intentionally separate from focus so one click never changes the camera state.</p>
        <div className="rl-inspector-guide"><span>01</span> Select a node<br /><span>02</span> Read its relationships<br /><span>03</span> Focus only when you want the impact surface</div>
      </aside>
    );
  }
  const incoming = module.incoming_count ?? module.incoming_dependencies?.length ?? 0;
  const outgoing = module.outgoing_count ?? module.outgoing_dependencies?.length ?? 0;
  const impact = module.total_connections ?? incoming + outgoing;
  const colors = tone(module.layer);
  return (
    <aside className="rl-inspector" style={{ "--inspector-accent": colors.main, "--inspector-glow": colors.glow } as CSSProperties}>
      <div className="rl-inspector-head"><div><span className="rl-kicker">SELECTED MODULE</span><h2>{module.module_name ?? node.label}</h2><code>{module.file ?? node.id}</code></div><span className="rl-layer-tag">{module.layer ?? "production"}</span></div>
      <div className="rl-impact-grid"><div><small>INCOMING</small><strong>{incoming}</strong></div><div><small>OUTGOING</small><strong>{outgoing}</strong></div><div><small>IMPACT</small><strong>{impact}</strong></div></div>
      <div className="rl-inspector-section"><span className="rl-kicker">CONNECTED MODULES</span><div className="rl-relationship-list">{connected.length ? connected.map((item) => <div key={item}><span />{item}</div>) : <p>No direct relationships detected.</p>}</div></div>
      <div className="rl-inspector-note">Deterministic dependency evidence · no generated topology</div>
    </aside>
  );
}

function ArchitectureState({ mode, message }: { mode: "loading" | "error"; message?: string }) {
  const isLoading = mode === "loading";
  return (
    <div className="rl-architecture-state">
      <div className="rl-state-grid" aria-hidden="true" />
      <div className="rl-state-nebula" aria-hidden="true" />
      <div className="rl-state-orbit orbit-a" aria-hidden="true" />
      <div className="rl-state-orbit orbit-b" aria-hidden="true" />
      <div className="rl-state-core" aria-hidden="true">
        <span>RL</span>
        <small>{isLoading ? "SCANNING" : "OFFLINE"}</small>
      </div>
      <div className="rl-state-copy">
        <span className="rl-kicker">CODEBASE CONSTELLATION</span>
        <h1>{isLoading ? "Reconstructing the codebase." : "The constellation is waiting for its source."}</h1>
        <p>
          {isLoading
            ? "RepoLens is loading the deterministic architecture graph and its supporting evidence."
            : "The visual system is ready, but the repository analysis API did not return an architecture model. No graph data is being invented or cached as a fake result."}
        </p>
        {!isLoading && (
          <div className="rl-state-error">
            <span className="rl-state-error-dot" />
            <div>
              <strong>Analysis connection unavailable</strong>
              <small>{message}</small>
            </div>
          </div>
        )}
        <div className="rl-state-meta">
          <span><i /> SOURCE-DERIVED GRAPH</span>
          <span><i /> NO SYNTHETIC RELATIONSHIPS</span>
          <span><i /> READY WHEN API CONNECTS</span>
        </div>
      </div>
    </div>
  );
}

export default function ArchitecturePage() {
  const [analysis, setAnalysis] = useState<RepositoryAnalysis | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [focusId, setFocusId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    getRepositoryAnalysis()
      .then((result) => { if (mounted) setAnalysis(result); })
      .catch((err) => { if (mounted) setError(err instanceof Error ? err.message : "Failed to load repository architecture."); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

  const architecture = useMemo(() => analysis ? asArchitectureData(analysis.architecture) : null, [analysis]);
  const modules = useMemo(() => architecture?.production_modules ?? [], [architecture]);
  const nodes = useMemo(() => architecture?.graph?.nodes ?? [], [architecture]);
  const edges = useMemo(() => architecture?.graph?.edges ?? [], [architecture]);
  const filtered = useMemo(() => {
    const value = query.trim().toLowerCase();
    if (!value) return nodes;
    return nodes.filter((node) => node.label.toLowerCase().includes(value) || node.id.toLowerCase().includes(value));
  }, [nodes, query]);
  const visibleSelectedId = selectedId && filtered.some((node) => node.id === selectedId) ? selectedId : null;
  const visibleFocusId = focusId && filtered.some((node) => node.id === focusId) ? focusId : null;
  const selectedNode = filtered.find((item) => item.id === visibleSelectedId) ?? null;
  const selectedModule = modules.find((item) => item.file === selectedNode?.id || item.module_name === selectedNode?.label) ?? null;
  const connected = useMemo(() => {
    if (!selectedNode) return [];
    const ids = new Set<string>();
    edges.forEach((edge) => {
      if (edge.source === selectedNode.id) ids.add(edge.target);
      if (edge.target === selectedNode.id) ids.add(edge.source);
    });
    return nodes.filter((node) => ids.has(node.id)).map((node) => node.label);
  }, [selectedNode, edges, nodes]);


  if (loading) {
    return (
      <main className="rl-architecture-shell">
        <div className="flex min-h-screen">
          <RepoLensSidebar />
          <section className="rl-architecture-content">
            <ArchitectureState mode="loading" />
          </section>
        </div>
      </main>
    );
  }

  if (error || !architecture) {
    return (
      <main className="rl-architecture-shell">
        <div className="flex min-h-screen">
          <RepoLensSidebar />
          <section className="rl-architecture-content">
            <ArchitectureState
              mode="error"
              message={error ?? "No architecture evidence was returned by the backend."}
            />
          </section>
        </div>
      </main>
    );
  }

  const layerCount = Object.keys(architecture.layer_summary ?? {}).length;
  const edgeCount = architecture.graph_summary?.edge_count ?? edges.length;

  return (
    <main className="rl-architecture-shell">
      <div className="flex min-h-screen">
        <RepoLensSidebar />
        <section className="rl-architecture-content">
          <header className="rl-architecture-nav">
            <div className="rl-brandline"><span className="rl-brand-mark">RL</span><div><span>REPOLENS</span><small>CODEBASE OBSERVATORY</small></div></div>
            <div className="rl-nav-status"><span /> SOURCE-DERIVED <b>·</b> {nodes.length} MODULES</div>
          </header>
          <div className="rl-architecture-wrap">
            <div className="rl-architecture-hero">
              <div>
                <span className="rl-kicker">ARCHITECTURE / OBSERVATORY</span>
                <h1>See the codebase as a <em>living system.</em></h1>
                <p>Trace real module relationships, inspect local impact, and isolate a dependency surface without hiding the evidence underneath the visualization.</p>
              </div>
              <div className="rl-hero-meta"><div><strong>{nodes.length}</strong><span>modules</span></div><div><strong>{edgeCount}</strong><span>relations</span></div><div><strong>{layerCount}</strong><span>layers</span></div></div>
            </div>

            <div className="rl-controlbar rl-controlbar-sticky">
              <label><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Find a module or path" aria-label="Search module or path" /><kbd>⌘ K</kbd></label>
              <div className="rl-control-actions"><button type="button" onClick={() => setFocusId(visibleSelectedId)} disabled={!visibleSelectedId}>Trace impact</button><button type="button" onClick={() => { setSelectedId(null); setFocusId(null); setQuery(""); }}>Reset view</button></div>
            </div>

            <div className="rl-architecture-grid">
              <ArchitectureScene nodes={filtered} edges={edges} modules={modules} selected={visibleSelectedId} focus={visibleFocusId} onSelect={(node) => setSelectedId(node.id)} />
              <Inspector node={selectedNode} module={selectedModule} connected={connected} />
            </div>
            <div className="rl-proofline"><span>REAL GRAPH</span><span>SELECT ≠ FOCUS</span><span>IMPACT IS LOCAL</span><strong>SOURCE-DERIVED ONLY</strong></div>
          </div>
        </section>
      </div>
    </main>
  );
}
