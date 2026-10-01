"use client";

import { useEffect, useMemo, useState } from "react";
import RepoLensSidebar from "@/components/RepoLensSidebar";
import { getRepositoryAnalysis, type RepositoryAnalysis } from "@/lib/api";

type EvidenceReference = { evidence_type?: string; file?: string | null; module_name?: string | null; start_line?: number | null; end_line?: number | null; [key: string]: unknown };
type EvidenceClaim = { text: string; status?: string; category?: string; severity?: string; evidence?: EvidenceReference[] };
type RiskIntelligence = { claim_count?: number; claims?: EvidenceClaim[]; coverage?: { claim_count?: number; supported_claims?: number; unsupported_claims?: number; coverage?: number } };
function path(value?: string | null) { return (value ?? "").replaceAll("\\", "/"); }

export default function EvidencePage() {
  const [analysis, setAnalysis] = useState<RepositoryAnalysis | null>(null);
  const [selected, setSelected] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { let active = true; getRepositoryAnalysis().then((result) => active && setAnalysis(result)).catch((err) => active && setError(err instanceof Error ? err.message : "Failed to load evidence analysis.")).finally(() => active && setLoading(false)); return () => { active = false; }; }, []);

  const intelligence = (analysis?.risk_intelligence ?? {}) as RiskIntelligence;
  const claims = useMemo(() => intelligence.claims ?? [], [intelligence.claims]);
  const coverage = intelligence.coverage ?? {};
  const claimCount = typeof coverage.claim_count === "number" ? coverage.claim_count : typeof intelligence.claim_count === "number" ? intelligence.claim_count : claims.length;
  const supported = typeof coverage.supported_claims === "number" ? coverage.supported_claims : 0;
  const unsupported = typeof coverage.unsupported_claims === "number" ? coverage.unsupported_claims : 0;
  const coveragePercent = Math.round((typeof coverage.coverage === "number" ? coverage.coverage : claimCount ? supported / claimCount : 0) * 100);
  const activeClaim = claims[selected] ?? claims[0];
  const referenceCount = useMemo(() => claims.reduce((sum, claim) => sum + (claim.evidence?.length ?? 0), 0), [claims]);

  if (loading) return <main className="min-h-screen repolens-page repolens-route-evidence text-white"><div className="rl-full-state">Tracing evidence chain…</div></main>;
  if (error || !analysis) return <main className="min-h-screen repolens-page text-white"><div className="rl-full-state"><div className="rl-product-error"><strong>Evidence data unavailable</strong><span>{error ?? "Repository evidence data could not be loaded."}</span></div></div></main>;

  return <main className="min-h-screen repolens-page repolens-route-evidence text-white"><div className="flex min-h-screen flex-col lg:flex-row"><RepoLensSidebar /><section className="min-w-0 flex-1">
    <header className="rl-product-topbar"><div className="rl-breadcrumb"><span>INTELLIGENCE</span><b>/</b> EVIDENCE</div><div className="rl-topbar-state"><i /> {coveragePercent}% VERIFIED COVERAGE</div></header>
    <div className="rl-product-shell">
      <section className="rl-evidence-hero"><div className="rl-evidence-copy"><div className="rl-page-kicker"><span className="rl-kicker-dot" /> EVIDENCE INTELLIGENCE · TRACE 01</div><h1>Every claim should have <em>something behind it.</em></h1><p>RepoLens connects generated risk claims to concrete repository evidence. Unsupported claims remain visible as unsupported instead of being silently promoted to facts.</p></div><div className="rl-evidence-chain" aria-hidden="true"><div className="chain-node"><b>{claimCount}</b><span>CLAIMS</span></div><i /><div className="chain-node accent"><b>{supported}</b><span>SUPPORTED</span></div><i /><div className="chain-node"><b>{referenceCount}</b><span>REFERENCES</span></div></div></section>

      <section className="rl-evidence-metrics"><div><span>CLAIMS</span><strong>{claimCount}</strong><small>generated risk claims</small></div><div><span>SUPPORTED</span><strong>{supported}</strong><small>claims with supporting evidence</small></div><div><span>UNSUPPORTED</span><strong>{unsupported}</strong><small>claims without sufficient support</small></div><div className="coverage"><span>EVIDENCE COVERAGE</span><strong>{coveragePercent}%</strong><div className="rl-coverage-track"><i style={{ width: `${Math.max(0, Math.min(100, coveragePercent))}%` }} /></div></div></section>

      <section className="rl-evidence-workbench">
        <div className="rl-surface-card rl-claim-list"><div className="rl-card-heading"><div><span>CLAIM LEDGER</span><h2>Select a claim to inspect its trail.</h2></div><span className="rl-status-chip">{claims.length} RECORDED</span></div>{claims.length === 0 ? <div className="rl-security-empty"><div className="rl-empty-icon">—</div><div><h3>No claims recorded</h3><p>The current analysis does not expose a claim ledger.</p></div></div> : <div className="rl-claim-items">{claims.map((claim, index) => <button type="button" key={`${claim.text}-${index}`} onClick={() => setSelected(index)} className={`rl-claim-item ${selected === index ? "selected" : ""}`}><span>{String(index + 1).padStart(2, "0")}</span><div><b>{claim.text}</b><small>{String(claim.status ?? "unknown").toUpperCase()} · {claim.evidence?.length ?? 0} references</small></div><em>→</em></button>)}</div>}</div>
        <aside className="rl-surface-card rl-claim-detail"><div className="rl-card-heading"><div><span>TRACE VIEW</span><h2>Claim → evidence.</h2></div><span className="rl-status-chip">{activeClaim ? String(activeClaim.status ?? "UNKNOWN").toUpperCase() : "EMPTY"}</span></div>{activeClaim ? <><div className="rl-active-claim"><span>SELECTED CLAIM</span><p>{activeClaim.text}</p></div><div className="rl-trace-line"><div className="trace-dot claim" /><div><span>CLAIM</span><b>Recorded analysis statement</b></div></div><div className="rl-trace-connector" />{(activeClaim.evidence ?? []).length ? (activeClaim.evidence ?? []).map((item, index) => <div className="rl-trace-line" key={`${item.file}-${item.module_name}-${index}`}><div className="trace-dot source" /><div><span>SOURCE {String(index + 1).padStart(2, "0")}</span><b>{path(item.file) || item.module_name || "Repository-level evidence"}</b><small>{item.evidence_type ?? "reference"}{typeof item.start_line === "number" ? ` · line ${item.start_line}` : ""}{typeof item.end_line === "number" ? `–${item.end_line}` : ""}</small></div></div>) : <div className="rl-warning-note">No evidence reference was attached to this claim.</div>}</> : <div className="rl-warning-note">Select a claim to inspect its evidence trail.</div>}</aside>
      </section>

      <footer className="rl-product-footer">RepoLens · evidence is concrete, status is explicit, and unsupported claims stay visible</footer>
    </div>
  </section></div></main>;
}
