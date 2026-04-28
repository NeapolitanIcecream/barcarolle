# Experiment Brief

## Goal

Validate whether a repository-specific benchmark predicts held-out repository work quality better than a general coding-agent benchmark.

The target outcome is a credible ranking reversal:

- ACUT A scores above ACUT B on `G_score`;
- ACUT A scores below ACUT B on `R_score`;
- ACUT A also performs worse than ACUT B on held-out `W_score`.

## Operating Constraints

- Do not build the full Barcarolle product.
- Keep artifacts small, reviewable, and auditable.
- Use disjoint worker ownership.
- Keep large workspaces, cloned repositories, caches, and logs out of Git.
- Do not use this Barcarolle repository as the target repository.
- ACUT execution uses only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL`; credential values must never be recorded.
- The executable experiment is budget-constrained by default: USD `$240` soft stop, USD `$300` hard cap, four core ACUTs, 6 `G_score` tasks, 8 `RBench` tasks, 6 `RWork` tasks, and one primary attempt per ACUT/task.
- Broad execution workers must not start until the LLM access contract and cost ledger gate are implemented.

## Phase 0 Output

Phase 0 should leave the coordinator with:

- a selected target repository candidate set;
- frozen or proposed ACUT manifests;
- an explicit general benchmark basis;
- an LLM access manifest and cost ledger gate;
- minimal schemas and runner/verifier tooling;
- enough status metadata to decide whether to start Phase 1 review and task-pack construction.
