import Link from "next/link";

export default function NotFound() {
  return (
    <main className="grid min-h-screen place-items-center bg-[#05060b] px-6 text-white">
      <div className="w-full max-w-xl rounded-3xl border border-indigo-300/10 bg-white/[0.035] p-8 shadow-2xl shadow-indigo-950/25">
        <div className="text-[10px] uppercase tracking-[0.2em] text-indigo-300/60">404 / RepoLens</div>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight">That surface does not exist.</h1>
        <p className="mt-3 text-sm leading-6 text-white/40">The requested route is outside the current product surface.</p>
        <Link href="/" className="mt-7 inline-flex rounded-xl border border-indigo-300/20 bg-indigo-400/15 px-4 py-2.5 text-sm font-medium text-indigo-100 hover:bg-indigo-400/25">Return to overview</Link>
      </div>
    </main>
  );
}
