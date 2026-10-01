"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import RepoLensSidebar from "@/components/RepoLensSidebar";
import {
  getRepositoryAnalysis,
  getRepositoryOverview,
  type RepositoryAnalysis,
  type RepositoryOverview,
  type RiskSignal,
} from "@/lib/api";

function normalizeSeverity(value?: string) {
  const severity = String(value ?? "").toUpperCase();
  if (severity.includes("HIGH") || severity.includes("CRITICAL")) return "HIGH";
  if (severity.includes("MEDIUM") || severity.includes("MODERATE")) return "MEDIUM";
  return "LOW";
}

function getRiskSignals(analysis: RepositoryAnalysis | null): RiskSignal[] {
  if (!analysis) return [];
  if (Array.isArray(analysis.risks?.risk_signals)) return analysis.risks.risk_signals;
  if (Array.isArray(analysis.risk_signals)) return analysis.risk_signals;
  return [];
}

const featureCards = [
  {
    href: "/architecture",
    index: "01",
    kicker: "MAP THE SYSTEM",
    title: "Architecture",
    text: "See the production modules and the relationships that shape the codebase.",
    className: "rl-feature-architecture",
  },
  {
    href: "/dependencies",
    index: "02",
    kicker: "TRACE IMPACT",
    title: "Dependencies",
    text: "Follow incoming and outgoing paths before a change creates a wider blast radius.",
    className: "rl-feature-dependencies",
  },
  {
    href: "/evidence",
    index: "03",
    kicker: "PROVE THE CLAIM",
    title: "Evidence",
    text: "Move from a conclusion to the repository facts that support it.",
    className: "rl-feature-evidence",
  },
  {
    href: "/risks",
    index: "04",
    kicker: "SURFACE SIGNALS",
    title: "Risks",
    text: "Inspect deterministic structural signals instead of guessing at vulnerabilities.",
    className: "rl-feature-risks",
  },
];

export default function Home() {
  const [overview, setOverview] = useState<RepositoryOverview | null>(null);
  const [analysis, setAnalysis] = useState<RepositoryAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let active = true;
    async function loadDashboard() {
      try {
        setLoading(true);
        setError("");
        const [overviewData, analysisData] = await Promise.all([
          getRepositoryOverview(),
          getRepositoryAnalysis(),
        ]);
        if (!active) return;
        setOverview(overviewData);
        setAnalysis(analysisData);
      } catch (requestError) {
        if (!active) return;
        console.error("RepoLens dashboard error:", requestError);
        setError(requestError instanceof Error ? requestError.message : "Unable to load repository analysis.");
      } finally {
        if (active) setLoading(false);
      }
    }
    loadDashboard();
    return () => { active = false; };
  }, [reloadToken]);

  const riskSignals = useMemo(() => getRiskSignals(analysis), [analysis]);
  const repositoryName = overview?.metadata.repository_name ?? "Repository";
  const totalFiles = overview?.metadata.total_files ?? 0;
  const pythonFiles = overview?.metadata.python_files ?? 0;
  const dependencyEdges = overview?.dependency_edge_count ?? 0;
  const architectureModules = overview?.production_module_count ?? 0;
  const architectureEdges = overview?.architecture.edge_count ?? 0;
  const riskCount = overview?.risk.signal_count ?? riskSignals.length;
  const highRisks = riskSignals.filter((risk) => normalizeSeverity(risk.severity) === "HIGH").length;

  return (
    <main className="min-h-screen repolens-page repolens-overview text-white">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <RepoLensSidebar />
        <section className="min-w-0 flex-1">
          <Topbar repositoryName={repositoryName} loading={loading} onRefresh={() => setReloadToken((value) => value + 1)} />
          <div className="mx-auto max-w-[1560px] px-4 pb-20 pt-4 sm:px-6 lg:px-8 lg:pt-6">
            {loading && <div className="rl-inline-status"><span /> Reconstructing repository intelligence…</div>}
            {error && (
              <div className="rl-error-banner">
                <strong>Repository analysis could not be loaded.</strong>
                <span>{error}</span>
              </div>
            )}

            <Hero
              repositoryName={repositoryName}
              totalFiles={totalFiles}
              dependencyEdges={dependencyEdges}
              architectureModules={architectureModules}
              architectureEdges={architectureEdges}
              riskCount={riskCount}
              highRisks={highRisks}
            />

            <SignalStrip
              totalFiles={totalFiles}
              pythonFiles={pythonFiles}
              dependencyEdges={dependencyEdges}
              architectureModules={architectureModules}
              architectureEdges={architectureEdges}
              riskCount={riskCount}
            />

            <section className="rl-intelligence-section">
              <div className="rl-section-heading">
                <div>
                  <span className="rl-overview-kicker">THE INTELLIGENCE LAYER</span>
                  <h2>Follow the signal.</h2>
                </div>
                <p>Every view answers a different engineering question. The data stays grounded in the same repository analysis.</p>
              </div>
              <div className="rl-feature-grid">
                {featureCards.map((card) => <FeatureCard key={card.href} {...card} />)}
              </div>
            </section>

            <section className="rl-proof-band">
              <div className="rl-proof-mark"><span>RL</span><i /></div>
              <div>
                <span className="rl-overview-kicker">EVIDENCE-FIRST</span>
                <strong>Deterministic analysis first. AI reasoning second.</strong>
              </div>
              <div className="rl-proof-points">
                <span>{architectureModules} modules mapped</span>
                <span>{architectureEdges} architecture relationships</span>
                <span>{riskCount} structural signals</span>
              </div>
              <Link href="/qa" className="rl-proof-action">Ask about this repository <span>↗</span></Link>
            </section>

            <footer className="rl-overview-footer">
              <span>RepoLens · Evidence-based codebase intelligence</span>
              <span>{pythonFiles} Python files · {dependencyEdges} dependency edges · analysis ready</span>
            </footer>
          </div>
        </section>
      </div>
    </main>
  );
}

