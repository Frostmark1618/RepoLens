"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import RepoLensSidebar from "@/components/RepoLensSidebar";
import { getRepositoryAnalysis, type RepositoryAnalysis } from "@/lib/api";

export default function ReportsPage() {
  const [analysis, setAnalysis] = useState<RepositoryAnalysis | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    getRepositoryAnalysis()
      .then((value) => active && setAnalysis(value))
      .catch((err) => active && setError(err instanceof Error ? err.message : "Unable to load report."));
    return () => { active = false; };
  }, []);

  const metrics = useMemo(() => {
    const metadata = analysis?.metadata as Record<string, unknown> | undefined;
    const architecture = (analysis?.architecture ?? {}) as { production_modules?: unknown[]; graph_summary?: { edge_count?: number } };
    const dependencies = (analysis?.dependency_graph ?? {}) as { edges?: unknown[] };
    const risks = Array.isArray(analysis?.risks?.risk_signals) ? analysis.risks.risk_signals.length : 0;
    return [
      ["Files analyzed", Number(metadata?.total_files ?? 0), "repository surface"],
      ["Python files", Number(metadata?.python_files ?? 0), "detected source files"],
      ["Dependency edges", Array.isArray(dependencies.edges) ? dependencies.edges.length : 0, "import relationships"],
      ["Production modules", Array.isArray(architecture.production_modules) ? architecture.production_modules.length : 0, "architecture nodes"],
      ["Architecture edges", Number(architecture.graph_summary?.edge_count ?? 0), "module relationships"],
      ["Risk signals", risks, "persisted structural signals"],
    ] as const;
  }, [analysis]);

  return (
    <main className="min-h-screen repolens-page repolens-route-reports text-white">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <RepoLensSidebar />
        <section className="min-w-0 flex-1">
          <header className="rl-product-topbar">
            <div className="rl-breadcrumb"><span>HISTORY</span><b>/</b> REPORTS</div>
            <div className="rl-topbar-state"><i /> DETERMINISTIC SNAPSHOT</div>
          </header>

          <div className="rl-product-shell">
            {error ? (
              <div className="rl-product-error"><strong>Report unavailable</strong><span>{error}</span></div>
            ) : !analysis ? (
              <div className="rl-product-loading"><span /><span /><span /> Reconstructing report…</div>
            ) : (
              <>
                <section className="rl-report-hero">
                  <div className="rl-report-hero-grid" aria-hidden="true" />
                  <div className="rl-report-copy">
                    <div className="rl-page-kicker"><span className="rl-kicker-dot" /> REPOSITORY INTELLIGENCE · REPORT 01</div>
                    <h1>Repository <em>report.</em></h1>
                    <p>A deterministic, evidence-oriented snapshot of the current analysis artifacts — structure, relationships, and persisted signals without pretending to know what the analyzer did not establish.</p>
                    <div className="rl-report-actions">
                      <Link href="/architecture" className="rl-glow-button">Explore architecture <span>↗</span></Link>
                      <Link href="/evidence" className="rl-ghost-button">Trace evidence</Link>
                    </div>
                  </div>
                  <div className="rl-report-orbit" aria-hidden="true">
                    <div className="rl-orbit-ring ring-one" /><div className="rl-orbit-ring ring-two" />
                    <div className="rl-report-core"><span>RL</span><small>ANALYSIS</small></div>
                    <div className="rl-report-node n-one"><b>{metrics[0][1]}</b><span>FILES</span></div>
                    <div className="rl-report-node n-two"><b>{metrics[3][1]}</b><span>MODULES</span></div>
                    <div className="rl-report-node n-three"><b>{metrics[4][1]}</b><span>RELATIONS</span></div>
                    <div className="rl-report-node n-four"><b>{metrics[5][1]}</b><span>RISKS</span></div>
                  </div>
                </section>

                <section className="rl-metric-grid rl-report-metrics">
                  {metrics.map(([label, value, note], index) => (
                    <div key={label} className={`rl-premium-metric metric-${index}`}>
                      <div className="rl-metric-top"><span>{label}</span><i>{String(index + 1).padStart(2, "0")}</i></div>
                      <strong>{Number(value).toLocaleString()}</strong>
                      <small>{note}</small>
                      <div className="rl-mini-bars" aria-hidden="true">{[1,2,3,4,5].map((bar) => <i key={bar} style={{ height: `${12 + ((Number(value) + bar * 7) % 24)}px` }} />)}</div>
                    </div>
                  ))}
                </section>

                <section className="rl-report-grid">
                  <div className="rl-surface-card rl-report-scope">
                    <div className="rl-card-heading"><div><span>01 · SCOPE</span><h2>What this report actually says.</h2></div><span className="rl-status-chip">EVIDENCE-ORIENTED</span></div>
                    <div className="rl-scope-lines">
                      <div><b>Structure</b><span>Repository files, Python surface, production modules and architecture relationships.</span><i>ANALYZED</i></div>
                      <div><b>Dependencies</b><span>Resolved import relationships represented in the current dependency graph.</span><i>ANALYZED</i></div>
                      <div><b>Risk</b><span>Persisted deterministic signals produced by the current risk analyzer.</span><i>ANALYZED</i></div>
                      <div className="muted"><b>Not established</b><span>Runtime behavior, universal security, code quality, or complete test coverage.</span><i>OUT OF SCOPE</i></div>
                    </div>
                  </div>
                  <div className="rl-surface-card rl-report-nav">
                    <div className="rl-card-heading"><div><span>02 · NAVIGATION</span><h2>Jump into the evidence.</h2></div></div>
                    <Link href="/repository"><span>◫</span><div><b>Repository</b><small>Current analysis scope</small></div><em>↗</em></Link>
                    <Link href="/architecture"><span>◇</span><div><b>Architecture</b><small>Modules & relationships</small></div><em>↗</em></Link>
                    <Link href="/risks"><span>△</span><div><b>Risk signals</b><small>Investigate findings</small></div><em>↗</em></Link>
                    <Link href="/evidence"><span>◉</span><div><b>Evidence chain</b><small>Claim → source</small></div><em>↗</em></Link>
                  </div>
                </section>

                <footer className="rl-product-footer">RepoLens · deterministic repository reporting · current analyzer scope only</footer>
              </>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
