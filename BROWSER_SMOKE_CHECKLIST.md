# RepoLens — Final Browser Smoke Checklist

Run after extracting the release on the demonstration machine.

1. Start FastAPI and confirm `/health` returns 200.
2. Start the Next.js frontend and open `/`.
3. Open Repository and confirm the demo `requests` analysis loads.
4. Open Architecture.
5. Select nodes at the top, bottom, left, and right of the graph.
6. Confirm each selected label remains outside the central `REPO` node and does not cover a dependency edge.
7. Test search, Trace Impact, and Reset View.
8. Open Dependencies and test selection/impact behavior.
9. Open Risks, Security, Testing, Evidence, Drift, Reports, and Evaluation.
10. Open AI Q&A and test a repository fact, an unsupported question, and an empty submission.
11. Refresh each major route directly.
12. Resize to desktop/laptop widths and confirm there is no clipping or horizontal overflow in the main content.
13. Stop FastAPI and confirm the frontend presents its controlled API/error state rather than crashing.
14. Start Ollama with `qwen2.5-coder:7b` and verify `/health/llm` becomes `ready` before demonstrating Q&A.
