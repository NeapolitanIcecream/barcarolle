# Phase 1 Autonomous Overnight Two-Repo Process

## Step 0 Preflight

Runbook:
`docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md`.

Recorded environment:

- branch: `codex/restart-benchmark-compiler`
- HEAD: `99bfab15f5507d5a75803a8830cfa2f4a290a7f8`
- generated at: `2026-05-22T15:44:16Z`
- Python: `python` command not available; `python3 --version` returned `Python 3.9.6`
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`
- codex: `codex-cli 0.133.0`
- kilo: `7.3.1`

Endpoint check:

- sourced `~/.zshrc` before checking
- `LLM_BASE_URL` present: yes
- `LLM_API_KEY` present: yes
- values printed: no

Frozen design check:

- second repo decision: `two_repo_future_holdout_design_frozen_ready_for_paid_validation`
- selected repos: `boltons`, `attrs`
- selected second repo: `attrs`
- two-repo preregistration status: `frozen`
- paid second-repo ACUT calls made: `false`
- predictive validity established: `false`
- planned attrs B_eval tasks: `attrs__hist__001`, `attrs__hist__003`, `attrs__hist__004`, `attrs__hist__008`
- planned attrs H_future tasks: `attrs__hist__012`, `attrs__hist__013`, `attrs__hist__023`, `attrs__hist__027`
- planned attrs cells: `8` B_eval, `8` H_future
- existing Boltons paid evidence: `8` B_eval scoreable cells, `8` H_future scoreable cells, `0` policy violations

Baseline validation:

- `git diff --check`: pass
- `uv run --project experiments/phase1_compiler pytest -q`: `65 passed in 0.36s`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools`: `74 passed in 2.14s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml`: `status=valid`

Worktree note:

- `docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md` was untracked at preflight start and is treated as user-provided input.

Initial branch selection:

The preflight evidence supports continuing toward Branch B, the paid gates path,
after the required local metadata consistency check. No paid calls were made in
Step 0.

## Step 1 Metadata Repair

The runbook's known issue was present:

- `phase1_second_repo_clean_supply_process.md` recorded attrs anchors scanned as `388`.
- `phase1_second_repo_clean_supply_candidate_inventory.json` and its Markdown report recorded anchors scanned as `0`.

Root cause:

- `certify-second-repo` rewrote the second-repo candidate inventory after local
  certification.
- That path did not pass mining anchors into `second_repo_inventory_payload`, so
  the helper replaced mining-stage anchor and first-filter counts with empty
  values.

Repair:

- Added a regression test for preserving prior mining counts during certification inventory rewrites.
- Updated `second_repo_inventory_payload` to preserve prior `anchors_scanned`
  and `first_filter_counts` when certification updates the inventory without
  rerunning mining.
- Updated `certify-second-repo` to read the existing candidate inventory and to
  pass candidates, contexts, certification rows, reviews, and prior mining
  counts into the rebuilt inventory.

Regenerated local artifacts without paid calls:

- `mine-second-repo --config experiments/phase1_compiler/configs/phase1_second_repo_clean_outcome_unseen_supply.yaml --repo-id attrs`
- `certify-second-repo --config experiments/phase1_compiler/configs/phase1_second_repo_clean_outcome_unseen_supply.yaml --repo-id attrs`

Post-repair counts:

- anchors scanned: `388`
- selected candidate rows: `48`
- source context rows: `48`
- local certification attempts: `48`
- local certification status counts: `certified=21`, `near_certified=27`
- promoted clean attrs candidates: `18`

No paid ACUT or paid LLM calls were made in Step 1.

## Step 2 Attrs Paid Entry Gate

Initial entry-gate preflight exposed a package-selection blocker:

- all four preflight commands returned `ready`, but package inspection selected
  the old Phase 0 matrix tasks because
  `phase1_two_repo_future_holdout_validation.yaml` did not expose frozen attrs
  tasks through runner-readable `splits`;
- the workspace runner also lacked support for loading
  `second_repo_clean_supply_overlay` packages from the attrs sidecar evidence.

Benchmark-side repair:

- added a regression test proving second-repo clean-overlay task ids can be
  selected by task id;
- added second-repo clean-supply overlay loading to
  `workspace_acut_run.py`;
- updated `phase1_two_repo_future_holdout_validation.yaml` with frozen attrs
  `splits`, the attrs clean-supply certified-task source, and
  `enabled_after_entry_gate` paid-call status.

Re-run preflight evidence:

| Prefix | Adapter | Status | Endpoint proof | Required env | Selected tasks | Missing |
| --- | --- | --- | --- | --- | ---: | ---: |
| `phase1_two_repo_future_holdout_attrs_b_eval_codex_preflight` | `codex_workspace` | `ready` | `codex_eligible` | `true` | `8` | `0` |
| `phase1_two_repo_future_holdout_attrs_b_eval_kilo_preflight` | `kilo_workspace` | `ready` | `kilo_eligible` | `true` | `8` | `0` |
| `phase1_two_repo_future_holdout_attrs_h_future_codex_preflight` | `codex_workspace` | `ready` | `codex_eligible` | `true` | `8` | `0` |
| `phase1_two_repo_future_holdout_attrs_h_future_kilo_preflight` | `kilo_workspace` | `ready` | `kilo_eligible` | `true` | `8` | `0` |

Frozen attrs tasks selected by package inspection:

- B_eval: `attrs__hist__001`, `attrs__hist__003`, `attrs__hist__004`, `attrs__hist__008`
- H_future: `attrs__hist__012`, `attrs__hist__013`, `attrs__hist__023`, `attrs__hist__027`

