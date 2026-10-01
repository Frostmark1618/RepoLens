"use client";

import RepoLensSidebar from "@/components/RepoLensSidebar";

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="flex min-h-screen flex-col bg-[#05060b] text-white lg:flex-row">
      <RepoLensSidebar />
      <main className="min-w-0 flex-1">
        <div className="repolens-error-screen">
          <div className="w-full max-w-xl">
            <div className="text-[10px] uppercase tracking-[0.2em] text-red-300/70">RepoLens runtime boundary</div>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight">This view hit an unexpected error.</h1>
            <p className="mt-3 text-sm leading-6 text-white/45">The failure was contained at the route boundary. The application shell remains available, and you can retry this view.</p>
            <button type="button" onClick={() => reset()} className="mt-7 rounded-xl border border-indigo-300/20 bg-indigo-400/15 px-4 py-2.5 text-sm font-medium text-indigo-100 hover:bg-indigo-400/25">Retry view</button>
          </div>
        </div>
      </main>
    </div>
  );
}
