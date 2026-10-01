"use client";

import { useEffect, useMemo, useState } from "react";
import RepoLensSidebar from "@/components/RepoLensSidebar";
import { getRepositoryAnalysis, type RepositoryAnalysis, type RiskSignal } from "@/lib/api";

function normalizePath(value?: string) { return (value ?? "").replaceAll("\\", "/"); }
function normalizeSeverity(value?: string) { return (value ?? "UNKNOWN").toUpperCase(); }

function SignalCard({ signal, index }: { signal: RiskSignal; index: number }) {
  return (
    <article className="rl-security-signal">
      <div className="rl-signal-index">{String(index + 1).padStart(2, "0")}</div>
      <div className="rl-signal-body">
        <div className="rl-signal-head"><div><span>SECURITY SIGNAL</span><h3>{signal.signal ?? "unknown_signal"}</h3></div><b>{normalizeSeverity(signal.severity)}</b></div>
        <div className="rl-signal-location"><span>FILE</span><code>{normalizePath(signal.file) || "Not provided"}</code><span>LINE</span><code>{typeof signal.line === "number" ? signal.line : "—"}</code></div>
        {signal.reason && <p>{signal.reason}</p>}
        <div className="rl-redacted-evidence"><span>REDACTED EVIDENCE</span><b>Matched value intentionally withheld</b><small>RepoLens records location and detector metadata without rendering the sensitive value.</small></div>
      </div>
    </article>
  );
}

export default function SecurityPage() {
  const [analysis, setAnalysis] = useState<RepositoryAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getRepositoryAnalysis().then((result) => { if (active) setAnalysis(result); }).catch((err) => active && setError(err instanceof Error ? err.message : "Failed to load security analysis.")).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  const signals = useMemo(() => {
    const source = [...(analysis?.risks?.risk_signals ?? []), ...(analysis?.risk_signals ?? [])];
    const seen = new Set<string>();
    return source.filter((signal) => {
      if (String(signal.category ?? "").toLowerCase() !== "security") return false;
      const key = JSON.stringify([signal.signal, signal.file, signal.line]);
      if (seen.has(key)) return false; seen.add(key); return true;
    });
  }, [analysis]);
  const secretCount = signals.filter((s) => String(s.signal ?? "").toLowerCase() === "possible_hardcoded_secret").length;

  if (loading) return <main className="min-h-screen repolens-page repolens-route-security text-white"><div className="rl-full-state">Scanning security surface…</div></main>;
  if (error || !analysis) return <main className="min-h-screen repolens-page text-white"><div className="rl-full-state"><div className="rl-product-error"><strong>Security data unavailable</strong><span>{error ?? "Repository security data could not be loaded."}</span></div></div></main>;

  return (
    <main className="min-h-screen repolens-page repolens-route-security text-white">
      <div className="flex min-h-screen flex-col lg:flex-row"><RepoLensSidebar /><section className="min-w-0 flex-1">
        <header className="rl-product-topbar"><div className="rl-breadcrumb"><span>INTELLIGENCE</span><b>/</b> SECURITY</div><div className="rl-topbar-state"><i /> VALUES REDACTED</div></header>
        <div className="rl-product-shell">
          <section className="rl-security-hero">
            <div className="rl-security-copy"><div className="rl-page-kicker"><span className="rl-kicker-dot" /> SECURITY INTELLIGENCE · SCOPE 01</div><h1>Detect what should <em>never be committed.</em></h1><p>RepoLens performs conservative detection of possible hardcoded secrets while keeping potentially sensitive values out of reported evidence.</p></div>
            <div className="rl-scanner"><div className="rl-scan-grid" /><div className="rl-scan-ring"><span>{signals.length}</span><small>SIGNALS</small></div><div className="rl-scan-line" /><div className="rl-scan-label top">SECRET-LIKE ASSIGNMENTS</div><div className="rl-scan-label bottom">VALUE REDACTED</div></div>
          </section>

          <section className="rl-security-metrics">
            <div><span>SECURITY SIGNALS</span><strong>{signals.length}</strong><small>detected by current analyzer</small></div>
            <div><span>POSSIBLE SECRETS</span><strong>{secretCount}</strong><small>possible hardcoded-secret signals</small></div>
            <div><span>STATUS</span><strong>{signals.length ? "REVIEW" : "NO SIGNALS"}</strong><small>based only on current analyzer output</small></div>
            <div><span>VALUES EXPOSED</span><strong>REDACTED</strong><small>matched values are never rendered</small></div>
          </section>

          <section className="rl-security-layout">
            <div className="rl-surface-card">
              <div className="rl-card-heading"><div><span>DETECTION RESULT</span><h2>Current security findings.</h2></div><span className="rl-status-chip">SCOPE-LIMITED</span></div>
              {signals.length === 0 ? <div className="rl-security-empty"><div className="rl-empty-icon">✓</div><div><h3>No security-specific signals detected</h3><p>The current security analyzer did not produce possible hardcoded-secret signals for this repository.</p><div className="rl-warning-note">This does not mean the repository is universally secure. It only describes the checks currently implemented by RepoLens.</div></div></div> : <div className="rl-security-list">{signals.map((signal, index) => <SignalCard key={`${signal.signal}-${signal.file}-${signal.line}-${index}`} signal={signal} index={index} />)}</div>}
            </div>
            <aside className="rl-surface-card rl-scope-panel"><div className="rl-card-heading"><div><span>ANALYZER SCOPE</span><h2>What is actually checked.</h2></div></div><div className="rl-scope-step"><b>01</b><div><strong>Secret-like names</strong><p>Assignment names are matched against configured secret-name hints.</p></div></div><div className="rl-scope-step"><b>02</b><div><strong>Placeholder filtering</strong><p>Known example values are excluded to reduce expected false positives.</p></div></div><div className="rl-scope-step"><b>03</b><div><strong>Test/example filtering</strong><p>Test and example files are excluded from this detector.</p></div></div><div className="rl-scope-step"><b>04</b><div><strong>Location, not value</strong><p>Findings retain file and line metadata without exposing the assigned value.</p></div></div></aside>
          </section>
          <div className="rl-scope-banner"><span>NOT ESTABLISHED</span><p>Dependency vulnerabilities, authentication flaws, authorization bugs, injection issues, cryptographic weaknesses, and runtime attacks are outside this detector.</p></div>
          <footer className="rl-product-footer">RepoLens · security signals are evidence-backed and scope-limited · no universal security claim</footer>
        </div>
      </section></div>
    </main>
  );
}
