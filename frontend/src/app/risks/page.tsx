"use client";

import { useEffect, useMemo, useState, type CSSProperties } from "react";
import RepoLensSidebar from "@/components/RepoLensSidebar";
import {
  getRepositoryAnalysis,
  type RepositoryAnalysis,
  type RiskSignal,
} from "@/lib/api";

function normalizeSeverity(value?: string) {
  const severity = String(value ?? "").toUpperCase();

  if (severity.includes("CRITICAL")) return "CRITICAL";
  if (severity.includes("HIGH")) return "HIGH";
  if (severity.includes("MEDIUM") || severity.includes("MODERATE")) {
    return "MEDIUM";
  }

  return "LOW";
}

function formatLabel(value?: string) {
  if (!value) return "Unknown";

  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function getRiskSignals(
  analysis: RepositoryAnalysis | null,
): RiskSignal[] {
  if (!analysis) return [];

  if (Array.isArray(analysis.risks?.risk_signals)) {
    return analysis.risks.risk_signals;
  }

  if (Array.isArray(analysis.risk_signals)) {
    return analysis.risk_signals;
  }

  return [];
}

function severityRank(value?: string) {
  const severity = normalizeSeverity(value);

  if (severity === "CRITICAL") return 4;
  if (severity === "HIGH") return 3;
  if (severity === "MEDIUM") return 2;

  return 1;
}

function asRecord(
  value: unknown,
): Record<string, unknown> | null {
  if (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  ) {
    return value as Record<string, unknown>;
  }

  return null;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];

  return value.filter(
    (item): item is string =>
      typeof item === "string" && item.trim().length > 0,
  );
}

function getRiskField(
  risk: RiskSignal,
  key: string,
): unknown {
  return risk[key];
}

function getEvidenceRecord(
  risk: RiskSignal,
): Record<string, unknown> | null {
  return asRecord(getRiskField(risk, "evidence"));
}

function getCycle(risk: RiskSignal): string[] {
  const directCycle = asStringArray(
    getRiskField(risk, "cycle"),
  );

  if (directCycle.length > 0) {
    return directCycle;
  }

  const evidence = getEvidenceRecord(risk);

  return asStringArray(evidence?.nodes);
}

