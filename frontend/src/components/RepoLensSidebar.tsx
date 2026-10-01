"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getRepositoryOverview, type RepositoryOverview } from "@/lib/api";
import CommandPalette from "@/components/CommandPalette";

const sections = [
  {
    title: "Analyze",
    items: [
      ["Overview", "⌂", "/"],
      ["Repository", "◫", "/repository"],
      ["Architecture", "◇", "/architecture"],
      ["Dependencies", "↗", "/dependencies"],
    ],
  },
  {
    title: "Intelligence",
    items: [
      ["Risks", "△", "/risks"],
      ["Security", "◇", "/security"],
      ["Testing", "✓", "/testing"],
      ["Evidence", "◉", "/evidence"],
      ["AI Q&A", "✦", "/qa"],
    ],
  },
  {
    title: "History",
    items: [
      ["Drift", "◌", "/drift"],
      ["Reports", "▤", "/reports"],
      ["Evaluation", "◎", "/evaluation"],
    ],
  },
] as const;

function isActive(pathname: string, href?: string, label?: string) {
  if (!href) return false;

  if (href === "/") {
    return pathname === "/" && label === "Overview";
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

function Brand() {
  return (
    <Link
      href="/"
      aria-label="Go to RepoLens overview"
      className="flex items-center gap-3"
    >
      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-white/15 bg-white/[0.04]">
        <span className="h-2.5 w-2.5 rotate-45 rounded-[2px] bg-gradient-to-br from-indigo-300 to-cyan-300 shadow-[0_0_14px_rgba(103,232,249,.65)]" />
      </span>

      <span>
        <span className="block text-sm font-semibold tracking-tight text-white">
          RepoLens
        </span>
        <span className="block text-[9px] font-medium tracking-[0.2em] text-white/30">
          CODE INTELLIGENCE
        </span>
      </span>
    </Link>
  );
}

export default function RepoLensSidebar() {
  const pathname = usePathname();
  const [overview, setOverview] = useState<RepositoryOverview | null>(null);

  useEffect(() => {
    let active = true;

    getRepositoryOverview()
      .then((data) => {
        if (active) setOverview(data);
      })
      .catch(() => {
        // Navigation must remain usable even when the API is offline.
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <>
      <CommandPalette />
      <aside className="sticky top-0 hidden h-screen w-[242px] shrink-0 self-start border-r border-indigo-300/10 bg-[#06070d]/95 shadow-[18px_0_60px_rgba(30,41,59,.12)] lg:flex lg:flex-col">
        <div className="flex h-[66px] items-center border-b border-white/[0.07] px-6">
          <Brand />
        </div>

        <div className="repolens-sidebar-scroll flex-1 overflow-y-auto px-3 py-7">
          {sections.map((section) => (
            <div key={section.title} className="mb-8">
              <div className="px-3 pb-3 text-[9px] font-semibold uppercase tracking-[0.2em] text-white/25">
                {section.title}
              </div>

              <nav className="space-y-1" aria-label={`${section.title} navigation`}>
                {section.items.map(([label, icon, href]) => {
                  const active = isActive(pathname, href, label);

                  if (!href) {
                    return (
                      <div
                        key={label}
                        className="flex h-10 items-center gap-3 rounded-lg px-3 text-[12px] text-white/20"
                        aria-disabled="true"
                      >
                        <span className="w-4 text-center text-[12px] text-white/25">
                          {icon}
                        </span>
                        <span>{label}</span>
                        <span className="ml-auto text-[8px] uppercase tracking-[0.12em] text-white/15">
                          Soon
                        </span>
                      </div>
                    );
                  }

                  return (
                    <Link
                      key={`${label}-${href}`}
                      href={href}
                      aria-current={active ? "page" : undefined}
                      className={`flex h-10 items-center gap-3 rounded-lg px-3 text-[12px] transition-colors ${
                        active
                          ? "bg-gradient-to-r from-indigo-400/16 via-sky-400/8 to-transparent text-white ring-1 ring-inset ring-indigo-300/15 shadow-[0_8px_24px_rgba(79,70,229,.12)]"
                          : "text-white/35 hover:bg-white/[0.045] hover:text-white/90"
                      }`}
                    >
                      <span className="w-4 text-center text-[12px] text-white/45">
                        {icon}
                      </span>
                      <span>{label}</span>
                      {active && (
                        <span className="ml-auto h-1.5 w-1.5 rounded-full bg-white/70" />
                      )}
                    </Link>
                  );
                })}
              </nav>
            </div>
          ))}
        </div>

        <div className="p-4">
          <div className="repolens-sidebar-status rounded-2xl border border-indigo-300/10 bg-gradient-to-br from-indigo-400/[0.10] via-cyan-400/[0.025] to-transparent p-4 shadow-[0_12px_40px_rgba(30,41,59,.20)]">
            <div className="mb-3 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              <span className="text-[10px] uppercase tracking-[0.18em] text-white/35">
                Active repository
              </span>
            </div>
            <div className="truncate text-sm font-medium text-white">
              {overview?.metadata.repository_name ?? "Repository analysis"}
            </div>
            <div className="mt-1 text-[11px] text-white/30">
              {overview
                ? `${overview.python_file_count} Python files · ${overview.dependency_edge_count} dependency edges`
                : "Analysis status available when API is connected"}
            </div>
          </div>
        </div>
      </aside>

      <div className="sticky top-0 z-40 border-b border-white/[0.07] bg-[#040404]/95 px-4 py-3 lg:hidden">
        <div className="flex items-center justify-between gap-3">
          <Brand />

          <details className="relative">
            <summary className="cursor-pointer list-none rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-[11px] font-medium text-white/70">
              Navigate
            </summary>

            <div className="absolute right-0 mt-2 w-[270px] rounded-2xl border border-white/10 bg-[#090909] p-3 shadow-2xl shadow-black/50">
              {sections.map((section) => (
                <div key={section.title} className="mb-4 last:mb-0">
                  <div className="px-2 pb-2 text-[9px] font-semibold uppercase tracking-[0.2em] text-white/25">
                    {section.title}
                  </div>

                  <nav className="space-y-1">
                    {section.items.map(([label, icon, href]) => {
                      const active = isActive(pathname, href, label);

                      if (!href) {
                        return (
                          <div
                            key={label}
                            className="flex items-center justify-between rounded-lg px-3 py-2.5 text-xs text-white/20"
                          >
                            <span className="flex items-center gap-2">
                              <span className="w-4 text-center">{icon}</span>
                              {label}
                            </span>
                            <span className="text-[8px] uppercase tracking-wider text-white/15">
                              Soon
                            </span>
                          </div>
                        );
                      }

                      return (
                        <Link
                          key={`${label}-${href}`}
                          href={href}
                          aria-current={active ? "page" : undefined}
                          className={`flex items-center gap-2 rounded-lg px-3 py-2.5 text-xs transition-colors ${
                            active
                              ? "bg-gradient-to-r from-indigo-400/16 via-sky-400/8 to-transparent text-white ring-1 ring-inset ring-indigo-300/15 shadow-[0_8px_24px_rgba(79,70,229,.12)]"
                              : "text-white/45 hover:bg-white/[0.04] hover:text-white/80"
                          }`}
                        >
                          <span className="w-4 text-center">{icon}</span>
                          {label}
                        </Link>
                      );
                    })}
                  </nav>
                </div>
              ))}
            </div>
          </details>
        </div>
      </div>
    </>
  );
}
