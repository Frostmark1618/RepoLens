"use client";

import { useEffect, useMemo, useState } from "react";
import RepoLensSidebar from "@/components/RepoLensSidebar";

import {
  getRepositoryAnalysis,
  type RepositoryAnalysis,
  type RiskSignal,
} from "@/lib/api";

function normalizePath(value?: string): string {
  return (value ?? "").replaceAll("\\", "/");
}

function testingSignalLabel(signal?: string): string {
  switch (signal) {
    case "unreferenced_production_module":
      return "Unreferenced production module";

    case "missing_test_counterpart":
      return "Missing test counterpart";

    default:
      return signal ?? "Unknown testing signal";
  }
}

function SignalCard({
  signal,
}: {
  signal: RiskSignal;
}) {
  const isUnreferenced =
    signal.signal === "unreferenced_production_module";

  const isMissingCounterpart =
    signal.signal === "missing_test_counterpart";

  const evidence =
    typeof signal.evidence === "object" &&
    signal.evidence !== null
      ? (signal.evidence as Record<string, unknown>)
      : {};

  const expectedTestFiles = Array.isArray(
    evidence.expected_test_files,
  )
    ? evidence.expected_test_files.filter(
        (value): value is string =>
          typeof value === "string",
      )
    : [];

  return (
    <div className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-6">
      <div className="flex items-start justify-between gap-5">
        <div>
          <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
            Testing signal
          </div>

          <div className="mt-3 text-base font-medium text-white">
            {testingSignalLabel(signal.signal)}
          </div>
        </div>

        <div className="rounded-full border border-white/10 px-3 py-1.5 text-[9px] uppercase tracking-widest text-white/40">
          possible risk
        </div>
      </div>

      <div className="mt-6 rounded-xl border border-white/8 bg-white/[0.02] p-4">
        <div className="text-[9px] uppercase tracking-widest text-white/25">
          Production file
        </div>

        <div className="mt-2 break-all font-mono text-sm text-white/65">
          {normalizePath(
            signal.file ??
              (typeof evidence.production_file ===
              "string"
                ? evidence.production_file
                : ""),
          ) || "Not provided"}
        </div>

        {signal.module_name && (
          <div className="mt-2 font-mono text-xs text-white/30">
            {signal.module_name}
          </div>
        )}
      </div>

      {isUnreferenced && (
        <div className="mt-4 rounded-xl border border-white/8 bg-black/20 p-4">
          <div className="text-[9px] uppercase tracking-widest text-white/25">
            Test references
          </div>

          <div className="mt-2 text-sm text-white/45">
            No test references were detected for this
            production module.
          </div>
        </div>
      )}

      {isMissingCounterpart && (
        <div className="mt-4 rounded-xl border border-white/8 bg-black/20 p-4">
          <div className="text-[9px] uppercase tracking-widest text-white/25">
            Expected test counterparts
          </div>

          {expectedTestFiles.length === 0 ? (
            <div className="mt-2 text-sm text-white/35">
              No candidate test counterpart was reported.
            </div>
          ) : (
            <div className="mt-3 space-y-2">
              {expectedTestFiles.map((file) => (
                <div
                  key={file}
                  className="rounded-lg border border-white/8 bg-white/[0.02] px-3 py-2 font-mono text-xs text-white/50"
                >
                  {normalizePath(file)}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="mt-4 rounded-xl border border-white/8 bg-white/[0.02] p-4">
        <div className="text-[9px] uppercase tracking-widest text-white/25">
          Evidence
        </div>

        <div className="mt-2 text-xs leading-6 text-white/35">
          {isUnreferenced
            ? "The module has no detected test references in the analyzed test-reference map."
            : isMissingCounterpart
              ? "The analyzer did not find a direct test counterpart for the production file."
              : "This finding is based on the deterministic testing analyzer."}
        </div>
      </div>
    </div>
  );
}

function MethodologyCard({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-white/8 bg-white/[0.02] p-5">
      <div className="flex items-start gap-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-white/10 font-mono text-[10px] text-white/40">
          {number}
        </div>

        <div>
          <div className="text-sm text-white/75">
            {title}
          </div>

          <p className="mt-2 text-xs leading-6 text-white/35">
            {description}
          </p>
        </div>
      </div>
    </div>
  );
}

export default function TestingPage() {
  const [analysis, setAnalysis] =
    useState<RepositoryAnalysis | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        setLoading(true);
        setError(null);

        const result = await getRepositoryAnalysis();

        if (!active) {
          return;
        }

        setAnalysis(result);
      } catch (err) {
        if (!active) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Failed to load testing analysis.",
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      active = false;
    };
  }, []);

  const testingSignals = useMemo(() => {
    if (!analysis) {
      return [];
    }

    const nested =
      analysis.risks?.risk_signals ?? [];

    const root = analysis.risk_signals ?? [];

    const seen = new Set<string>();
    const result: RiskSignal[] = [];

    for (const signal of [...nested, ...root]) {
      const category =
        String(signal.category ?? "").toLowerCase();

      const signalName =
        String(signal.signal ?? "").toLowerCase();

      if (
        category !== "testing" &&
        !signalName.includes("test")
      ) {
        continue;
      }

      const key = JSON.stringify([
        signal.signal,
        signal.file,
        signal.module_name,
      ]);

      if (seen.has(key)) {
        continue;
      }

      seen.add(key);
      result.push(signal);
    }

    return result;
  }, [analysis]);

  const unreferencedModules = useMemo(() => {
    return testingSignals.filter(
      (signal) =>
        signal.signal ===
        "unreferenced_production_module",
    );
  }, [testingSignals]);

  const missingTestCounterparts = useMemo(() => {
    return testingSignals.filter(
      (signal) =>
        signal.signal ===
        "missing_test_counterpart",
    );
  }, [testingSignals]);

  const testingStatus =
    testingSignals.length === 0
      ? "No signals"
      : "Review required";

  if (loading) {
    return (
      <main className="min-h-screen repolens-page repolens-route-testing bg-[#050505] text-white">
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-sm text-white/40">
            Loading testing intelligence…
          </div>
        </div>
      </main>
    );
  }

  if (error || !analysis) {
    return (
      <main className="min-h-screen repolens-page bg-[#050505] text-white">
        <div className="flex min-h-screen items-center justify-center p-8">
          <div className="max-w-lg rounded-2xl border border-red-400/20 bg-red-400/5 p-6">
            <div className="text-sm font-medium text-red-300">
              Testing data unavailable
            </div>

            <p className="mt-3 text-sm leading-6 text-white/50">
              {error ??
                "Repository testing data could not be loaded."}
            </p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen repolens-page bg-[#050505] text-white">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <RepoLensSidebar />

        <section className="min-w-0 flex-1">
          <header className="flex h-16 items-center justify-between border-b border-white/10 px-6 lg:px-10">
            <div className="text-xs text-white/30">
              Repository / Testing
            </div>

            <span className="rounded-full border border-white/10 px-3 py-1.5 text-[10px] uppercase tracking-widest text-white/35">
              Deterministic analysis
            </span>
          </header>

          <div className="mx-auto max-w-[1500px] px-6 py-10 lg:px-10">
            <div className="max-w-4xl">
              <div className="text-xs uppercase tracking-[0.2em] text-white/30">
                Testing intelligence
              </div>

              <h1 className="mt-5 text-5xl font-semibold tracking-[-0.045em] text-white lg:text-7xl">
                See what is
                <span className="block text-white/30">
                  actually tested.
                </span>
              </h1>

              <p className="mt-6 max-w-3xl text-base leading-7 text-white/40">
                RepoLens checks production modules against the
                repository&apos;s detected test references and direct
                test-counterpart structure.
              </p>
            </div>

            <div className="mt-12 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-6">
                <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                  Testing signals
                </div>

                <div className="mt-5 text-4xl font-semibold text-white">
                  {testingSignals.length}
                </div>

                <div className="mt-2 text-xs text-white/30">
                  deterministic findings
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-6">
                <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                  Unreferenced modules
                </div>

                <div className="mt-5 text-4xl font-semibold text-white">
                  {unreferencedModules.length}
                </div>

                <div className="mt-2 text-xs text-white/30">
                  no detected test references
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-6">
                <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                  Missing counterparts
                </div>

                <div className="mt-5 text-4xl font-semibold text-white">
                  {missingTestCounterparts.length}
                </div>

                <div className="mt-2 text-xs text-white/30">
                  direct test counterpart absent
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-6">
                <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                  Current status
                </div>

                <div className="mt-5 text-2xl font-semibold text-white">
                  {testingStatus}
                </div>

                <div className="mt-2 text-xs text-white/30">
                  based only on analyzer output
                </div>
              </div>
            </div>

            <div className="mt-7 rounded-2xl border border-white/10 bg-[#0b0b0b]">
              <div className="border-b border-white/10 px-6 py-5">
                <div className="text-sm font-medium text-white">
                  Testing findings
                </div>

                <div className="mt-1 text-xs text-white/35">
                  Structural testing signals detected in the
                  analyzed repository
                </div>
              </div>

              <div className="p-6">
                {testingSignals.length === 0 ? (
                  <div className="rounded-2xl border border-white/8 bg-white/[0.02] p-8">
                    <div className="flex items-start gap-5">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/[0.03] text-white/60">
                        ✓
                      </div>

                      <div>
                        <div className="text-base font-medium text-white">
                          No testing-specific signals detected
                        </div>

                        <p className="mt-2 max-w-3xl text-sm leading-7 text-white/40">
                          The current testing analyzers did not
                          produce any unreferenced-production-module
                          or missing-test-counterpart findings for
                          this repository.
                        </p>

                        <div className="mt-5 rounded-xl border border-white/8 bg-black/20 px-4 py-3 text-xs leading-6 text-white/30">
                          This does not establish complete test
                          coverage or prove that all behavior is
                          tested. It only describes the structural
                          checks currently implemented by RepoLens.
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="grid gap-4">
                    {testingSignals.map((signal, index) => (
                      <SignalCard
                        key={`${signal.signal}-${signal.file}-${signal.module_name}-${index}`}
                        signal={signal}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="mt-7 grid gap-7 xl:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-[#0b0b0b]">
                <div className="border-b border-white/10 px-6 py-5">
                  <div className="text-sm font-medium text-white">
                    What RepoLens checks
                  </div>

                  <div className="mt-1 text-xs text-white/35">
                    Current testing analyzer scope
                  </div>
                </div>

                <div className="space-y-3 p-6">
                  <MethodologyCard
                    number="01"
                    title="Production module references"
                    description="Each production module is checked against the detected test-reference map. Modules without references can produce an unreferenced-production-module signal."
                  />

                  <MethodologyCard
                    number="02"
                    title="Direct test counterparts"
                    description="Production files are checked for an expected direct test counterpart. Missing counterparts can produce a missing-test-counterpart signal."
                  />

                  <MethodologyCard
                    number="03"
                    title="Deterministic evidence"
                    description="Findings preserve the production file and, where applicable, the expected test files or detected test-reference state."
                  />

                  <MethodologyCard
                    number="04"
                    title="No fabricated coverage"
                    description="RepoLens does not convert these structural checks into a percentage coverage score."
                  />
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-6">
                <div className="text-sm font-medium text-white">
                  Testing scope
                </div>

                <p className="mt-4 text-sm leading-7 text-white/40">
                  The current testing intelligence is structural.
                  It identifies missing relationships between
                  production code and tests, but it does not execute
                  the repository&apos;s test suite.
                </p>

                <div className="mt-6 space-y-3">
                  <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
                    <div className="text-xs text-white/65">
                      Currently covered
                    </div>

                    <div className="mt-2 text-xs leading-6 text-white/35">
                      Test references and direct test-counterpart
                      relationships.
                    </div>
                  </div>

                  <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
                    <div className="text-xs text-white/65">
                      Not established by this page
                    </div>

                    <div className="mt-2 text-xs leading-6 text-white/35">
                      Runtime test results, branch coverage,
                      mutation coverage, test quality, or behavioral
                      correctness.
                    </div>
                  </div>

                  <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
                    <div className="text-xs text-white/65">
                      Evidence policy
                    </div>

                    <div className="mt-2 text-xs leading-6 text-white/35">
                      Findings are shown only when supported by the
                      deterministic testing analysis.
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-10 border-t border-white/10 pt-6 text-xs text-white/25">
              RepoLens · Testing intelligence reconstructed from
              repository structure · No arbitrary coverage score
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}