export default function RisksPage() {
  const [analysis, setAnalysis] =
    useState<RepositoryAnalysis | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadToken, setReloadToken] = useState(0);
  const [selectedRiskIndex, setSelectedRiskIndex] = useState(0);

  useEffect(() => {
    let active = true;

    async function loadRisks() {
      try {
        setLoading(true);
        setError("");

        const data = await getRepositoryAnalysis();

        if (!active) return;

        setAnalysis(data);
      } catch (requestError) {
        if (!active) return;

        console.error(
          "RepoLens risk analysis error:",
          requestError,
        );

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load risk analysis.",
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadRisks();

    return () => {
      active = false;
    };
  }, [reloadToken]);

  const risks = useMemo(() => {
    return [...getRiskSignals(analysis)].sort(
      (a, b) =>
        severityRank(b.severity) -
        severityRank(a.severity),
    );
  }, [analysis]);

  const counts = useMemo<{
  critical: number;
  high: number;
  medium: number;
  low: number;
}>(() => {
  const result = {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  };

  for (const risk of risks) {
    const severity = normalizeSeverity(risk.severity);

    if (severity === "CRITICAL") {
      result.critical += 1;
    } else if (severity === "HIGH") {
      result.high += 1;
    } else if (severity === "MEDIUM") {
      result.medium += 1;
    } else {
      result.low += 1;
    }
  }

  return result;
}, [risks]);

  const categories = useMemo(() => {
    const values = new Map<string, number>();

    for (const risk of risks) {
      const category = risk.category || "unknown";

      values.set(
        category,
        (values.get(category) ?? 0) + 1,
      );
    }

    return [...values.entries()].sort(
      (a, b) => b[1] - a[1],
    );
  }, [risks]);

  return (
    <main className="min-h-screen repolens-page repolens-route-risks bg-[#050505] text-white">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <RepoLensSidebar />

        <section className="min-w-0 flex-1">
          <Topbar
            loading={loading}
            repositoryName={
              typeof analysis?.metadata?.repository_name === "string"
                ? analysis.metadata.repository_name
                : "Repository"
            }
            onRefresh={() => setReloadToken((value) => value + 1)}
          />

          <div className="mx-auto max-w-[1500px] px-6 pb-16 pt-10 lg:px-8">
            {loading && (
              <div className="mb-6 rounded-2xl border border-white/10 bg-white/[0.025] px-5 py-4 text-sm text-white/50">
                Loading deterministic risk analysis…
              </div>
            )}

            {error && (
              <div className="mb-6 rounded-2xl border border-red-500/20 bg-red-500/[0.05] px-5 py-4">
                <div className="text-sm font-medium text-red-300">
                  Risk analysis could not be loaded.
                </div>

                <div className="mt-1 text-xs text-red-200/50">
                  {error}
                </div>
              </div>
            )}

            <header>
              <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-white/35">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                Risk intelligence
              </div>

              <div className="mt-5 flex flex-col justify-between gap-6 xl:flex-row xl:items-end">
                <div>
                  <h1 className="text-[44px] font-semibold leading-none tracking-[-0.045em] sm:text-[58px]">
                    Structural risks.
                    <br />
                    <span className="text-white/30">
                      Backed by evidence.
                    </span>
                  </h1>

                  <p className="mt-6 max-w-2xl text-sm leading-6 text-white/40">
                    RepoLens identifies deterministic structural
                    signals from repository analysis and keeps each
                    finding tied to the underlying codebase evidence.
                  </p>
                </div>

                <div className="rounded-xl border border-white/10 bg-white/[0.025] px-5 py-4 xl:min-w-[190px]">
                  <div className="text-[9px] uppercase tracking-[0.18em] text-white/25">
                    Total signals
                  </div>

                  <div className="mt-2 text-3xl font-semibold tracking-[-0.04em]">
                    {risks.length}
                  </div>

                  <div className="mt-1 text-[10px] text-white/30">
                    deterministic findings
                  </div>
                </div>
              </div>
            </header>

            <section className="mt-10 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <SeverityCard label="Critical" value={counts.critical} tone="critical" />
              <SeverityCard label="High" value={counts.high} tone="high" />
              <SeverityCard label="Medium" value={counts.medium} tone="medium" />
              <SeverityCard label="Low" value={counts.low} tone="low" />
            </section>

            <section className="rl-risk-console mt-6">
              <div className="rl-risk-console-head">
                <div>
                  <span className="rl-kicker">INVESTIGATION CONSOLE</span>
                  <h2>Inspect the signal, then trace the evidence.</h2>
                </div>
                <div className="rl-risk-console-meta">
                  <span>{risks.length} signals</span>
                  <span>deterministic ordering</span>
                </div>
              </div>

              {risks.length === 0 ? (
                <EmptyState />
              ) : (
                <div className="rl-risk-console-grid">
                  <div className="rl-risk-rail" aria-label="Risk findings">
                    {risks.map((risk, index) => (
                      <RiskListItem
                        key={`${risk.signal}-${risk.file}-${index}`}
                        risk={risk}
                        index={index}
                        selected={index === Math.min(selectedRiskIndex, risks.length - 1)}
                        onSelect={() => setSelectedRiskIndex(index)}
                      />
                    ))}
                  </div>

                  <RiskInvestigation
                    risk={risks[Math.min(selectedRiskIndex, Math.max(risks.length - 1, 0))] ?? null}
                    index={Math.min(selectedRiskIndex, Math.max(risks.length - 1, 0))}
                  />
                </div>
              )}
            </section>

            <section className="mt-6 grid gap-6 lg:grid-cols-[1fr_1fr]">
              <CategoryBreakdown categories={categories} />
              <EvidencePrinciples />
            </section>
          </div>
        </section>
      </div>
    </main>
  );
}

function Topbar({
  loading,
  repositoryName,
  onRefresh,
}: {
  loading: boolean;
  repositoryName: string;
  onRefresh: () => void;
}) {
  return (
    <header className="flex h-[66px] items-center justify-between border-b border-white/[0.07] px-5 lg:px-8">
      <div>
        <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
          Repository
        </div>

        <div className="mt-0.5 flex items-center gap-2 text-xs font-medium">
          {repositoryName}
          <span className="rounded border border-white/10 px-1.5 py-0.5 text-[9px] text-white/35">
            analyzed
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/[0.025] px-3 py-2 text-[10px] text-white/55 sm:flex">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          Analysis ready
        </div>

        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-[11px] font-medium text-white/75 transition hover:bg-white/[0.08] disabled:cursor-wait disabled:opacity-50"
        >
          {loading ? "Refreshing…" : "Refresh analysis"}
        </button>

        <div className="grid h-8 w-8 place-items-center rounded-full border border-white/10 bg-white/[0.04] text-[10px] text-white/50">
          R
        </div>
      </div>
    </header>
  );
}

function SeverityCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "critical" | "high" | "medium" | "low";
}) {
  const classes = {
    critical:
      "border-red-400/20 bg-red-400/[0.045] text-red-300",
    high:
      "border-orange-400/15 bg-orange-400/[0.035] text-orange-300",
    medium:
      "border-amber-400/15 bg-amber-400/[0.035] text-amber-300",
    low:
      "border-white/[0.08] bg-white/[0.025] text-white/45",
  };

  return (
    <div
      className={`rounded-xl border p-5 ${classes[tone]}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-[0.16em]">
          {label}
        </span>

        <span className="h-1.5 w-1.5 rounded-full bg-current opacity-70" />
      </div>

      <div className="mt-6 text-3xl font-semibold tracking-[-0.04em] text-white">
        {value}
      </div>

      <div className="mt-1 text-[9px] text-white/25">
        findings
      </div>
    </div>
  );
}

function RiskListItem({
  risk,
  index,
  selected,
  onSelect,
}: {
  risk: RiskSignal;
  index: number;
  selected: boolean;
  onSelect: () => void;
}) {
  const severity = normalizeSeverity(risk.severity);
  const accent =
    severity === "CRITICAL" ? "#fb7185" :
    severity === "HIGH" ? "#fb923c" :
    severity === "MEDIUM" ? "#f5c76a" : "#8f9aaa";

  return (
    <button
      type="button"
      onClick={onSelect}
      className={`rl-risk-list-button ${selected ? "is-selected" : ""}`}
      style={{ "--risk-accent": accent } as CSSProperties}
      aria-pressed={selected}
    >
      <span className="rl-risk-list-index">{String(index + 1).padStart(2, "0")}</span>
      <span className="rl-risk-list-copy">
        <strong>{formatLabel(risk.signal)}</strong>
        <small>{risk.file || "Repository-level finding"}</small>
      </span>
      <span className="rl-risk-list-severity">{severity}</span>
      <span className="rl-risk-list-arrow">→</span>
    </button>
  );
}

function RiskInvestigation({ risk, index }: { risk: RiskSignal | null; index: number }) {
  if (!risk) return null;
  const severity = normalizeSeverity(risk.severity);
  const evidence = getEvidenceRecord(risk);
  const accent =
    severity === "CRITICAL" ? "#fb7185" :
    severity === "HIGH" ? "#fb923c" :
    severity === "MEDIUM" ? "#f5c76a" : "#8f9aaa";

  return (
    <article className="rl-risk-investigation" style={{ "--risk-accent": accent } as CSSProperties}>
      <div className="rl-risk-investigation-glow" />
      <div className="rl-risk-investigation-head">
        <div>
          <span className="rl-kicker">SIGNAL {String(index + 1).padStart(2, "0")}</span>
          <h3>{formatLabel(risk.signal)}</h3>
          <code>{risk.file || "Repository-level finding"}</code>
        </div>
        <span className="rl-risk-investigation-badge">{severity}</span>
      </div>

      <div className="rl-risk-fact-strip">
        <div><span>Category</span><strong>{formatLabel(risk.category)}</strong></div>
        <div><span>Signal</span><strong>{formatLabel(risk.signal)}</strong></div>
        <div><span>Evidence</span><strong>{evidence ? "Available" : "Not returned"}</strong></div>
      </div>

      <div className="rl-risk-why">
        <span className="rl-kicker">WHY REPO LENS FLAGGED IT</span>
        <p>{risk.reason || "The deterministic analyzer recorded this signal, but no explanatory reason was returned."}</p>
      </div>

      {evidence ? (
        <div className="rl-risk-evidence-panel">
          <div className="rl-risk-evidence-head">
            <div><span className="rl-kicker">SOURCE EVIDENCE</span><strong>Observed repository facts</strong></div>
            <span>traceable</span>
          </div>
          <EvidenceBlock risk={risk} evidence={evidence} />
        </div>
      ) : (
        <div className="rl-risk-no-evidence">No structured evidence was returned for this finding. RepoLens does not invent supporting facts.</div>
      )}
    </article>
  );
}

function EvidenceBlock({
  risk,
  evidence,
}: {
  risk: RiskSignal;
  evidence: Record<string, unknown>;
}) {
  const signal = String(risk.signal ?? "");

  if (signal === "high_connectivity") {
    return (
      <HighConnectivityEvidence
        risk={risk}
        evidence={evidence}
      />
    );
  }

  if (signal === "circular_dependency") {
    return (
      <CircularDependencyEvidence
        risk={risk}
        evidence={evidence}
      />
    );
  }

  return (
    <GenericEvidence
      evidence={evidence}
    />
  );
}

function HighConnectivityEvidence({
  risk,
  evidence,
}: {
  risk: RiskSignal;
  evidence: Record<string, unknown>;
}) {
  const incoming = asStringArray(
    evidence.incoming_dependencies,
  );

  const outgoing = asStringArray(
    evidence.outgoing_dependencies,
  );

  const incomingCount =
    typeof evidence.incoming_count === "number"
      ? evidence.incoming_count
      : 0;

  const outgoingCount =
    typeof evidence.outgoing_count === "number"
      ? evidence.outgoing_count
      : 0;

  const totalConnections =
    typeof evidence.total_connections === "number"
      ? evidence.total_connections
      : typeof evidence.connection_count === "number"
        ? evidence.connection_count
        : 0;

  return (
    <details className="group mt-4 overflow-hidden rounded-xl border border-emerald-400/10 bg-emerald-400/[0.025]">
      <summary className="cursor-pointer list-none px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-emerald-300/70">
              ▸
            </span>

            <span className="text-[9px] font-medium uppercase tracking-[0.15em] text-emerald-300/70">
              View dependency evidence
            </span>
          </div>

          <span className="text-[9px] text-white/25">
            {totalConnections} connections
          </span>
        </div>
      </summary>

      <div className="border-t border-emerald-400/10 p-4">
        <div className="grid gap-3 sm:grid-cols-3">
          <EvidenceMetric
            label="Incoming"
            value={incomingCount}
          />

          <EvidenceMetric
            label="Outgoing"
            value={outgoingCount}
          />

          <EvidenceMetric
            label="Total"
            value={totalConnections}
          />
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <DependencyList
            title="Incoming dependencies"
            items={incoming}
          />

          <DependencyList
            title="Outgoing dependencies"
            items={outgoing}
          />
        </div>

        <div className="mt-4 rounded-lg border border-white/[0.06] bg-black/20 px-3 py-2.5">
          <div className="text-[8px] uppercase tracking-[0.15em] text-white/20">
            Evidence file
          </div>

          <div className="mt-1 break-all font-mono text-[10px] text-white/45">
            {String(
              evidence.file ??
                risk.file ??
                "Unknown file",
            )}
          </div>
        </div>
      </div>
    </details>
  );
}

function CircularDependencyEvidence({
  risk,
  evidence,
}: {
  risk: RiskSignal;
  evidence: Record<string, unknown>;
}) {
  const cycle = getCycle(risk);

  const edges = Array.isArray(evidence.edges)
    ? evidence.edges
    : [];

  return (
    <details
      open
      className="group mt-4 overflow-hidden rounded-xl border border-red-400/10 bg-red-400/[0.025]"
    >
      <summary className="cursor-pointer list-none px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-red-300/70">
              ▾
            </span>

            <span className="text-[9px] font-medium uppercase tracking-[0.15em] text-red-300/70">
              Dependency cycle evidence
            </span>
          </div>

          <span className="text-[9px] text-white/25">
            {cycle.length} modules
          </span>
        </div>
      </summary>

      <div className="border-t border-red-400/10 p-4">
        {cycle.length > 0 ? (
          <>
            <div className="text-[8px] uppercase tracking-[0.16em] text-white/20">
              Detected cycle
            </div>

            <div className="mt-3 space-y-2">
              {cycle.map((node, index) => {
                const nextNode =
                  cycle[(index + 1) % cycle.length];

                return (
                  <div
                    key={`${node}-${index}`}
                    className="flex flex-col gap-2"
                  >
                    <div className="rounded-lg border border-white/[0.07] bg-black/20 px-3 py-2.5">
                      <div className="font-mono text-[10px] text-white/55">
                        {node}
                      </div>
                    </div>

                    <div className="pl-4 text-[10px] text-red-300/40">
                      ↓
                    </div>

                    {index === cycle.length - 1 && (
                      <div className="rounded-lg border border-red-400/10 bg-red-400/[0.035] px-3 py-2.5">
                        <div className="font-mono text-[10px] text-red-200/55">
                          {nextNode}
                        </div>

                        <div className="mt-1 text-[8px] uppercase tracking-[0.13em] text-red-300/40">
                          cycle closes here
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </>
        ) : (
          <div className="text-[10px] text-white/30">
            Cycle nodes are not available in the current evidence.
          </div>
        )}

        {edges.length > 0 && (
          <div className="mt-5">
            <div className="text-[8px] uppercase tracking-[0.16em] text-white/20">
              Recorded edges
            </div>

            <div className="mt-2 space-y-2">
              {edges.map((edge, index) => (
                <div
                  key={index}
                  className="rounded-lg border border-white/[0.06] bg-black/20 px-3 py-2 font-mono text-[9px] text-white/35"
                >
                  {formatEvidenceValue(edge)}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </details>
  );
}

function GenericEvidence({
  evidence,
}: {
  evidence: Record<string, unknown>;
}) {
  const entries = Object.entries(evidence);

  return (
    <details className="mt-4 overflow-hidden rounded-xl border border-emerald-400/10 bg-emerald-400/[0.025]">
      <summary className="cursor-pointer list-none px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-emerald-300/70">
            ▸
          </span>

          <span className="text-[9px] font-medium uppercase tracking-[0.15em] text-emerald-300/70">
            View evidence
          </span>
        </div>
      </summary>

      <div className="border-t border-emerald-400/10 p-4">
        <div className="space-y-2">
          {entries.map(([key, value]) => (
            <div
              key={key}
              className="grid gap-2 rounded-lg border border-white/[0.06] bg-black/20 px-3 py-3 sm:grid-cols-[180px_1fr]"
            >
              <div className="text-[8px] uppercase tracking-[0.14em] text-white/20">
                {formatLabel(key)}
              </div>

              <div className="break-all font-mono text-[9px] leading-5 text-white/40">
                {formatEvidenceValue(value)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </details>
  );
}

function EvidenceMetric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-lg border border-white/[0.06] bg-black/20 px-3 py-3">
      <div className="text-[8px] uppercase tracking-[0.14em] text-white/20">
        {label}
      </div>

      <div className="mt-1 text-lg font-semibold text-white/70">
        {value}
      </div>
    </div>
  );
}

function DependencyList({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  return (
    <div className="rounded-lg border border-white/[0.06] bg-black/20 p-3">
      <div className="text-[8px] uppercase tracking-[0.14em] text-white/20">
        {title}
      </div>

      {items.length === 0 ? (
        <div className="mt-3 text-[9px] text-white/25">
          No dependency names supplied.
        </div>
      ) : (
        <div className="mt-3 max-h-44 space-y-1.5 overflow-auto">
          {items.map((item, index) => (
            <div
              key={`${item}-${index}`}
              className="rounded-md border border-white/[0.05] bg-white/[0.018] px-2.5 py-2 font-mono text-[9px] text-white/40"
            >
              {item}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function formatEvidenceValue(
  value: unknown,
): string {
  if (typeof value === "string") {
    return value;
  }

  if (
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }

  if (value === null) {
    return "null";
  }

  try {
    return JSON.stringify(value);
  } catch {
    return "Evidence data available";
  }
}

function CategoryBreakdown({
  categories,
}: {
  categories: [string, number][];
}) {
  const maxCount =
    categories.length > 0
      ? Math.max(
          ...categories.map((item) => item[1]),
        )
      : 1;

  return (
    <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.02]">
      <div className="border-b border-white/[0.07] px-5 py-4">
        <div className="text-sm font-medium">
          Risk categories
        </div>

        <div className="mt-1 text-[10px] text-white/30">
          Distribution of detected signals
        </div>
      </div>

      <div className="p-5">
        {categories.length === 0 ? (
          <div className="text-sm text-white/30">
            No category data available.
          </div>
        ) : (
          <div className="space-y-4">
            {categories.map(([category, count]) => (
              <div key={category}>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-white/45">
                    {formatLabel(category)}
                  </span>

                  <span className="text-[10px] text-white/30">
                    {count}
                  </span>
                </div>

                <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/[0.06]">
                  <div
                    className="h-full rounded-full bg-white/45"
                    style={{
                      width: `${Math.max(
                        8,
                        (count / maxCount) * 100,
                      )}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function EvidencePrinciples() {
  return (
    <div className="rounded-2xl border border-emerald-400/10 bg-emerald-400/[0.025] p-5">
      <div className="flex items-center gap-2">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />

        <span className="text-[10px] font-medium uppercase tracking-[0.16em] text-emerald-300/75">
          Evidence-first
        </span>
      </div>

      <div className="mt-4 text-sm font-medium text-white/70">
        Findings are signals, not guesses.
      </div>

      <p className="mt-3 text-[10px] leading-5 text-white/35">
        Deterministic analyzers produce repository facts first.
        AI reasoning can later interpret those facts, but
        unsupported conclusions should remain uncertain rather
        than becoming repository truth.
      </p>

      <div className="mt-5 space-y-2 text-[9px] text-white/30">
        <div>FACT — directly observed structure</div>
        <div>INFERENCE — derived from observed evidence</div>
        <div>POSSIBLE RISK — requires interpretation</div>
        <div>UNKNOWN — evidence is insufficient</div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="p-10 text-center">
      <div className="mx-auto grid h-10 w-10 place-items-center rounded-full border border-emerald-400/15 bg-emerald-400/[0.04] text-emerald-300/70">
        ✓
      </div>

      <div className="mt-4 text-sm font-medium text-white/60">
        No risk signals detected
      </div>

      <div className="mx-auto mt-2 max-w-sm text-[10px] leading-5 text-white/30">
        The current deterministic analysis did not return any
        risk findings.
      </div>
    </div>
  );
}