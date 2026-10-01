import RepoLensSidebar from "@/components/RepoLensSidebar";

export default function Loading() {
  return (
    <div className="flex min-h-screen flex-col bg-[#05060b] text-white lg:flex-row">
      <RepoLensSidebar />
      <main className="min-w-0 flex-1">
        <div className="repolens-loading-screen">
          <div className="w-[min(560px,90vw)]">
            <div className="text-[10px] uppercase tracking-[0.2em] text-indigo-300/60">RepoLens / loading</div>
            <h1 className="mt-3 text-2xl font-semibold tracking-tight">Loading repository intelligence.</h1>
            <p className="mt-2 text-sm leading-6 text-white/40">The application shell remains available while this route loads.</p>
            <div className="mt-7 h-1.5 w-40 overflow-hidden rounded-full bg-white/10"><div className="h-full w-1/2 animate-pulse rounded-full bg-gradient-to-r from-indigo-400 to-cyan-300" /></div>
          </div>
        </div>
      </main>
    </div>
  );
}
