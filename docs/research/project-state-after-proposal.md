# Project State After Proposal

Status: canonical handoff snapshot, 2026-06-04.

This document records the state Barcarolle should have on main after the
proposal-stage work is complete. It is the single starting point for future
development and experiments.

## Project Position

Barcarolle is a target-repository benchmark compiler for coding-agent
evaluation and tuning.

It is not:

- an Agent harness;
- a general SWE task factory;
- a public leaderboard;
- an Agent License product by itself.

The core project is task selection, certification, release construction,
calibration, and feedback for a specific repository and Agent family. Task
generation is supply infrastructure. Agent License and Agent Tuning are
downstream product directions.

## Agent Boundary

An Agent means the full tested configuration:

```text
model + harness + prompt/skills + tools + retrieval + runtime policy + budget
```

Older reports use ACUT (`Agent Configuration Under Test`) for the same idea.

Barcarolle does not implement the Agent's internal harness. It prepares a clean
solver workspace, provides solver-visible task material, invokes the configured
Agent harness, captures the final Git diff, replays that diff in a fresh
verifier workspace, injects private oracle material only there, and records
sanitized status, cost, latency, and failure labels.

## What We Know

The workspace Agent protocol works well enough for pilot evidence:

- the three-repo paid validation ran `120` planned cells, completed `120`, and
  had `120` scoreable cells with endpoint compliance and no policy violations;
- the observed/conservative cost for that pilot was `$51.267333`;
- the primary conservative design was `repo_stratified`, with primary gap `0.1`
  under the preregistered `<= 0.15` pilot threshold.

Task selection matters:

- the old weighted target-profile design failed the paid pilot: `44` scoreable
  cells, gaps `0.3148` for attrs and `0.7481` for boltons, while simple
  baselines were much better;
- this is evidence that a bad selector can mislead, not evidence that a new
  selector is already solved.

There is traction for selection optimization:

- in a 1000-seed retrospective same-budget random comparison, the
  `coverage_constrained_unweighted` candidate beat or tied random samples on
  overall MAE in `93.4%` of samples;
- against the best simple baseline envelope, the same candidate is only
  slightly better overall (`0.209` MAE versus `0.2149`) and loses on several
  adapter, repository, and window slices.

The current evidence supports continued work and proposal traction. It does not
prove predictive validity.

## What We Do Not Claim

Barcarolle has not established that its benchmark releases predict future Agent
performance better than simple baselines.

Do not claim:

- predictive validity is proven;
- the current selector is generally superior;
- public benchmark rank predicts target-repo future work;
- adapter differences are model-only effects;
- task generators alone solve the repo-specific benchmark problem.

## Evidence Map

| Evidence | Path | Supports |
| --- | --- | --- |
| Final proposal report | `docs/research/barcarolle-proposal-report-v5.md` | Reader-facing project claim and product route. |
| Evidence manifest | `experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md` | Audit index for proposal evidence. |
| Research inputs and related work reference | `docs/research/research-inputs-and-related-work-reference.md` | Condensed May research-input synthesis, related-work positioning, source-adapter policy, and external-review constraints. |
| Weighted pilot | `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md` | Bad selection can mislead; old weighted design is not mainline. |
| Local algorithm bakeoff | `experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md` | Keep simple stratified reporting; local candidate not paid-ready. |
| Three-repo paid validation | `experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md` | Workspace protocol and conservative pilot feasibility. |
| Random baseline distribution | `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md` | Retrospective traction versus random same-budget samples. |
| Baseline envelope | `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md` | Candidate fragility versus best simple baselines. |
| Validation hardening | `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md` | Future claim gates, adapter handling, and candidate policy. |
| Task supply bakeoff | `experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md` | Internal repo-history generator remains useful supply infrastructure. |
| Source-context repair | `experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md` | LLM-assisted statement/source repair can be used under provenance and review controls. |

## Evidence Data Map

The repository retains the data needed to audit the proposal at the score-table
and metric level. It does not retain raw Agent transcripts, raw prompts, raw
completions, solver workspaces, verifier workspaces, cloned target
repositories, raw hidden-oracle streams, standalone process closeout logs, or
proposal/deck preflight traces. Some compact gate and package-inspection
metadata files remain where retained tools or reports use them for
reproducibility.

