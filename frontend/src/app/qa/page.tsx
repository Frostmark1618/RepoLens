"use client";

import { FormEvent, useState } from "react";
import RepoLensSidebar from "@/components/RepoLensSidebar";

import {
  askRepository,
  type RepositoryAnswer,
  type RepositoryClaim,
  type RepositoryEvidence,
} from "@/lib/api";

function normalizePath(value?: string): string {
  return (value ?? "").replaceAll("\\", "/");
}

function formatEvidenceLocation(evidence: RepositoryEvidence): string {
  const file = normalizePath(evidence.file);

  if (
    typeof evidence.start_line === "number" &&
    typeof evidence.end_line === "number"
  ) {
    return `${file} · lines ${evidence.start_line}-${evidence.end_line}`;
  }

  return file || "Repository location unavailable";
}

function EvidenceCard({
  evidence,
}: {
  evidence: RepositoryEvidence;
}) {
  return (
    <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="font-mono text-xs text-white/65 break-all">
            {formatEvidenceLocation(evidence)}
          </div>

          {evidence.evidence_type && (
            <div className="mt-2 text-[9px] uppercase tracking-widest text-white/25">
              {evidence.evidence_type}
            </div>
          )}
        </div>

        {evidence.retrieval_role && (
          <span className="shrink-0 rounded-full border border-white/10 px-2.5 py-1 text-[9px] uppercase tracking-widest text-white/30">
            {evidence.retrieval_role}
          </span>
        )}
      </div>

      {evidence.evidence_type === "repository_metadata" &&
        (typeof evidence.label === "string" ||
          typeof evidence.value === "number") && (
          <div className="mt-3 text-xs text-white/45">
            {typeof evidence.label === "string" ? evidence.label : "Repository fact"}:{" "}
            {typeof evidence.value === "number" ? evidence.value : "—"}
          </div>
        )}

      {typeof evidence.content === "string" &&
        evidence.content.trim() && (
          <pre className="mt-4 max-h-52 overflow-auto rounded-lg border border-white/8 bg-black/30 p-3 font-mono text-[11px] leading-5 text-white/35 whitespace-pre-wrap">
            {evidence.content}
          </pre>
        )}
    </div>
  );
}

