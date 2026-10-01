"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

const commands = [
  ["Overview", "/"],
  ["Repository", "/repository"],
  ["Architecture", "/architecture"],
  ["Dependencies", "/dependencies"],
  ["Risks", "/risks"],
  ["Security", "/security"],
  ["Testing", "/testing"],
  ["Evidence", "/evidence"],
  ["AI Q&A", "/qa"],
  ["Drift", "/drift"],
  ["Reports", "/reports"],
  ["Evaluation", "/evaluation"],
] as const;

export default function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
      }
      if (event.key === "Escape") setOpen(false);
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const filtered = useMemo(() => {
    const value = query.trim().toLowerCase();
    if (!value) return commands;
    return commands.filter(([label]) => label.toLowerCase().includes(value));
  }, [query]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center bg-black/65 px-4 pt-[12vh] backdrop-blur-md" role="dialog" aria-modal="true" aria-label="RepoLens command palette">
      <button className="absolute inset-0 cursor-default" aria-label="Close command palette" onClick={() => setOpen(false)} />
      <div className="relative w-full max-w-xl overflow-hidden rounded-2xl border border-white/12 bg-[#090b12]/95 shadow-[0_30px_100px_rgba(0,0,0,.65)] ring-1 ring-indigo-300/10">
        <div className="border-b border-white/8 px-4 py-3">
          <div className="flex items-center gap-3 rounded-xl border border-white/8 bg-white/[.035] px-3">
            <span className="text-white/30">⌕</span>
            <input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search RepoLens…" className="h-12 min-w-0 flex-1 bg-transparent text-sm text-white outline-none placeholder:text-white/25" />
            <kbd className="rounded-md border border-white/10 px-1.5 py-1 text-[9px] text-white/30">ESC</kbd>
          </div>
        </div>
        <div className="max-h-[55vh] overflow-y-auto p-2">
          {filtered.length ? filtered.map(([label, href], index) => (
            <button key={href} type="button" onClick={() => { setOpen(false); setQuery(""); router.push(href); }} className="group flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left transition hover:bg-indigo-400/[.08]">
              <span className="grid h-8 w-8 place-items-center rounded-lg border border-white/8 bg-white/[.025] text-[10px] text-white/35">{String(index + 1).padStart(2, "0")}</span>
              <span className="text-sm text-white/70 group-hover:text-white">{label}</span>
              <span className="ml-auto text-[10px] text-white/20">{href}</span>
            </button>
          )) : <div className="px-4 py-10 text-center text-xs text-white/30">No matching RepoLens destination.</div>}
        </div>
        <div className="border-t border-white/8 px-4 py-3 text-[9px] uppercase tracking-[.16em] text-white/20">⌘K anywhere · navigate instantly</div>
      </div>
    </div>
  );
}