Primary three-repo paid validation:

- `experiments/phase1_compiler/results/phase1_three_repo_paid_validation_score_tables_manifest.json`
  records `120` completed cells and `120` scoreable cells.
- The manifest points to `10` retained score tables in
  `experiments/phase0_headroom/results/phase1_three_repo_paid_validation_*_score_table.csv`.
- Companion matrix, metrics, and cost-summary files are retained under the same
  `experiments/phase0_headroom/results/phase1_three_repo_paid_validation_*`
  prefixes.
- Aggregate metrics are retained in
  `experiments/phase1_compiler/results/phase1_three_repo_paid_validation_metrics.json`.

Three-repo diagnostics and adapter accounting:

- `experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_result_cube.{json,csv}`
- `experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_adapter_effects.json`
- `experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_three_repo_summary.{json,csv}`
- `experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_cost_latency_summary.json`

Supplementary paid cells:

- `experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_combined_score_tables_manifest.json`
- retained `phase1_blocked_split_missing_cell_supplement_paid_execution_*`
  score tables, matrices, metrics, and cost summaries under
  `experiments/phase0_headroom/results/`

Weighted-design pilot:

- `experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_score_table.csv`
- `experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_matrix.json`
- `experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_metrics.json`
- `experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_cost_summary.json`

Selection and baseline evidence:

- `experiments/phase1_compiler/results/phase1_proposal_evidence_package_random_baseline_distribution.json`
- `experiments/phase1_compiler/results/phase1_proposal_evidence_package_baseline_envelope.json`
- `experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_*`

Usage and cost accounting:

- `experiments/phase0_headroom/results/workspace_usage_ledger.jsonl` is a
  sanitized usage ledger used by follow-up analyses.
- It is retained because several analysis tools and reports depend on it. It is
  not a raw Agent transcript.

Statement generation references:

- `experiments/phase1_compiler/results/phase1_diff_assisted_regenerated_statements.jsonl`
- `experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_generated_statements.jsonl`
- `experiments/phase1_compiler/results/phase1_canonical_regenerated_statements.jsonl`

These JSONL files are retained as sanitized solver-facing statement examples
for future task-statement generator and QA work. They are not raw prompts,
completions, diffs, paid outcomes, or transcripts.

## Algorithm State

The current conservative reporting mainline is repo-stratified or simple
stratified baselines.

The old metadata-weighted target-profile design is diagnostic only. It should
not be promoted to a primary design.

Candidate selectors remain open research. Useful directions include:

- coverage-constrained unweighted selection;
- blocked and stratified variants;
- temporal recency baselines;
- shrinkage or capped weighting when support is sparse;
- information-aware or active benchmark refinement once supply grows.

The next credible proof step is preregistered rolling-origin or true future
holdout validation against simple baselines. In plain terms: freeze a benchmark
using only what would have been known at an earlier time, predict later Agent
performance, then compare that prediction with the actual later outcomes.

## Task Supply And Oracle Sources

Current task supply mostly comes from repository history: commits, pull
requests, issues, changed tests, and reconstructed base commits. This is supply
infrastructure, not the core claim.

Current oracle sources include:

- changed tests from historical work;
- pass-to-pass guards;
- verifier packages assembled from recovered test material;
- manual review of source context and leakage risk.

Future supply or oracle sources can include external task generators, SWE-style
pipelines, generated tests after review, manual customer regressions, and
canaries. All sources must pass local certification before entering a release.

## Next Development Route

The next project work should move from proposal evidence to compiler
development and stronger validation:

- implement a clearer compiler v1 around normalized candidates, certification,
  release manifests, selector policies, scoring, and uncertainty;
- keep task source adapters source-agnostic so external generators can be used
  when they become useful;
- expand certified supply until each claimed repository has enough eligible
  tasks for meaningful selection experiments;
- implement selection experiments against preregistered random, stratified, and
  temporal baselines;
- run rolling-origin or true future holdout validation before making predictive
  validity claims;
- expose Agent run evidence, failure labels, cost summaries, and reward signals
  for tuning loops.

## Product Directions

Agent Tuning is the nearer product direction. Barcarolle can supply benchmark
releases, failure labels, reward signals, uncertainty, and before/after reports
for optimization loops.