Cost and prior-run gate:

- current cumulative observed-or-conservative spend: `$46.99`
- planned attrs paid cells: `16`
- conservative planned attrs increment: `$8.00`
- projected cumulative observed-or-conservative spend: `$54.99`, below the `$80.00` unattended stop cap
- projected overnight increment: `$8.00`, below the `$35.00` hard cap
- no prior paid score table or submission files exist for
  `phase1_two_repo_future_holdout_attrs_b_eval` or
  `phase1_two_repo_future_holdout_attrs_h_future`
- paid parallelism remains disabled; planned paid cells will run sequentially

Entry-gate decision:

Proceed to the attrs B_eval paid batch if scoped tests and `git diff --check`
pass. No paid ACUT or paid LLM calls were made in Step 2.

## Step 3 Paid Attrs B_eval

Executed paid B_eval cells sequentially:

- `codex_workspace`: `attrs__hist__001`, `attrs__hist__003`, `attrs__hist__004`, `attrs__hist__008`
- `kilo_workspace`: `attrs__hist__001`, `attrs__hist__003`, `attrs__hist__004`, `attrs__hist__008`

Score table summary:

- terminal cells: `8/8`
- scoreable cells: `8/8`
- verified pass: `7`
- verified fail: `1`
- policy violations: `0`
- harness errors: `0`
- adapter cells: `4` Codex, `4` Kilo

Cost and usage:

- usage observed cells: `8/8`
- usage observed rate: `1.0`
- B_eval observed-or-conservative estimated cost: `$6.4833018`
- conservative fallback for missing usage: `$0`
- cumulative observed-or-conservative estimate after import: `$53.4708656`
- cumulative usage observed rate after import: `0.9524`

Hidden oracle leak check:

- no `*_hidden_tests.patch` files were found under B_eval solver workspaces
- raw artifacts and workspaces remain under ignored paths

## Step 4 H_future Continuation Decision

The B_eval gate passed:

- at least `6/8` cells are scoreable: yes, `8/8`
- policy violations are `0`: yes
- usage/cost is observed or conservatively bounded: yes
- cumulative spend remains below the `$80.00` unattended stop cap: yes
- adapter failures are not recurring harness errors: yes

Decision: continue to the paid attrs H_future batch.

## Step 5 Paid Attrs H_future

Executed paid H_future cells sequentially:

- `codex_workspace`: `attrs__hist__012`, `attrs__hist__013`, `attrs__hist__023`, `attrs__hist__027`
- `kilo_workspace`: `attrs__hist__012`, `attrs__hist__013`, `attrs__hist__023`, `attrs__hist__027`

Score table summary:

- terminal cells: `8/8`
- scoreable cells: `7/8`
- verified pass: `1`
- verified fail: `6`
- policy violations: `1`
- harness errors: `1`
- adapter cells: `4` Codex, `4` Kilo

Policy finding:

- `kilo_workspace` on `attrs__hist__027` was recorded as
  `policy_violation` with harness error
  `submission_edited_out_of_scope_paths`.
- The changed path was `src/attr/_make.py`.

Cost and usage:

- usage observed cells: `8/8`
- usage observed rate: `1.0`
- H_future observed-or-conservative estimated cost: `$8.7120804`
- cumulative observed-or-conservative estimate after import: `$62.182946`
- cumulative usage observed rate after import: `0.9548`

Hidden oracle leak check:

- no `*_hidden_tests.patch` files were found under H_future solver workspaces
- raw artifacts and workspaces remain under ignored paths

Runbook implication:

The paid attrs H_future batch completed, but the policy violation means the
two-repo predictive-validity threshold cannot be marked established.

## Step 6 Two-Repo Metrics

Extended `phase1_future_holdout.py` with a `two-repo-score` command so the
frozen two-repo design can be scored from the Boltons paid prefixes and the attrs
paid prefixes.

Metrics inputs:

- Boltons B_eval: `phase1_future_holdout_b_eval`
- Boltons H_future: `phase1_future_holdout_h_future`
- attrs B_eval: `phase1_two_repo_future_holdout_attrs_b_eval`
- attrs H_future: `phase1_two_repo_future_holdout_attrs_h_future`

Generated artifacts:

- `experiments/phase1_compiler/results/phase1_two_repo_future_holdout_prediction_metrics.json`
- `experiments/phase1_compiler/reports/phase1_two_repo_future_holdout_prediction_metrics.md`
- `experiments/phase1_compiler/results/phase1_two_repo_future_holdout_decision.json`
- `experiments/phase1_compiler/reports/phase1_two_repo_future_holdout_decision.md`

Two-repo score summary:

- selected repos: `boltons`, `attrs`
- B_eval scoreable cells: `16`
- H_future scoreable cells: `15`
- policy violations: `1`
- non-scoreable cells: `1`
- pooled MAE across repo/adapter cells: `0.479167`
- frozen design match: `matched`
- incremental observed-or-conservative cost across the four validation prefixes:
  `$24.5357028`

Threshold checks:

- selected repos at least `2`: pass
- H_future scoreable cells at least `12`: pass
- policy violations equal `0`: fail
- holdout tuning did not occur: pass
- metrics computed from frozen design: pass

Decision:

- primary decision:
  `two_repo_paid_validation_complete_insufficient_evidence`
- predictive validity established: `false`
- blocker: `policy_violation_count_exceeds_acceptance_gate`
