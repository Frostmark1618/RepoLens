const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type RepositoryOverview = {
  metadata: {
    repository_name: string;
    repository_path: string;
    total_files: number;
    python_files: number;
  };

  relevant_file_count: number;
  python_file_count: number;
  production_module_count: number;
  dependency_edge_count: number;

  architecture: {
    node_count: number;
    edge_count: number;
    layer_summary: Record<string, number>;
    layer_percentages: Record<string, number>;
  };

  risk: {
    signal_count: number;
  };
};

export type RepositoryAnalysis = {
  metadata: Record<string, unknown>;
  relevant_files: unknown;
  file_tree: unknown;
  python_structure: unknown;
  dependency_graph: unknown;
  architecture: unknown;

  risks: {
    risk_signals?: RiskSignal[];
    [key: string]: unknown;
  };

  risk_intelligence?: unknown;
  risk_signals?: RiskSignal[];
};

export type RiskSignal = {
  signal?: string;
  category?: string;
  severity?: string;
  reason?: string;
  file?: string;
  module_name?: string;
  evidence?: unknown;

  [key: string]: unknown;
};



export type RepositoryDrift = {
  status: "ready" | "unconfigured";
  message: string;
  baseline: { path?: string; created_at?: string } | null;
  current: { path?: string; created_at?: string } | null;
  drift: {
    has_drift: boolean;
    module_drift: { added_modules: string[]; removed_modules: string[]; unchanged_modules: string[]; added_count: number; removed_count: number; unchanged_count: number };
    dependency_drift: { changed_modules: Array<{ file: string; added_dependencies: string[]; removed_dependencies: string[] }>; changed_count: number };
    layer_drift: { changed_modules: Array<{ file: string; baseline_layer?: string; current_layer?: string }>; changed_count: number };
  } | null;
};

// ---------------------------------------------------------
// Repository Q&A Types
// ---------------------------------------------------------

export type RepositoryEvidence = {
  evidence_type?: string;
  file?: string;
  start_line?: number;
  end_line?: number;
  content?: string;
  retrieval_score?: number;
  retrieval_role?: string;
  context_role?: string;
  [key: string]: unknown;
};

export type RepositoryClaim = {
  text?: string;
  status?: string;
  evidence?: RepositoryEvidence[];
  [key: string]: unknown;
};

export type ClaimCoverage = {
  claim_count: number;
  supported_claims: number;
  unsupported_claims: number;
  coverage: number;
};

export type RepositoryAnswer = {
  answer: string;
  status: string;

  evidence: RepositoryEvidence[];

  claims: RepositoryClaim[];

  supporting_evidence: RepositoryEvidence[];

  architecture_evidence: RepositoryEvidence[];

  retrieval_counts: {
    primary?: number;
    supporting?: number;
    architecture?: number;
    metadata?: number;
    [key: string]: unknown;
  };

  claim_coverage?: ClaimCoverage | null;
};


// ---------------------------------------------------------
// Generic GET API
// ---------------------------------------------------------

async function fetchApi<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(
      `RepoLens API request failed: ${response.status} ${response.statusText}`,
    );
  }

  return response.json() as Promise<T>;
}


// ---------------------------------------------------------
// Repository Overview
// ---------------------------------------------------------

export function getRepositoryOverview(): Promise<RepositoryOverview> {
  return fetchApi<RepositoryOverview>("/api/repository/overview");
}


// ---------------------------------------------------------
// Repository Analysis
// ---------------------------------------------------------

export function getRepositoryAnalysis(): Promise<RepositoryAnalysis> {
  return fetchApi<RepositoryAnalysis>("/api/repository/analysis");
}


// ---------------------------------------------------------
// Repository Q&A
// ---------------------------------------------------------

export async function askRepository(
  query: string,
): Promise<RepositoryAnswer> {
  const cleanedQuery = query.trim();

  if (!cleanedQuery) {
    throw new Error("Repository question cannot be empty.");
  }

  const response = await fetch(
    `${API_BASE_URL}/api/repository/ask`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: cleanedQuery,
      }),
      cache: "no-store",
    },
  );

  if (!response.ok) {
    let detail = "";

    try {
      const errorBody = (await response.json()) as {
        detail?: string;
      };

      detail =
        typeof errorBody.detail === "string"
          ? errorBody.detail
          : "";
    } catch {
      // Keep the generic HTTP error below.
    }

    throw new Error(
      detail ||
        `RepoLens Q&A request failed: ${response.status} ${response.statusText}`,
    );
  }

  return response.json() as Promise<RepositoryAnswer>;
}
export async function getRepositoryDrift(): Promise<RepositoryDrift> {
  return fetchApi<RepositoryDrift>("/api/repository/drift");
}

