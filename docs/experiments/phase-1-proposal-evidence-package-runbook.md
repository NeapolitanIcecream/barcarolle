# Phase 1 Proposal Evidence Package Runbook

Status: no-paid proposal evidence runbook, 2026-06-01.

This runbook is for one dedicated Codex CLI session. Its job is to produce the
M3 no-paid evidence package routed by M2: the preliminary evidence summary,
many-seed random baseline distribution, baseline-envelope comparison, coverage
objective ablation, fallback-share accounting, source-supply status, and report
evidence index needed by the proposal report.

```text
Fill the evidence-type P0 gaps from proposal report v1 without claiming
predictive validity and without authorizing paid validation.
```

Plain-language summary:

```text
M2 decided which blanks belong to evidence production. M3 should now compute
and write the evidence package that M4 will use for protocol hardening and M5
will use for reviewer-facing report revision.
```

## Execution Boundary

This runbook is no-paid analysis and documentation work. It must not make paid
ACUT solver calls, paid LLM calls, external GPT-5.5-Pro calls, or new external
review calls.

Allowed work:

- read committed reports, configs, score-table manifests, sanitized score
  tables, selection manifests, candidate-policy artifacts, source-quality
  overlays, and local planning files;
- create a narrowly scoped proposal-evidence tool and tests if existing tools
  do not already produce the required package;
- compute no-paid summaries from already committed/sanitized artifacts;
- write proposal-facing evidence reports and machine-readable summaries;
- update the proposal evidence matrix, roadmap, or `PROCESS.md` only to record
  the M3 handoff state;
- run scoped tests and `git diff --check`.

Disallowed work:

- running paid ACUT cells;
- running paid LLM calls;
- calling GPT-5.5-Pro or another external reviewer;
- browsing for public citations;
- running new ACUT adapters or solver workspaces;
- changing paid outcomes, score tables, selected task IDs, split labels, source
  eligibility artifacts, task statements, or completed decisions;
- changing candidate-policy thresholds, adapter estimands, invalid-cell rules,
  success gates, power/budget assumptions, or paid-readiness gates;
- drafting M4, M5, or M6 runbooks;
- claiming predictive validity is established;
- authorizing paid validation;
- committing raw prompts, raw completions, raw ACUT transcripts, solver
  workspaces, verifier workspaces, target repo clones, raw public API
  responses, raw target diffs, raw test patches, `.venv`, caches, secrets, or
  large raw outputs.

If evidence is too weak, conflicting, or incomplete, record that directly. Do
not strengthen the proposal claim to hide a weak result.

## Starting Point

M2 completed placeholder triage:

```text
docs/research/phase-1-proposal-p0-placeholder-triage.md
```

M3 owns these proposal report v1 P0/P1 placeholders:

```text
[NEEDS TABLE: one-page preliminary evidence summary]
[NEEDS RESULT: many-seed random baseline distribution and candidate percentile]
[NEEDS RESULT: baseline-envelope comparison]
[NEEDS RESULT: coverage objective ablation]
[NEEDS APPENDIX TABLE: report evidence index]
```

M3 also provides supporting evidence for:

```text
fallback-share accounting and boltons fallback wording
concise source-supply status
adapter/repo fragility summary
```

M3 does not decide fallback thresholds, adapter estimands, invalid-cell rules,
joint success gates, or power/budget notes. Those belong to M4.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-proposal-evidence-package-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md and PROCESS.md first.
Then read docs/research/phase-1-proposal-p0-placeholder-triage.md,
docs/research/phase-1-proposal-report-v1.md,
docs/research/phase-1-proposal-evidence-todo-matrix.md,
docs/research/phase-1-proposal-claim-boundary.md, and
docs/research/phase-1-proposal-roadmap-and-claim-planning.md. Follow AGENTS.md
step-level acceptance and commit requirements.

