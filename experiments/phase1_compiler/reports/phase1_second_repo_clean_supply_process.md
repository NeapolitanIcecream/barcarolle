# Phase 1 Second-Repo Clean Supply Process

Status: in progress.

Generated: 2026-05-22T12:17:29Z.

## Step 0 Preflight

- Branch: `codex/restart-benchmark-compiler`
- Starting HEAD: `00ff5c0aab6eaa39021bac1a3ff6e98db79524cc`
- Python: `Python 3.11.13`
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`
- Paid ACUT calls allowed: `false`
- Direct paid LLM calls allowed: `false`
- Paid ACUT calls made: `false`
- Direct paid LLM calls made: `false`
- Predictive validity established: `false`

Worktree preflight state:

- `git diff --check` passed.
- `git status --short --branch` showed only the untracked runbook file supplied for this execution.
- The branch was ahead of origin by `159` commits at preflight.

Boltons clean future-holdout pilot matched the runbook:

- decision: `boltons_clean_future_holdout_pilot_complete_insufficient_sample`
- selected repo: `boltons`
- B_eval scoreable cells: `8`
- H_future scoreable cells: `8`
- policy violations: `0`
- blockers: `predictive_validity_min_target_repos_not_met`, `predictive_validity_min_holdout_scoreable_cells_not_met`
- recommended next runbook: `mine_second_repo_clean_outcome_unseen_supply_for_two_repo_validation`

Current Phase 1 closeout matched the required next path:

- future-holdout sidecar evidence: `available_as_future_holdout_sidecar_evidence`
- clean future-holdout scale-up status: `boltons_clean_future_holdout_pilot_complete`
- next runbook recommendation: `mine_second_repo_clean_outcome_unseen_supply_for_two_repo_validation`
- predictive validity established: `false`

Baseline checks passed:

- `uv run --project experiments/phase1_compiler pytest -q` -> `57 passed in 0.36s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`

No paid calls have been made in this runbook.

## Step 1 Configure Second-Repo Mining

Created `experiments/phase1_compiler/configs/phase1_second_repo_clean_outcome_unseen_supply.yaml`.

Config properties:

- claim scope: `second_repo_clean_supply_not_predictive_validation`
- predictive validity established: `false`
- paid ACUT calls: disabled
- paid LLM calls: disabled
- primary candidate repo: `attrs`
- fallback candidate repo: `toolz`
- minimum clean split: `B_eval >= 2`, `H_future >= 2`
- preferred clean split: `B_eval >= 4`, `H_future >= 4`
- attrs local repo path: `experiments/phase0_headroom/external_repos/attrs`
- attrs candidate prefix: `attrs_clean_outcome_unseen_supply`
- prior Boltons future-holdout decision: `experiments/phase1_compiler/results/phase1_future_holdout_decision.json`
- prior Boltons clean overlay: `experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_overlay.json`

Promotion policy requires outcome-unseen tasks, target-commit-unseen tasks,
non-leaky public problem context, local certification gates, oracle alignment,
and future-holdout cutoff feasibility. It rejects commit-message-only,
solution-leaky, project-heavy ambiguous, docs-only, and config-only candidates.

Output paths are namespaced to second-repo sidecar artifacts and do not mutate
canonical Boltons release or hardening outputs.

## Step 2 Prepare Local Repo And Candidate Anchors

Confirmed the attrs clone path is ignored by Git:

- `git check-ignore -v experiments/phase0_headroom/external_repos/attrs` -> `.gitignore:224:experiments/phase0_headroom/external_repos/`

Cloned and fetched attrs under
`experiments/phase0_headroom/external_repos/attrs`. The clone remains under an
ignored external-repo path and is not committed.

Added second-repo commands to
`experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py`
and focused policy tests in
`experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py`.

Validation:

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py` -> `12 passed in 0.02s`

Ran:

- `phase1_clean_outcome_unseen_supply_mining.py mine-second-repo --config experiments/phase1_compiler/configs/phase1_second_repo_clean_outcome_unseen_supply.yaml --repo-id attrs`

Generated:

- `experiments/phase0_headroom/candidate_sources/attrs_clean_outcome_unseen_supply_candidates.jsonl`
- `experiments/phase0_headroom/candidate_sources/attrs_clean_outcome_unseen_supply_source_context.jsonl`
- `experiments/phase1_compiler/results/phase1_second_repo_clean_supply_candidate_inventory.json`
- `experiments/phase1_compiler/reports/phase1_second_repo_clean_supply_candidate_inventory.md`

Mining result:

- anchors scanned: `388`
- selected candidate rows: `48`
- source context rows: `48`
- source context status counts: `non_leaky_problem_context=43`, `commit_message_only_source=5`
- first filter counts: `candidate=48`, `rejected=340`
- paid ACUT calls made: `false`
- paid LLM calls made: `false`

The source-context writer prefers linked issue reports over PR bodies when PR
metadata references a public issue, and stores only sanitized summaries rather
than raw GitHub API responses.

## Step 3 Certify And Review Candidates

Ran:

- `phase1_clean_outcome_unseen_supply_mining.py certify-second-repo --config experiments/phase1_compiler/configs/phase1_second_repo_clean_outcome_unseen_supply.yaml --repo-id attrs`

Generated:

- `experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_certified_tasks.jsonl`
- `experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_review_records.jsonl`
- `experiments/phase1_compiler/results/phase1_second_repo_clean_supply_candidate_inventory.json`
- `experiments/phase1_compiler/results/phase1_second_repo_clean_supply_review.json`
- `experiments/phase1_compiler/reports/phase1_second_repo_clean_supply_candidate_inventory.md`
- `experiments/phase1_compiler/reports/phase1_second_repo_clean_supply_review.md`

Review result:

- local certification attempts: `48`
- local certification status counts: `certified=21`, `near_certified=27`
- promoted clean attrs candidates: `18`
- rejected candidates: `30`
- promoted task ids: `attrs__hist__001`, `attrs__hist__003`, `attrs__hist__004`, `attrs__hist__008`, `attrs__hist__009`, `attrs__hist__010`, `attrs__hist__012`, `attrs__hist__013`, `attrs__hist__023`, `attrs__hist__027`, `attrs__hist__032`, `attrs__hist__033`, `attrs__hist__035`, `attrs__hist__036`, `attrs__hist__039`, `attrs__hist__041`, `attrs__hist__045`, `attrs__hist__047`
- rejection blocker counts include `local_certification_gate_failed:reference_pass=21`, `solution_exposure_risk=7`, `scope_context_project_heavy_or_ambiguous=5`, `commit_message_only_source=5`
- paid ACUT calls made: `false`
- paid LLM calls made: `false`

Promoted rows have local certification status `certified`, non-leaky public
problem context, clean overlay gates passing, outcome-unseen task ids, and
target-commit-unseen status. Review records list all rejected candidates and
blockers.