Agent License is a lighter future direction. A license can summarize evidence
about whether an Agent is ready for a repository, but that product should depend
on benchmark validity rather than replace it.

## Research Asset Map

The retained experiment code is an active asset. It is not just evidence, and it
should be mined when implementing compiler v1.

Task supply and generation:

- `experiments/phase1_compiler/tools/phase1_task_supply_v2_generator_bakeoff.py`
- `experiments/phase1_compiler/tools/phase1_two_repo_certified_supply_expansion.py`
- `experiments/phase1_compiler/tools/phase1_third_repo_release_supply_screen.py`
- `experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py`

Task certification, statement hardening, and oracle checks:

- `experiments/phase1_compiler/tools/phase1_task_supply_v2_fresh_certification.py`
- `experiments/phase1_compiler/tools/phase1_source_certification_hardening.py`
- `experiments/phase1_compiler/tools/phase1_source_context_statement_hardening.py`
- `experiments/phase1_compiler/tools/phase1_reference_pass_failure_audit.py`

Task selection, validation design, and predictive-signal analysis:

- `experiments/phase1_compiler/tools/phase1_local_algorithm_bakeoff.py`
- `experiments/phase1_compiler/tools/phase1_future_holdout.py`
- `experiments/phase1_compiler/tools/phase1_retrospective_predictive_signal.py`
- `experiments/phase1_compiler/tools/phase1_three_repo_paid_validation.py`
- `experiments/phase1_compiler/tools/phase1_three_repo_paid_result_diagnostics.py`

Workspace and Agent execution support:

- `experiments/phase0_headroom/tools/workspace_acut_run.py`
- `experiments/phase0_headroom/tools/codex_workspace_adapter.py`
- `experiments/phase0_headroom/tools/kilo_workspace_adapter.py`
- `experiments/phase0_headroom/tools/measured_endpoint_run.py`
- `experiments/phase0_headroom/tools/workspace_usage_import.py`

Schemas, configs, and tests:

- `experiments/phase1_compiler/schemas/`
- `experiments/phase1_compiler/configs/`
- `experiments/phase1_compiler/tests/`
- `experiments/phase0_headroom/configs/`
- `experiments/phase0_headroom/tools/test_*.py`

External review inputs:

- `archive/2026-05-external-review-inputs/`

This archive keeps selected prompts and problem briefs for future external
review packet design. It does not define active project state.

Related-work and input synthesis:

- `docs/research/research-inputs-and-related-work-reference.md`

This reference condenses the still-current parts of the May research outline,
weighted-pilot review, task-generator/source-adapter plan, and external review.
It is a reference for compiler-v1 development, not a second canonical state
document.

## Repository Layout

Active material:

- `README.md`: repository entry point.
- `AGENTS.md`: agent-session rules and artifact hygiene.
- `PROCESS.md`: durable process decisions.
- `docs/architecture/system-design.md`: active architecture.
- `docs/research/barcarolle-proposal-report-v5.md`: final proposal report.
- `docs/research/project-state-after-proposal.md`: this canonical state doc.
- `docs/research/research-inputs-and-related-work-reference.md`: related-work
  and research-input reference for compiler-v1 planning.
- `experiments/phase1_compiler/`: compiler prototype, schemas, tests, selected
  reports, and small evidence tables.
- Retained `raw_*` task-supply files are mined candidate inventories, not raw
  LLM prompts, completions, or transcripts. They remain because current
  configs, tests, and evidence reports reference them.
- `experiments/phase0_headroom/`: retained historical task-supply and
  workspace-adapter evidence used by the compiler prototype.

Archived material:

- `archive/2026-05-agent-license-reset/`: historical Agent License and
  core-narrative notes retained only for audit or future productization
  reference.
- `archive/2026-05-external-review-inputs/`: selected external-review prompts
  and problem briefs retained as research-process references.

Removed from active mainline:

- old Agent License architecture and decision docs;
- old core-narrative experiment tree;
- `.codex-workflows` process bundles;
- proposal/deck runbooks, PPT outputs, standalone preflight/process artifacts,
  raw transcripts, solver/verifier workspaces, local virtual environments,
  caches, and large raw outputs.