Main goal: produce the M3 no-paid proposal evidence package. The package must
include a one-page preliminary evidence summary, many-seed random baseline
distribution with candidate percentile, baseline-envelope comparison,
coverage-objective ablation, fallback-share accounting, concise source-supply
status, and compact report evidence index.

Use existing committed/sanitized artifacts only. You may add a narrow
`phase1_proposal_evidence_package.py` tool, config, and tests if needed. Do not
run paid ACUT cells. Do not call paid LLMs. Do not call GPT-5.5-Pro or browse
for citations. Do not change score tables, task IDs, split labels, source
eligibility, task statements, or completed decisions.

Do not claim predictive validity is proved. Do not authorize paid validation.
Do not decide M4 protocol thresholds. If an evidence result is weak or negative,
report it as weak or negative and explain what claim it can and cannot support.
Do not draft M4, M5, or M6 runbooks.
```

## Required Inputs

Read these coordination files first:

```text
AGENTS.md
PROCESS.md
docs/research/phase-1-proposal-p0-placeholder-triage.md
docs/research/phase-1-proposal-report-v1.md
docs/research/phase-1-proposal-evidence-todo-matrix.md
docs/research/phase-1-proposal-claim-boundary.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
experiments/phase1_compiler/reports/phase1_p0_placeholder_external_review_triage_decision.md
```

Use these existing analysis and policy artifacts:

```text
experiments/phase1_compiler/configs/phase1_retrospective_predictive_signal.yaml
experiments/phase1_compiler/tools/phase1_retrospective_predictive_signal.py
experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_universe.json
experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_selection_freeze.json
experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_score_join_manifest.json
experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_adapter_metrics.json
experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_baseline_comparison.json
experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_uncertainty.json
experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_selection_manifest.json
experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_policy_spec.json
experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_outcome_blindness_audit.json
experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_validation_protocol.json
experiments/phase1_compiler/results/phase1_task_supply_v2_source_bakeoff_decision.json
experiments/phase1_compiler/results/phase1_click_llm_source_context_repair_decision.json
```

Use these canonical reports for proposal-facing evidence text:

```text
experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md
experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md
experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md
experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md
experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md
experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md
```

Read local planning files only if a claim boundary needs context:

```text
/Users/chenmohan/Downloads/barcarolle-research-0519.md
/Users/chenmohan/Downloads/barcarolle-research-0526.md
/Users/chenmohan/Downloads/barcarolle-research-0526-1.md
/Users/chenmohan/Downloads/barcarolle-research-0530.md
```

## Output Layout

Add or update a narrow tool/config only if needed:

```text
experiments/phase1_compiler/configs/phase1_proposal_evidence_package.yaml
experiments/phase1_compiler/tools/phase1_proposal_evidence_package.py
experiments/phase1_compiler/tests/test_phase1_proposal_evidence_package.py
```

Add proposal-facing evidence document:

```text
docs/research/phase-1-proposal-evidence-package.md
```

Add machine-readable outputs:

```text
experiments/phase1_compiler/results/
  phase1_proposal_evidence_package_preflight.json
  phase1_proposal_evidence_package_preliminary_evidence_summary.json
  phase1_proposal_evidence_package_random_baseline_distribution.json
  phase1_proposal_evidence_package_baseline_envelope.json
  phase1_proposal_evidence_package_coverage_ablation.json
  phase1_proposal_evidence_package_fallback_share.json
  phase1_proposal_evidence_package_source_supply_status.json
  phase1_proposal_evidence_package_report_evidence_index.json
  phase1_proposal_evidence_package_decision.json
```

Add Markdown reports:

```text
experiments/phase1_compiler/reports/
  phase1_proposal_evidence_package_process.md
  phase1_proposal_evidence_package_preliminary_evidence_summary.md
  phase1_proposal_evidence_package_random_baseline_distribution.md
  phase1_proposal_evidence_package_baseline_envelope.md
  phase1_proposal_evidence_package_coverage_ablation.md
  phase1_proposal_evidence_package_fallback_share.md
  phase1_proposal_evidence_package_source_supply_status.md
  phase1_proposal_evidence_package_report_evidence_index.md
  phase1_proposal_evidence_package_decision.md