function Topbar({ repositoryName, loading, onRefresh }: { repositoryName: string; loading: boolean; onRefresh: () => void }) {
  return (
    <header className="repolens-topbar flex h-[64px] items-center justify-between px-4 sm:px-6 lg:px-8">
      <div className="min-w-0">
        <div className="rl-topbar-kicker">REPOSITORY / INTELLIGENCE</div>
        <div className="mt-1 truncate text-xs font-medium text-white/80">psf / {repositoryName} <span className="rl-branch">main</span></div>
      </div>
      <div className="flex items-center gap-2">
        <div className="rl-ready"><span /> {loading ? "Updating" : "Analysis ready"}</div>
        <button type="button" onClick={onRefresh} disabled={loading} className="repolens-topbar-button">{loading ? "Updating…" : "Refresh analysis"}</button>
      </div>
    </header>
  );
}

function Hero({ repositoryName, totalFiles, dependencyEdges, architectureModules, architectureEdges, riskCount, highRisks }: {
  repositoryName: string;
  totalFiles: number;
  dependencyEdges: number;
  architectureModules: number;
  architectureEdges: number;
  riskCount: number;
  highRisks: number;
}) {
  return (
    <section className="rl-flagship-hero">
      <div className="rl-hero-noise" aria-hidden="true" />
      <div className="rl-hero-gridline" aria-hidden="true" />
      <div className="rl-hero-corner" aria-hidden="true" />

      <div className="rl-hero-copy">
        <div className="rl-hero-kicker"><span className="rl-live-dot" /> CODEBASE INTELLIGENCE <b>01</b></div>
        <h1>See the system.<br /><em>Not just the code.</em></h1>
        <p>RepoLens reconstructs the architecture behind a repository, traces dependency impact, surfaces structural risk, and connects conclusions back to concrete evidence.</p>
        <div className="rl-hero-actions">
          <Link href="/architecture" className="rl-primary-action">Open architecture <span>↗</span></Link>
          <Link href="/qa" className="rl-secondary-action">Ask RepoLens <kbd>⌘ K</kbd></Link>
        </div>
        <div className="rl-hero-meta">
          <span>{repositoryName}</span>
          <i />
          <span>{totalFiles.toLocaleString()} files analyzed</span>
          <i />
          <span>{dependencyEdges} dependency edges</span>
        </div>
      </div>

      <div className="rl-system-stage" aria-label="Repository intelligence signal field">
        <div className="rl-stage-grid" />
        <div className="rl-stage-scan" />
        <div className="rl-stage-orbit orbit-a" />
        <div className="rl-stage-orbit orbit-b" />
        <div className="rl-stage-orbit orbit-c" />
        <div className="rl-stage-axis axis-x" />
        <div className="rl-stage-axis axis-y" />
        <div className="rl-stage-core">
          <span>RL</span>
          <small>REPOSITORY</small>
          <i />
        </div>
        <StageSatellite className="sat-files" label="FILES" value={totalFiles.toLocaleString()} note={`${architectureModules} modules`} />
        <StageSatellite className="sat-deps" label="DEPENDENCY GRAPH" value={dependencyEdges.toLocaleString()} note="internal edges" />
        <StageSatellite className="sat-arch" label="ARCHITECTURE" value={architectureModules.toLocaleString()} note={`${architectureEdges} relations`} />
        <StageSatellite className="sat-risk" label="RISK SIGNALS" value={riskCount.toLocaleString()} note={highRisks ? `${highRisks} high attention` : "deterministic"} warning={highRisks > 0} />
        <div className="rl-stage-readout readout-top"><span>MODEL STATE</span><strong>GROUNDED</strong></div>
        <div className="rl-stage-readout readout-bottom"><span>TRACE MODE</span><strong>DETERMINISTIC</strong></div>
      </div>
    </section>
  );
}

