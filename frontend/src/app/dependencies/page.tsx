"use client";

import { useEffect, useMemo, useState } from "react";
import RepoLensSidebar from "@/components/RepoLensSidebar";

import {
  getRepositoryAnalysis,
  type RepositoryAnalysis,
} from "@/lib/api";

type DependencyEdge = {
  source: string;
  target: string;
  import?: string;
};

type DependencySummary = {
  edge_count?: number;
  node_count?: number;
  unresolved_count?: number;
  outgoing_file_count?: number;
  incoming_file_count?: number;
  [key: string]: unknown;
};

type DependencyGraph = {
  edges?: DependencyEdge[];
  summary?: DependencySummary;
};

type DependencyAnalysis = RepositoryAnalysis & {
  dependency_graph?: DependencyGraph;
};

type ModuleStats = {
  incoming: number;
  outgoing: number;
  total: number;
};

function normalizePath(value: string): string {
  return value.replaceAll("\\", "/");
}

function shortPath(value: string, max = 42): string {
  const normalized = normalizePath(value);

  if (normalized.length <= max) {
    return normalized;
  }

  return `…${normalized.slice(-(max - 1))}`;
}

function moduleNameFromPath(path: string): string {
  const normalized = normalizePath(path)
    .replace(/^\.\//, "")
    .replace(/\.py$/, "");

  const sourceMarker = normalized.indexOf("src/");
  const modulePath =
    sourceMarker >= 0
      ? normalized.slice(sourceMarker + 4)
      : normalized;

  const segments = modulePath
    .split("/")
    .filter(Boolean)
    .filter((segment) => segment !== "__pycache__");

  if (segments.length === 0) {
    return normalized || "unknown";
  }

  if (segments[segments.length - 1] === "__init__") {
    segments.pop();
  }

  return segments.length > 0
    ? segments.join(".")
    : normalized;
}

function buildModuleStats(
  edges: DependencyEdge[],
): Map<string, ModuleStats> {
  const stats = new Map<string, ModuleStats>();

  function ensure(path: string) {
    if (!stats.has(path)) {
      stats.set(path, {
        incoming: 0,
        outgoing: 0,
        total: 0,
      });
    }

    return stats.get(path)!;
  }

  for (const edge of edges) {
    const source = ensure(edge.source);
    const target = ensure(edge.target);

    source.outgoing += 1;
    target.incoming += 1;

    source.total += 1;
    target.total += 1;
  }

  return stats;
}

function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-6">
      <div className="text-[11px] uppercase tracking-[0.18em] text-white/35">
        {label}
      </div>

      <div className="mt-5 flex items-end justify-between gap-4">
        <div className="text-4xl font-semibold tracking-tight text-white">
          {value}
        </div>

        <div className="pb-1 text-[11px] text-white/30">
          {hint}
        </div>
      </div>
    </div>
  );
}

