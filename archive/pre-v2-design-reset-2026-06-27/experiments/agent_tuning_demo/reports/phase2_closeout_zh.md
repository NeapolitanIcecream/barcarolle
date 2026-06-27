# Agent Tuning Phase 2 closeout

Terminal state: `phase2_success_no_holdout_regression`.

- Paid cells: `20`.
- Estimated cost: `$1.3267749`.
- Preflight passed: `True`.
- Optimizer/proposer: `gepa_optimize_anything_custom_local_proposer`.
- Target Agent/surface: `kilo_gpt_5_4_mini` / `repo_AGENTS_md`.
- Candidate artifact count: `2`.
- Selection-dev paired net wins: `0`.
- Holdout paired net wins: `0`.
- Selection-dev matrix: baseline `1/4`, tuned `1/4`, invalid `0/0`.
- Holdout matrix: baseline `5/6`, tuned `5/6`, invalid `0/0`.
- Cost/latency: Selection-dev baseline `$0.23297655` median `65.2s`, tuned `$0.47956725` median `72.246s`; Holdout baseline `$0.3224709` median `32.081s`, tuned `$0.2917602` median `34.701s`.
- Tests: agent-tuning `11 passed`; phase0 adapter/workspace `30 passed`; `git diff --check` pass.
- Hygiene: tracked artifact scan no hits; final staged hygiene scan recorded before commit.

Supported claims:

- A repo-local Kilo `AGENTS.md` appendix can change real Kilo CLI action behavior in the controlled preflight.
- Barcarolle can export Selection-train feedback without Holdout IDs or raw transcripts.
- Barcarolle can generate, hash-freeze, inject, and validate one deployable repo-local text artifact before/after on held-out tasks.

Unsupported claims:

- tuned improvement;
- full predictive validity;
- cross-repo generalization;
- model fine-tuning;
- full opaque Codex/Kilo Agent tuning;
- GEPA/Phoenix superiority;
- statistical significance;
- production-ready Agent tuning system.

Commits made before this closeout commit:

- `6b2d5c2b` Add phase2 artifact tuning helpers
- `fdb06563` Freeze phase2 tuning protocol
- `62ebb53c` Prove phase2 action-level artifact preflight
- `cd957b18` Export phase2 tuning feedback labels
- `200bf911` Evaluate phase2 candidate on selection dev
- `0267c32d` Freeze phase2 chosen artifact
- `4f45394a` Run phase2 frozen holdout validation

See the JSON closeout for full matrices, claims, and canonical artifact links.