function StageSatellite({ className, label, value, note, warning = false }: { className: string; label: string; value: string; note: string; warning?: boolean }) {
  return (
    <div className={`rl-stage-satellite ${className}`}>
      <span className="sat-dot" data-warning={warning} />
      <div><small>{label}</small><strong>{value}</strong><em>{note}</em></div>
    </div>
  );
}

function SignalStrip({ totalFiles, pythonFiles, dependencyEdges, architectureModules, architectureEdges, riskCount }: {
  totalFiles: number;
  pythonFiles: number;
  dependencyEdges: number;
  architectureModules: number;
  architectureEdges: number;
  riskCount: number;
}) {
  const metrics = [
    ["FILES", totalFiles, `${pythonFiles} Python`, "01"],
    ["DEPENDENCIES", dependencyEdges, "internal edges", "02"],
    ["MODULES", architectureModules, `${architectureEdges} graph relations`, "03"],
    ["RISK SIGNALS", riskCount, "evidence-backed", "04"],
  ];
  return (
    <section className="rl-signal-strip">
      {metrics.map(([label, value, detail, index]) => (
        <div key={String(label)} className="rl-strip-item">
          <span>{index}</span>
          <div><small>{label}</small><strong>{Number(value).toLocaleString()}</strong><em>{detail}</em></div>
        </div>
      ))}
    </section>
  );
}

function FeatureCard({ href, index, kicker, title, text, className }: { href: string; index: string; kicker: string; title: string; text: string; className: string }) {
  return (
    <Link href={href} className={`rl-feature-card ${className}`}>
      <div className="rl-feature-top"><span>{index}</span><small>{kicker}</small><b>↗</b></div>
      <div className="rl-feature-copy"><h3>{title}</h3><p>{text}</p></div>
      <FeatureVisual type={className} />
    </Link>
  );
}

function FeatureVisual({ type }: { type: string }) {
  if (type.includes("architecture")) {
    return <div className="rl-mini-visual mini-map" aria-hidden="true"><i /><i /><i /><i /><i /><span /><span /></div>;
  }
  if (type.includes("dependencies")) {
    return <div className="rl-mini-visual mini-chain" aria-hidden="true"><i /><i /><i /><i /><b /><b /><b /></div>;
  }
  if (type.includes("evidence")) {
    return <div className="rl-mini-visual mini-evidence" aria-hidden="true"><i /><i /><i /><span /><span /><span /></div>;
  }
  return <div className="rl-mini-visual mini-risk" aria-hidden="true"><i /><i /><i /><i /><b /></div>;
}