function ClaimCard({
  claim,
  index,
}: {
  claim: RepositoryClaim;
  index: number;
}) {
  const claimEvidence = Array.isArray(claim.evidence)
    ? claim.evidence
    : [];

  const claimStatus = claim.status ?? "unknown";

  return (
    <div className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-5">
      <div className="flex items-start justify-between gap-5">
        <div className="flex min-w-0 items-start gap-3">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-white/10 text-[10px] font-mono text-white/35">
            {String(index + 1).padStart(2, "0")}
          </div>

          <div className="text-sm leading-6 text-white/65">
            {claim.text ?? "Claim text unavailable."}
          </div>
        </div>

        <span className="shrink-0 rounded-full border border-white/10 px-2.5 py-1 text-[9px] uppercase tracking-widest text-white/30">
          {claimStatus}
        </span>
      </div>

      <div className="mt-5">
        <div className="mb-3 text-[9px] uppercase tracking-[0.18em] text-white/25">
          Claim evidence
        </div>

        {claimEvidence.length === 0 ? (
          <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4 text-xs text-white/30">
            No evidence was attributed to this claim.
          </div>
        ) : (
          <div className="space-y-2">
            {claimEvidence.map((evidence, evidenceIndex) => (
              <EvidenceCard
                key={`${evidence.file}-${evidence.start_line}-${evidence.end_line}-${evidenceIndex}`}
                evidence={evidence}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function QAPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<RepositoryAnswer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const cleanedQuery = query.trim();

    if (!cleanedQuery) {
      setError("Enter a repository question first.");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await askRepository(cleanedQuery);

      setResult(response);
    } catch (err) {
      setResult(null);

      setError(
        err instanceof Error
          ? err.message
          : "Repository Q&A failed.",
      );
    } finally {
      setLoading(false);
    }
  }

  const coverage = result?.claim_coverage;

  return (
    <main className="min-h-screen repolens-page repolens-route-qa bg-[#050505] text-white">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <RepoLensSidebar />

        <section className="min-w-0 flex-1">
          <header className="flex h-16 items-center justify-between border-b border-white/10 px-6 lg:px-10">
            <div className="text-xs text-white/30">
              Repository / AI Q&A
            </div>

            <span className="rounded-full border border-white/10 px-3 py-1.5 text-[10px] uppercase tracking-widest text-white/35">
              Evidence grounded
            </span>
          </header>

          <div className="mx-auto max-w-[1500px] px-6 py-10 lg:px-10">
            <div className="max-w-4xl">
              <div className="text-xs uppercase tracking-[0.2em] text-white/30">
                Repository intelligence
              </div>

              <h1 className="mt-5 text-5xl font-semibold tracking-[-0.045em] text-white lg:text-7xl">
                Ask the
                <span className="block text-white/30">
                  codebase.
                </span>
              </h1>

              <p className="mt-6 max-w-3xl text-base leading-7 text-white/40">
                Ask questions about the analyzed repository and receive
                answers grounded in retrieved code evidence, with
                claim-level attribution.
              </p>
            </div>

            <form
              onSubmit={handleSubmit}
              className="mt-12 rounded-2xl border border-white/10 bg-[#0b0b0b] p-5"
            >
              <div className="text-[10px] uppercase tracking-[0.18em] text-white/25">
                Repository question
              </div>

              <textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Example: How does the repository prepare and send a request?"
                rows={4}
                maxLength={2000}
                disabled={loading}
                className="mt-4 w-full resize-none rounded-xl border border-white/10 bg-black/30 px-4 py-4 text-sm leading-6 text-white outline-none placeholder:text-white/20 focus:border-white/20 disabled:opacity-50"
              />

              <div className="mt-4 flex items-center justify-between gap-4">
                <div className="text-[10px] text-white/20">
                  {query.length}/2000
                </div>

                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="rounded-xl border border-white/15 bg-white px-5 py-3 text-xs font-medium text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-30"
                >
                  {loading ? "Analyzing…" : "Ask RepoLens"}
                </button>
              </div>
            </form>

            {error && (
              <div className="mt-6 rounded-2xl border border-red-400/20 bg-red-400/5 p-5">
                <div className="text-sm font-medium text-red-300">
                  Q&A unavailable
                </div>

                <p className="mt-2 text-sm leading-6 text-white/40">
                  {error}
                </p>
              </div>
            )}

            {result && (
              <div className="mt-7 space-y-7">
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <div className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-5">
                    <div className="text-[10px] uppercase tracking-[0.18em] text-white/25">
                      Status
                    </div>

                    <div className="mt-4 text-2xl font-semibold text-white">
                      {result.status}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-5">
                    <div className="text-[10px] uppercase tracking-[0.18em] text-white/25">
                      Primary evidence
                    </div>

                    <div className="mt-4 text-2xl font-semibold text-white">
                      {result.retrieval_counts.primary ?? result.evidence.length}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-5">
                    <div className="text-[10px] uppercase tracking-[0.18em] text-white/25">
                      Claims
                    </div>

                    <div className="mt-4 text-2xl font-semibold text-white">
                      {coverage?.claim_count ?? result.claims.length}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-5">
                    <div className="text-[10px] uppercase tracking-[0.18em] text-white/25">
                      Claim coverage
                    </div>

                    <div className="mt-4 text-2xl font-semibold text-white">
                      {coverage
                        ? `${Math.round(coverage.coverage * 100)}%`
                        : "—"}
                    </div>
                  </div>
                </div>

                <section className="rounded-2xl border border-white/10 bg-[#0b0b0b]">
                  <div className="border-b border-white/10 px-6 py-5">
                    <div className="text-sm font-medium text-white">
                      Answer
                    </div>

                    <div className="mt-1 text-xs text-white/30">
                      Generated from repository evidence
                    </div>
                  </div>

                  <div className="p-6">
                    <p className="max-w-5xl text-base leading-8 text-white/70">
                      {result.answer}
                    </p>
                  </div>
                </section>

                <section className="rounded-2xl border border-white/10 bg-[#0b0b0b]">
                  <div className="border-b border-white/10 px-6 py-5">
                    <div className="text-sm font-medium text-white">
                      Primary evidence
                    </div>

                    <div className="mt-1 text-xs text-white/30">
                      Repository locations used by the Q&A pipeline
                    </div>
                  </div>

                  <div className="space-y-3 p-6">
                    {result.evidence.length === 0 ? (
                      <div className="rounded-xl border border-white/8 bg-white/[0.02] p-5 text-sm text-white/30">
                        No primary evidence was returned.
                      </div>
                    ) : (
                      result.evidence.map((evidence, index) => (
                        <EvidenceCard
                          key={`${evidence.file}-${evidence.start_line}-${evidence.end_line}-${index}`}
                          evidence={evidence}
                        />
                      ))
                    )}
                  </div>
                </section>

                <section>
                  <div className="mb-4">
                    <div className="text-sm font-medium text-white">
                      Claim → Evidence
                    </div>

                    <div className="mt-1 text-xs text-white/30">
                      Each generated claim is checked against repository
                      evidence.
                    </div>
                  </div>

                  {result.claims.length === 0 ? (
                    <div className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-6 text-sm text-white/30">
                      No claims were generated.
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {result.claims.map((claim, index) => (
                        <ClaimCard
                          key={`${claim.text}-${index}`}
                          claim={claim}
                          index={index}
                        />
                      ))}
                    </div>
                  )}
                </section>

                {result.supporting_evidence.length > 0 && (
                  <section className="rounded-2xl border border-white/10 bg-[#0b0b0b]">
                    <div className="border-b border-white/10 px-6 py-5">
                      <div className="text-sm font-medium text-white">
                        Supporting context
                      </div>

                      <div className="mt-1 text-xs text-white/30">
                        Additional retrieved context retained for auditability.
                      </div>
                    </div>

                    <div className="space-y-3 p-6">
                      {result.supporting_evidence.map(
                        (evidence, index) => (
                          <EvidenceCard
                            key={`${evidence.file}-${evidence.start_line}-${evidence.end_line}-${index}`}
                            evidence={evidence}
                          />
                        ),
                      )}
                    </div>
                  </section>
                )}

                {coverage && (
                  <section className="rounded-2xl border border-white/10 bg-[#0b0b0b] p-6">
                    <div className="text-sm font-medium text-white">
                      Evidence verification
                    </div>

                    <div className="mt-5 grid gap-4 md:grid-cols-3">
                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-white/25">
                          Supported
                        </div>

                        <div className="mt-2 text-2xl font-semibold text-white">
                          {coverage.supported_claims}
                        </div>
                      </div>

                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-white/25">
                          Unsupported
                        </div>

                        <div className="mt-2 text-2xl font-semibold text-white">
                          {coverage.unsupported_claims}
                        </div>
                      </div>

                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-white/25">
                          Coverage
                        </div>

                        <div className="mt-2 text-2xl font-semibold text-white">
                          {Math.round(coverage.coverage * 100)}%
                        </div>
                      </div>
                    </div>
                  </section>
                )}
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}