"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import RepoLensSidebar from "@/components/RepoLensSidebar";
import { getRepositoryAnalysis, getRepositoryOverview, type RepositoryAnalysis, type RepositoryOverview } from "@/lib/api";

function topLevelEntries(fileTree: unknown): string[] {
  if (!fileTree || typeof fileTree !== "object" || Array.isArray(fileTree)) return [];
  const root = Object.values(fileTree as Record<string, unknown>)[0];
  if (!root || typeof root !== "object" || Array.isArray(root)) return [];
  return Object.keys(root as Record<string, unknown>).sort((a, b) => a.localeCompare(b));
}

function layerEntries(analysis: RepositoryAnalysis | null) {
  const architecture = analysis?.architecture;
  if (!architecture || typeof architecture !== "object") return [];
  const summary = (architecture as Record<string, unknown>).layer_summary;
  if (!summary || typeof summary !== "object" || Array.isArray(summary)) return [];
  return Object.entries(summary as Record<string, unknown>)
    .map(([name, value]) => [name, Number(value) || 0] as const)
    .filter(([, count]) => count > 0)
    .sort((a, b) => b[1] - a[1]);
}

export default function RepositoryPage() {
  const [overview, setOverview] = useState<RepositoryOverview | null>(null);
  const [analysis, setAnalysis] = useState<RepositoryAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        setLoading(true);
        setError("");
        const [overviewData, analysisData] = await Promise.all([getRepositoryOverview(), getRepositoryAnalysis()]);
        if (!active) return;
        setOverview(overviewData);
        setAnalysis(analysisData);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Unable to load repository intelligence.");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => { active = false; };
  }, []);

  const entries = useMemo(() => topLevelEntries(analysis?.file_tree), [analysis]);
  const layers = useMemo(() => layerEntries(analysis), [analysis]);
  const name = overview?.metadata.repository_name ?? "Repository";
  const path = overview?.metadata.repository_path ?? "";
  const total = overview?.metadata.total_files ?? 0;
  const python = overview?.metadata.python_files ?? 0;
  const relevant = overview?.relevant_file_count ?? 0;
  const modules = overview?.production_module_count ?? 0;
  const dependencies = overview?.dependency_edge_count ?? 0;
  const architectureEdges = overview?.architecture.edge_count ?? 0;
  const risks = overview?.risk.signal_count ?? 0;

  return (
    <div className="min-h-screen repolens-page repolens-route-repository bg-[#030303] text-white">
      <div className="flex min-h-screen">
        <RepoLensSidebar />
        <main className="min-w-0 flex-1">
          <header className="flex h-[66px] items-center justify-between border-b border-white/[0.07] px-5 lg:px-8">
            <div>
              <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">Repository</div>
              <div className="mt-0.5 flex items-center gap-2 text-xs font-medium">
                {name}
                <span className="rounded border border-white/10 px-1.5 py-0.5 text-[9px] text-white/35">main</span>
              </div>
            </div>
            <Link href="/" className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-[11px] font-medium text-white/70 transition hover:bg-white/[0.08]">Back to overview</Link>
          </header>

          <div className="mx-auto w-full max-w-[1380px] px-5 py-10 lg:px-10 lg:py-14">
            <section>
              <div className="flex items-center gap-2 text-[10px] font-medium uppercase tracking-[0.2em] text-white/35"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />Repository intelligence</div>
              <h1 className="mt-5 max-w-4xl text-[44px] font-semibold leading-[0.98] tracking-[-0.045em] sm:text-[58px] lg:text-[64px]">Know what is inside.<br /><span className="text-white/30">Before changing it.</span></h1>
              <p className="mt-6 max-w-2xl text-sm leading-6 text-white/40">RepoLens maps the repository as an analyzable system: files, Python structure, production modules, dependencies, architecture relationships, and deterministic risk signals.</p>
            </section>

            {error && <div className="mt-8 rounded-2xl border border-red-400/20 bg-red-500/[0.06] px-5 py-4"><div className="text-xs font-medium text-red-300">Repository analysis could not be loaded.</div><div className="mt-1 text-[11px] text-red-200/50">{error}</div></div>}

            <section className="mt-10 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {[["Files analyzed", total, `${python} Python files`], ["Relevant files", relevant, "analysis-relevant files"], ["Production modules", modules, "architecture modules"], ["Risk signals", risks, "deterministic findings"]].map(([label, value, detail]) => (
                <div key={label} className="rounded-xl border border-white/[0.08] bg-white/[0.025] p-5"><div className="text-[10px] font-medium uppercase tracking-[0.16em] text-white/30">{label}</div><div className="mt-7 text-[32px] font-semibold tracking-[-0.04em]">{loading ? "—" : Number(value).toLocaleString()}</div><div className="mt-1 text-[9px] text-white/25">{detail}</div></div>
              ))}
            </section>

            <section className="mt-8 grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
              <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02]"><div className="border-b border-white/[0.07] px-5 py-4"><div className="text-sm font-medium">Repository identity</div><div className="mt-1 text-[10px] text-white/30">The concrete source analyzed by the current RepoLens run.</div></div><div className="grid gap-3 p-5 sm:grid-cols-2">
                {[["Repository", name], ["Analysis path", path || "Not reported"], ["Dependency graph", `${dependencies.toLocaleString()} edges`], ["Architecture graph", `${architectureEdges.toLocaleString()} relationships`]].map(([label, value]) => <div key={label} className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-4"><div className="text-[9px] uppercase tracking-[0.16em] text-white/25">{label}</div><div className={`mt-2 text-sm font-medium ${label === "Analysis path" ? "break-all font-mono text-[11px] text-white/55" : ""}`}>{loading && label !== "Repository" ? "—" : value}</div></div>)}
              </div></div>

              <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02]"><div className="border-b border-white/[0.07] px-5 py-4"><div className="text-sm font-medium">Architecture layers</div><div className="mt-1 text-[10px] text-white/30">Production modules grouped by deterministic architecture analysis.</div></div><div className="space-y-3 p-5">{layers.length === 0 && !loading ? <div className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-4 text-[11px] text-white/35">No layer summary is available.</div> : (loading ? [["Loading", 0] as const] : layers).map(([layer, count]) => <div key={layer}><div className="flex items-center justify-between text-[10px]"><span className="text-white/55">{layer}</span><span className="text-white/30">{count}</span></div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/[0.06]"><div className="h-full rounded-full bg-white/40" style={{ width: `${Math.min(100, (count / Math.max(modules, 1)) * 100)}%` }} /></div></div>)}</div></div>
            </section>

            <section className="mt-6 rounded-2xl border border-white/[0.08] bg-white/[0.02]"><div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-4"><div><div className="text-sm font-medium">Repository structure</div><div className="mt-1 text-[10px] text-white/30">Top-level entries from the analyzed repository tree.</div></div><div className="text-[10px] text-white/25">{entries.length} top-level entries</div></div><div className="grid gap-2 p-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">{loading ? <div className="col-span-full rounded-xl border border-white/[0.07] bg-white/[0.02] p-5 text-[11px] text-white/30">Loading repository structure…</div> : entries.length === 0 ? <div className="col-span-full rounded-xl border border-white/[0.07] bg-white/[0.02] p-5 text-[11px] text-white/30">No repository tree data is available.</div> : entries.map((entry) => <div key={entry} className="rounded-xl border border-white/[0.07] bg-white/[0.02] px-4 py-3 transition hover:border-white/[0.13] hover:bg-white/[0.035]"><div className="flex items-center gap-3"><span className="grid h-7 w-7 place-items-center rounded-lg border border-white/10 bg-white/[0.03] text-[10px] text-white/45">/</span><span className="truncate font-mono text-[11px] text-white/65">{entry}</span></div></div>)}</div></section>

            <div className="mt-8 flex flex-wrap gap-2"><Link href="/architecture" className="rounded-lg border border-white/10 bg-white/[0.04] px-4 py-2.5 text-[11px] font-medium text-white/70 transition hover:bg-white/[0.08]">Explore architecture →</Link><Link href="/dependencies" className="rounded-lg border border-white/10 bg-white/[0.04] px-4 py-2.5 text-[11px] font-medium text-white/70 transition hover:bg-white/[0.08]">Inspect dependencies →</Link><Link href="/qa" className="rounded-lg bg-white px-4 py-2.5 text-[11px] font-semibold text-black transition hover:bg-white/90">Ask RepoLens →</Link></div>
          </div>
        </main>
      </div>
    </div>
  );
}
