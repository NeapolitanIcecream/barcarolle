# Codex Kilo Workspace Analysis

The Codex/Kilo cross-harness comparison is not scoreable yet. Both candidate harnesses are blocked at endpoint proof, so the experiment stopped before smoke and full matrix execution.

The main decision is operational rather than statistical: no `same_model_cross_harness` estimate should be computed from this run. The adapter code can isolate multiple harnesses, but no candidate currently has a proven command template that satisfies the endpoint and credential constraints.

Required next evidence:

- A successful non-scoreable Codex proof using `LLM_BASE_URL` and `LLM_API_KEY`, without local subscription auth.
- A successful non-scoreable Kilo proof using `LLM_BASE_URL` and `LLM_API_KEY`, without provider credentials from outside those variables.
- Only after both proofs pass should the four-cell smoke matrix run.