function ModuleRow({
  module,
  stats,
  selected,
  onClick,
}: {
  module: string;
  stats: ModuleStats;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`group w-full rounded-xl border p-4 text-left transition ${
        selected
          ? "border-white/25 bg-white/[0.08]"
          : "border-white/8 bg-white/[0.015] hover:border-white/15 hover:bg-white/[0.035]"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div
            className={`truncate font-mono text-sm ${
              selected
                ? "text-white"
                : "text-white/70 group-hover:text-white"
            }`}
          >
            {moduleNameFromPath(module)}
          </div>

          <div className="mt-1 truncate font-mono text-[10px] text-white/25">
            {normalizePath(module)}
          </div>
        </div>

        <div className="shrink-0 text-[10px] text-white/25">
          {stats.total} links
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2">
        <div className="rounded-lg border border-white/8 bg-black/20 px-3 py-2">
          <div className="text-[9px] uppercase tracking-widest text-white/25">
            Incoming
          </div>

          <div className="mt-1 text-sm text-white/70">
            {stats.incoming}
          </div>
        </div>

        <div className="rounded-lg border border-white/8 bg-black/20 px-3 py-2">
          <div className="text-[9px] uppercase tracking-widest text-white/25">
            Outgoing
          </div>

          <div className="mt-1 text-sm text-white/70">
            {stats.outgoing}
          </div>
        </div>
      </div>
    </button>
  );
}

function RelationshipRow({
  edge,
  direction,
  onSelectModule,
}: {
  edge: DependencyEdge;
  direction: "incoming" | "outgoing";
  onSelectModule: (module: string) => void;
}) {
  const otherModule =
    direction === "outgoing"
      ? edge.target
      : edge.source;

  return (
    <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <div className="text-[9px] uppercase tracking-[0.18em] text-white/25">
            {direction}
          </div>

          <button
            type="button"
            onClick={() => onSelectModule(otherModule)}
            className="mt-2 block max-w-full truncate text-left font-mono text-sm text-white/70 transition hover:text-white"
          >
            {moduleNameFromPath(otherModule)}
          </button>

          <div className="mt-1 truncate font-mono text-[10px] text-white/25">
            {shortPath(otherModule)}
          </div>
        </div>

        <div className="shrink-0 rounded-lg border border-white/10 px-3 py-2 font-mono text-[10px] text-white/45">
          {edge.import || "import"}
        </div>
      </div>
    </div>
  );
}

function SelectedModule({
  module,
  edges,
  stats,
  onSelectModule,
}: {
  module: string | null;
  edges: DependencyEdge[];
  stats: ModuleStats | null;
  onSelectModule: (module: string) => void;
}) {
  if (!module || !stats) {
    return (
      <div className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-6">
        <div className="text-sm font-medium text-white">
          Dependency inspection
        </div>

        <p className="mt-3 text-sm leading-6 text-white/35">
          Select a module to inspect its incoming and outgoing
          dependency relationships.
        </p>
      </div>
    );
  }

  const incoming = edges.filter(
    (edge) => edge.target === module,
  );

  const outgoing = edges.filter(
    (edge) => edge.source === module,
  );

  return (
    <div className="rounded-2xl border border-white/10 bg-[#0b0b0b]">
      <div className="border-b border-white/10 px-6 py-5">
        <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
          Selected module
        </div>

        <div className="mt-3 font-mono text-xl text-white">
          {moduleNameFromPath(module)}
        </div>

        <div className="mt-2 break-all font-mono text-xs text-white/30">
          {normalizePath(module)}
        </div>
      </div>

      <div className="grid grid-cols-3 divide-x divide-white/10 border-b border-white/10">
        <div className="p-5">
          <div className="text-[9px] uppercase tracking-widest text-white/25">
            Incoming
          </div>

          <div className="mt-2 text-2xl text-white">
            {stats.incoming}
          </div>
        </div>

        <div className="p-5">
          <div className="text-[9px] uppercase tracking-widest text-white/25">
            Outgoing
          </div>

          <div className="mt-2 text-2xl text-white">
            {stats.outgoing}
          </div>
        </div>

        <div className="p-5">
          <div className="text-[9px] uppercase tracking-widest text-white/25">
            Total
          </div>

          <div className="mt-2 text-2xl text-white">
            {stats.total}
          </div>
        </div>
      </div>

      <div className="grid gap-7 p-6 xl:grid-cols-2">
        <div>
          <div className="mb-3 text-[10px] uppercase tracking-[0.18em] text-white/30">
            Incoming dependencies
          </div>

          <div className="space-y-2">
            {incoming.length === 0 ? (
              <div className="rounded-xl border border-white/8 px-4 py-3 text-xs text-white/30">
                No incoming dependencies detected.
              </div>
            ) : (
              incoming.map((edge, index) => (
                <RelationshipRow
                  key={`${edge.source}-${edge.target}-${index}`}
                  edge={edge}
                  direction="incoming"
                  onSelectModule={onSelectModule}
                />
              ))
            )}
          </div>
        </div>

        <div>
          <div className="mb-3 text-[10px] uppercase tracking-[0.18em] text-white/30">
            Outgoing dependencies
          </div>

          <div className="space-y-2">
            {outgoing.length === 0 ? (
              <div className="rounded-xl border border-white/8 px-4 py-3 text-xs text-white/30">
                No outgoing dependencies detected.
              </div>
            ) : (
              outgoing.map((edge, index) => (
                <RelationshipRow
                  key={`${edge.source}-${edge.target}-${index}`}
                  edge={edge}
                  direction="outgoing"
                  onSelectModule={onSelectModule}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DependenciesPage() {
  const [analysis, setAnalysis] =
    useState<DependencyAnalysis | null>(null);

  const [selectedModule, setSelectedModule] =
    useState<string | null>(null);

  const [search, setSearch] = useState("");

  const [direction, setDirection] = useState<
    "all" | "incoming" | "outgoing"
  >("all");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        setLoading(true);
        setError(null);

        const result =
          (await getRepositoryAnalysis()) as DependencyAnalysis;

        if (!active) {
          return;
        }

        setAnalysis(result);
      } catch (err) {
        if (!active) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Failed to load dependency analysis.",
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      active = false;
    };
  }, []);

  const dependencyGraph =
    analysis?.dependency_graph ?? {};

  const edges = useMemo(
    () => dependencyGraph.edges ?? [],
    [dependencyGraph.edges],
  );

  const summary = dependencyGraph.summary ?? {};

  const moduleStats = useMemo(
    () => buildModuleStats(edges),
    [edges],
  );

  const modules = useMemo(() => {
    return Array.from(moduleStats.keys()).sort(
      (a, b) => {
        const statsA = moduleStats.get(a)!;
        const statsB = moduleStats.get(b)!;

        return (
          statsB.total - statsA.total ||
          a.localeCompare(b)
        );
      },
    );
  }, [moduleStats]);

  const filteredModules = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) {
      return modules;
    }

    return modules.filter((module) => {
      return (
        module.toLowerCase().includes(query) ||
        moduleNameFromPath(module)
          .toLowerCase()
          .includes(query)
      );
    });
  }, [modules, search]);

  const filteredEdges = useMemo(() => {
    const query = search.trim().toLowerCase();

    return edges.filter((edge) => {
      const matchesDirection =
        direction === "all" ||
        (direction === "incoming" &&
          edge.target === selectedModule) ||
        (direction === "outgoing" &&
          edge.source === selectedModule);

      if (!matchesDirection) {
        return false;
      }

      if (!query) {
        return true;
      }

      return (
        edge.source.toLowerCase().includes(query) ||
        edge.target.toLowerCase().includes(query) ||
        moduleNameFromPath(edge.source)
          .toLowerCase()
          .includes(query) ||
        moduleNameFromPath(edge.target)
          .toLowerCase()
          .includes(query) ||
        (edge.import ?? "")
          .toLowerCase()
          .includes(query)
      );
    });
  }, [edges, search, direction, selectedModule]);

  const selectedStats = selectedModule
    ? moduleStats.get(selectedModule) ?? null
    : null;

  const topModules = modules.slice(0, 8);

  if (loading) {
    return (
      <main className="min-h-screen repolens-page repolens-route-dependencies bg-[#050505] text-white">
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-sm text-white/40">
            Loading dependency intelligence…
          </div>
        </div>
      </main>
    );
  }

  if (error || !analysis) {
    return (
      <main className="min-h-screen repolens-page bg-[#050505] text-white">
        <div className="flex min-h-screen items-center justify-center p-8">
          <div className="max-w-lg rounded-2xl border border-red-400/20 bg-red-400/5 p-6">
            <div className="text-sm font-medium text-red-300">
              Dependency data unavailable
            </div>

            <p className="mt-3 text-sm leading-6 text-white/50">
              {error ??
                "Repository dependency data could not be loaded."}
            </p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen repolens-page bg-[#050505] text-white">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <RepoLensSidebar />

        <section className="min-w-0 flex-1">
          <header className="flex h-16 items-center justify-between border-b border-white/10 px-6 lg:px-10">
            <div className="text-xs text-white/30">
              Repository / Dependencies
            </div>

            <span className="rounded-full border border-white/10 px-3 py-1.5 text-[10px] uppercase tracking-widest text-white/35">
              Deterministic analysis
            </span>
          </header>

          <div className="mx-auto max-w-[1500px] px-6 py-10 lg:px-10">
            <div className="max-w-4xl">
              <div className="text-xs uppercase tracking-[0.2em] text-white/30">
                Dependency intelligence
              </div>

              <h1 className="mt-5 text-5xl font-semibold tracking-[-0.045em] text-white lg:text-7xl">
                See what depends
                <span className="block text-white/30">
                  on what.
                </span>
              </h1>

              <p className="mt-6 max-w-3xl text-base leading-7 text-white/40">
                RepoLens reconstructs module-to-module dependency
                relationships from the analyzed repository and
                preserves the import that created each relationship.
              </p>
            </div>

            <div className="mt-12 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                label="Dependency edges"
                value={
                  summary.edge_count ??
                  edges.length
                }
                hint="relationships"
              />

              <MetricCard
                label="Modules"
                value={
                  summary.node_count ??
                  moduleStats.size
                }
                hint="connected nodes"
              />

              <MetricCard
                label="Outgoing modules"
                value={
                  summary.outgoing_file_count ??
                  new Set(edges.map((edge) => edge.source)).size
                }
                hint="source files"
              />

              <MetricCard
                label="Incoming modules"
                value={
                  summary.incoming_file_count ??
                  new Set(edges.map((edge) => edge.target)).size
                }
                hint="target files"
              />
            </div>

            <div className="mt-7 rounded-2xl border border-white/10 bg-[#0b0b0b]">
              <div className="flex flex-col gap-4 border-b border-white/10 p-5 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <div className="text-sm font-medium text-white">
                    Dependency explorer
                  </div>

                  <div className="mt-1 text-xs text-white/35">
                    Search modules or imports, then inspect the
                    relationships behind them.
                  </div>
                </div>

                <div className="flex flex-col gap-2 sm:flex-row">
                  <input
                    value={search}
                    onChange={(event) =>
                      setSearch(event.target.value)
                    }
                    placeholder="Search module or import…"
                    className="h-10 w-full rounded-xl border border-white/10 bg-black/30 px-4 text-sm text-white outline-none placeholder:text-white/20 focus:border-white/25 sm:w-[280px]"
                  />

                  <select
                    value={direction}
                    onChange={(event) =>
                      setDirection(
                        event.target.value as
                          | "all"
                          | "incoming"
                          | "outgoing",
                      )
                    }
                    className="h-10 rounded-xl border border-white/10 bg-[#0b0b0b] px-3 text-xs text-white/60 outline-none focus:border-white/25"
                  >
                    <option value="all">
                      All relationships
                    </option>
                    <option value="incoming">
                      Incoming
                    </option>
                    <option value="outgoing">
                      Outgoing
                    </option>
                  </select>
                </div>
              </div>

              <div className="grid gap-6 p-5 xl:grid-cols-[0.8fr_1.2fr]">
                <div>
                  <div className="mb-3 flex items-center justify-between">
                    <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                      Modules
                    </div>

                    <div className="text-[10px] text-white/25">
                      {filteredModules.length} shown
                    </div>
                  </div>

                  <div className="max-h-[560px] space-y-2 overflow-y-auto pr-1">
                    {filteredModules.length === 0 ? (
                      <div className="rounded-xl border border-white/8 px-4 py-6 text-center text-xs text-white/30">
                        No modules match the current search.
                      </div>
                    ) : (
                      filteredModules.map((module) => (
                        <ModuleRow
                          key={module}
                          module={module}
                          stats={moduleStats.get(module)!}
                          selected={
                            selectedModule === module
                          }
                          onClick={() =>
                            setSelectedModule(module)
                          }
                        />
                      ))
                    )}
                  </div>
                </div>

                <div>
                  <div className="mb-3 flex items-center justify-between">
                    <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                      Relationships
                    </div>

                    <div className="text-[10px] text-white/25">
                      {filteredEdges.length} edges
                    </div>
                  </div>

                  <div className="max-h-[560px] space-y-2 overflow-y-auto pr-1">
                    {filteredEdges.length === 0 ? (
                      <div className="rounded-xl border border-white/8 px-4 py-6 text-center text-xs text-white/30">
                        No dependency relationships match the
                        current filters.
                      </div>
                    ) : (
                      filteredEdges.map((edge, index) => (
                        <button
                          type="button"
                          key={`${edge.source}-${edge.target}-${index}`}
                          onClick={() =>
                            setSelectedModule(edge.source)
                          }
                          className="w-full rounded-xl border border-white/8 bg-white/[0.015] p-4 text-left transition hover:border-white/18 hover:bg-white/[0.035]"
                        >
                          <div className="flex items-center gap-3">
                            <div className="min-w-0 flex-1">
                              <div className="truncate font-mono text-xs text-white/65">
                                {moduleNameFromPath(
                                  edge.source,
                                )}
                              </div>
                            </div>

                            <div className="text-white/25">
                              →
                            </div>

                            <div className="min-w-0 flex-1 text-right">
                              <div className="truncate font-mono text-xs text-white/65">
                                {moduleNameFromPath(
                                  edge.target,
                                )}
                              </div>
                            </div>
                          </div>

                          <div className="mt-3 flex items-center justify-between gap-3">
                            <span className="truncate font-mono text-[10px] text-white/25">
                              {edge.import
                                ? `import: ${edge.import}`
                                : "import relationship"}
                            </span>

                            <span className="shrink-0 rounded-md border border-white/8 px-2 py-1 text-[9px] uppercase tracking-widest text-white/25">
                              dependency
                            </span>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-7">
              <SelectedModule
                module={selectedModule}
                edges={edges}
                stats={selectedStats}
                onSelectModule={setSelectedModule}
              />
            </div>

            <div className="mt-7 grid gap-7 xl:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-[#0b0b0b]">
                <div className="border-b border-white/10 px-6 py-5">
                  <div className="text-sm font-medium text-white">
                    High-connectivity modules
                  </div>

                  <div className="mt-1 text-xs text-white/35">
                    Modules with the largest number of detected
                    dependency relationships.
                  </div>
                </div>

                <div className="divide-y divide-white/8">
                  {topModules.map((module, index) => {
                    const stats = moduleStats.get(module)!;

                    return (
                      <button
                        key={module}
                        type="button"
                        onClick={() =>
                          setSelectedModule(module)
                        }
                        className="flex w-full items-center gap-4 px-6 py-4 text-left transition hover:bg-white/[0.025]"
                      >
                        <span className="w-6 font-mono text-[10px] text-white/25">
                          {String(index + 1).padStart(2, "0")}
                        </span>

                        <span className="min-w-0 flex-1 truncate font-mono text-xs text-white/60">
                          {moduleNameFromPath(module)}
                        </span>

                        <span className="text-xs text-white/30">
                          {stats.total}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-6">
                <div className="text-sm font-medium text-white">
                  Evidence-first dependency analysis
                </div>

                <p className="mt-4 text-sm leading-7 text-white/40">
                  Every relationship shown in this page comes from
                  the reconstructed dependency graph. The import
                  name is preserved as supporting structural
                  evidence rather than inferred by the interface.
                </p>

                <div className="mt-6 grid gap-3">
                  <div className="rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3">
                    <div className="text-xs text-white/70">
                      {edges.length} concrete dependency edges
                    </div>

                    <div className="mt-1 text-[11px] text-white/30">
                      Directed relationships reconstructed from
                      source imports.
                    </div>
                  </div>

                  <div className="rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3">
                    <div className="text-xs text-white/70">
                      Import provenance preserved
                    </div>

                    <div className="mt-1 text-[11px] text-white/30">
                      Each edge can expose the import that created
                      the relationship.
                    </div>
                  </div>

                  <div className="rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3">
                    <div className="text-xs text-white/70">
                      No arbitrary dependency score
                    </div>

                    <div className="mt-1 text-[11px] text-white/30">
                      RepoLens presents structural facts instead of
                      inventing health scores.
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-10 border-t border-white/10 pt-6 text-xs text-white/25">
              RepoLens · Dependency relationships reconstructed from
              repository evidence · No arbitrary scoring
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}