```

Optionally update:

```text
docs/research/phase-1-proposal-evidence-todo-matrix.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
PROCESS.md
```

Do not update `docs/research/phase-1-proposal-report-v1.md` except for a short
appendix pointer if the evidence package location must be discoverable. M5 owns
the reviewer-ready report rewrite.

## Evidence Package Requirements

### Preliminary Evidence Summary

Create a one-page proposal-facing table with rows for:

- research problem is real;
- naive weighted design failed in a diagnosable way;
- workspace ACUT protocol and artifact hygiene are technically tractable;
- click source-quality caveat is repaired for source-quality narrative use;
- adapter-stratified reporting is required;
- retrospective signal is directional but underpowered;
- candidate policy exists but is composite because of labeled fallback.

Each row must include:

```text
reader question
claim strength
key numeric result or status
canonical report
limitation
proposal use
```

### Many-Seed Random Baseline Distribution

Produce a random baseline distribution that is stronger than the existing
single `seeded_random_same_budget` summary. Requirements:

- use the same analysis universe and score-join policy as the retrospective
  predictive-signal analysis;
- keep budget and eligibility matched to the candidate comparison;
- use deterministic seeds;
- use enough seeds to give a meaningful percentile, with a default target of
  at least `1000` seeds unless runtime or support constraints require a smaller
  number;
- report overall, per-adapter, per-repo, and per-window summaries where support
  exists;
- report the candidate percentile by MAE and catastrophic-miss rate;
- preserve adapter-level reporting as primary.

If the existing retrospective tool cannot generate this directly, add the
minimal code needed in `phase1_proposal_evidence_package.py` and test it.

### Baseline Envelope

Produce a baseline envelope comparing the promoted research candidate against
the best preregistered simple baseline:

```text
repo_unweighted_same_budget
repo_stratified_by_target_profile
temporal_recent_baseline
many-seed random same-budget distribution
```

Report:

- overall equal-mix secondary summary;
- adapter-level primary summary;
- repo-level and window-level diagnostics when support exists;
- best baseline by slice and by aggregate;
- candidate delta versus the best baseline;
- whether the candidate is better, tied, or worse for each slice.

This is evidence for M4. Do not set the final success threshold in M3.

### Coverage Objective Ablation

Isolate what the coverage objective contributes beyond simple heuristics. At
minimum compare:

- `coverage_constrained_unweighted`;
- `repo_unweighted_same_budget`;
- `repo_stratified_by_target_profile`;
- `temporal_recent_baseline`;
- many-seed random same-budget distribution.

If a clean decomposition is possible, separate:

```text
coverage objective contribution
unweighted same-budget contribution
fallback/composite-policy contribution
temporal recency contribution
```

If a clean decomposition is not possible from current artifacts, write an
explicit limitation and route the missing decomposition to M4 or post-proposal
work. Do not overclaim the ablation.

### Fallback-Share Accounting

Quantify fallback behavior for
`coverage_constrained_unweighted_v1_with_labeled_fallbacks`:

- selected task count by repo;
- fallback-selected count by repo and task slot;
- fallback share overall and by repo;
- coverage gaps by repo and feature;
- including/excluding fallback-repo sensitivity if computable from existing
  artifacts without changing the candidate policy.

M3 must not set the fallback threshold. It should provide the factual basis M4
needs to set a threshold.

### Source-Supply Status

Write a concise Layer 1 source-supply status:

- current source-quality status for `attrs`, `boltons`, and `click`;
- click repair status and limits;
- Task Supply v2 relevance as supply infrastructure, not core claim;
- source-support caveats that can affect future paid readiness;
- no broad task-generator expansion in the short-term proposal scope.

### Report Evidence Index

Create an appendix-friendly compact index of canonical reports. Include:

```text
report
evidence type
claim function
key numeric result or status
limitation
belongs in main text? yes/no
```

## Step 0: Preflight And Artifact Plan

Actions:

1. Record branch, HEAD, date, worktree status, and required-input availability.
2. Confirm M2 route ownership and active report state.
3. Decide whether to add a new proposal-evidence tool/config or reuse existing
   scripts plus manual synthesis.
4. Write the artifact plan in:

```text
experiments/phase1_compiler/results/phase1_proposal_evidence_package_preflight.json
experiments/phase1_compiler/reports/phase1_proposal_evidence_package_process.md
```

Acceptance:

- no paid calls made;
- no external reviewer calls made;
- no public citation browsing made;
- all required inputs are inventoried;
- evidence package output plan is explicit;
- no M4/M5/M6 runbook drafted.

Commit:

```text
Record M3 evidence package preflight
```

## Step 1: Build Or Reuse The Evidence Package Tool

Actions:

1. If existing scripts already produce all required outputs, document the reuse
   plan and skip new code.
2. Otherwise add:

```text
experiments/phase1_compiler/configs/phase1_proposal_evidence_package.yaml
experiments/phase1_compiler/tools/phase1_proposal_evidence_package.py
experiments/phase1_compiler/tests/test_phase1_proposal_evidence_package.py
```

3. Keep custom code narrow and deterministic.
4. Reuse existing parsing/selection logic from
   `phase1_retrospective_predictive_signal.py` where practical instead of
   reimplementing score-table joins.
5. Add tests for:
   - no paid calls and no external review calls;
   - all P0 evidence outputs created;
   - random baseline seed count and determinism;
   - adapter-stratified reporting retained;
   - predictive-validity and paid-validation flags remain false.

Acceptance:

- tool/config/tests exist or reuse plan is recorded;
- tests cover the evidence package's key invariants;
- no score-table or task-selection artifact is changed.

Commit:

```text
Implement proposal evidence package tooling
```

If no new tool is needed, use:

```text
Record proposal evidence package tooling reuse
```

## Step 2: Produce Baseline And Ablation Evidence

Actions:

1. Generate:

```text
phase1_proposal_evidence_package_random_baseline_distribution.json
phase1_proposal_evidence_package_baseline_envelope.json
phase1_proposal_evidence_package_coverage_ablation.json
```

2. Write corresponding reports:

```text
phase1_proposal_evidence_package_random_baseline_distribution.md
phase1_proposal_evidence_package_baseline_envelope.md
phase1_proposal_evidence_package_coverage_ablation.md
```

3. Label every result as:
   - proposal traction;
   - diagnostic negative evidence;
   - insufficient support;
   - not predictive validity.

Acceptance:

- random baseline distribution includes candidate percentile or an explicit
  blocker explaining why it cannot be computed;
- baseline envelope reports best simple comparator overall and by available
  slices;
- coverage ablation reports what is and is not identifiable;
- adapter-level results are primary;
- no final success gate or threshold is set.

Commit:

```text
Produce proposal baseline and ablation evidence
```

## Step 3: Produce Fallback, Source-Supply, And Evidence-Index Outputs

Actions:

1. Generate:

```text
phase1_proposal_evidence_package_fallback_share.json
phase1_proposal_evidence_package_source_supply_status.json
phase1_proposal_evidence_package_report_evidence_index.json
```

2. Write corresponding reports:

```text
phase1_proposal_evidence_package_fallback_share.md
phase1_proposal_evidence_package_source_supply_status.md
phase1_proposal_evidence_package_report_evidence_index.md
```

3. Keep task-supply content inside Layer 1 source infrastructure.
4. Do not promote external task systems or broad generator expansion.

Acceptance:

- fallback share is quantified by repo and task slot where available;
- coverage gaps and `boltons` fallback caveat are visible;
- source-supply status separates `attrs`, `boltons`, and `click`;
- report index is compact and proposal-facing;
- no fallback threshold is set.

Commit:

```text
Produce fallback and source evidence package
```

## Step 4: Write Proposal-Facing Evidence Summary

Actions:

1. Generate:

```text
phase1_proposal_evidence_package_preliminary_evidence_summary.json
phase1_proposal_evidence_package_preliminary_evidence_summary.md
docs/research/phase-1-proposal-evidence-package.md
```

2. Make the summary answer reader questions, not experiment chronology.
3. Mark every claim with one of:

```text
supported_for_proposal
traction_only
diagnostic_negative
needs_M4_protocol_decision
deferred
prohibited
```

Acceptance:

- one-page summary table exists;
- no result is overstated into predictive validity;
- proposal-facing document links to detailed reports;
- evidence gaps remaining for M4/M5 are explicit.

Commit:

```text
Write proposal evidence package summary
```

## Step 5: Align Supporting Documents

Actions:

1. Update `docs/research/phase-1-proposal-evidence-todo-matrix.md` with M3
   evidence status.
2. Update `docs/research/phase-1-proposal-roadmap-and-claim-planning.md` if M3
   changes the recommended next route.
3. Update `PROCESS.md` with the M3 handoff state.
4. Update `docs/research/phase-1-proposal-report-v1.md` only if a short
   appendix pointer to the evidence package is needed.

Acceptance:

- M3 outputs are discoverable from supporting docs;
- roadmap still owns milestone planning;
- proposal report remains final-shape draft and is not rewritten in M3;
- paid validation remains unauthorized;
- no next runbook is drafted.

Commit:

```text
Align M3 evidence package supporting documents
```

## Step 6: Verification And Closeout

Actions:

1. Run focused tests:

```bash
cd experiments/phase1_compiler
uv run pytest tests/test_phase1_proposal_evidence_package.py
```

If the retrospective tool was modified, also run:

```bash
cd experiments/phase1_compiler
uv run pytest tests/test_phase1_retrospective_predictive_signal.py
```

2. Validate JSON outputs:

```bash
python3 -m json.tool experiments/phase1_compiler/results/phase1_proposal_evidence_package_preflight.json
python3 -m json.tool experiments/phase1_compiler/results/phase1_proposal_evidence_package_decision.json
```

3. Check prohibited claims:

```bash
rg -n "proves predictive validity|established predictive validity|authorizes paid|validated predictive benchmark compiler|model-only superiority" docs/research/phase-1-proposal-evidence-package.md experiments/phase1_compiler/reports/phase1_proposal_evidence_package_*.md
```

If a phrase appears only as a prohibited-claim example, record that in the
process report.

4. Run:

```bash
git diff --check
```

5. Write:

```text
experiments/phase1_compiler/reports/phase1_proposal_evidence_package_decision.md
experiments/phase1_compiler/results/phase1_proposal_evidence_package_decision.json
```

Stop with one label:

```text
proposal_evidence_package_complete
blocked_random_baseline_unavailable
blocked_baseline_envelope_unavailable
blocked_coverage_ablation_unidentifiable
blocked_fallback_accounting_unavailable
blocked_claim_boundary_unclear
```

Decision must say:

- no paid calls were made;
- no external reviewer calls were made;
- predictive validity remains unestablished;
- paid validation remains unauthorized;
- whether every M3-owned placeholder is filled, partially filled, or blocked;
- whether M4 should proceed next;
- whether user decisions are needed before the next runbook.

Commit:

```text
Close M3 proposal evidence package
```

## Final Report Expectations

The closeout should say:

```text
What happened:
  the no-paid evidence package filled or explicitly blocked the M3-owned P0/P1
  proposal placeholders.

Why it matters:
  M4 can now harden validation and candidate-policy gates using concrete
  baseline, ablation, fallback, and support evidence instead of assumptions.

What action it suggests next:
  proceed to M4 validation/candidate-policy hardening unless the evidence
  package exposes a blocker that requires user decision first.
```

Do not draft the M4 runbook unless the user explicitly asks after reviewing the
M3 result.
