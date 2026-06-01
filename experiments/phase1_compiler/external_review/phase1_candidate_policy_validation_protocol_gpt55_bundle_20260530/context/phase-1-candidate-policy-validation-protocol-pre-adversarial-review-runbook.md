# Phase 1 Candidate Policy And Validation Protocol Pre-Adversarial Review Runbook

Status: no-paid implementation and protocol-prep runbook, 2026-05-30.

This runbook is for one dedicated Codex CLI session. Its job is to do the work
needed before an adversarial GPT-5.5-Pro review:

```text
Promote coverage_constrained_unweighted from retrospective candidate into a
deterministic, outcome-blind Barcarolle candidate selection policy; freeze the
next validation protocol; and create a sanitized review packet that is ready
for adversarial review but is not submitted by this runbook.
```

Plain-language summary:

```text
The latest no-paid retrospective analysis found weak directional signal for a
coverage-constrained unweighted design. That is useful traction, but not a
predictive-validity proof.

The next useful step is not another paid ACUT run. The next useful step is to
make the candidate policy reproducible, write down exactly how the next
rolling-origin or future-holdout validation would test it, and prepare the
smallest clear evidence packet for adversarial review.
```

## Execution Boundary

This runbook is no-paid. It must not make paid ACUT solver calls, paid LLM
calls, or external GPT-5.5-Pro/adversarial-review calls.

Allowed work:

- read committed runbooks, process notes, candidate inventories, selection
  artifacts, score-table manifests, retrospective signal reports, and sanitized
  result files;
- implement deterministic local tooling for a
  `coverage_constrained_unweighted` candidate selection policy;
- write config schemas, small JSON artifacts, tests, reports, and a decision;
- define outcome-blind policy inputs, feature fields, exclusion rules, seed
  policy, tie-break policy, output manifest, and fallback rules;
- define a preregistered validation protocol for a future rolling-origin or
  future-holdout study;
- compare the planned candidate policy against simple baselines at the protocol
  level, without joining new outcomes;
- create a sanitized adversarial-review packet with an evidence index,
  question list, claim boundary, and manifest;
- update `PROCESS.md` if the run changes the active handoff state.

Disallowed work:

- running paid ACUT solver cells;
- invoking GPT-5.5-Pro or any external LLM for review, task solving, statement
  generation, policy selection, or scoring;
- rerunning completed paid cells;
- changing completed paid terminal outcomes, score tables, selected task IDs,
  split labels, source-eligibility artifacts, task statements, or completed
  decisions;
- using terminal outcomes, pass/fail labels, adapter outcomes, or H_future
  outcomes to choose selected tasks, tune the policy, pick seeds, choose
  cutoffs, define success thresholds, or select favorable baselines;
- promoting the completed blocked split supplement to a primary design claim;
- claiming formal predictive validity;
- collapsing Codex and Kilo into a model-only result;
- committing raw prompts, raw completions, raw ACUT transcripts, raw Codex/Kilo
  logs, solver workspaces, verifier workspaces, target repo clones, raw public
  API responses, raw target diffs, raw test patches, `.venv`, caches, secrets,
  or large raw outputs;
- submitting, emailing, pasting, or otherwise sending the review packet to an
  external reviewer.

If the worker cannot implement an outcome-blind policy without reading outcome
columns, stop and write a blocker report. Do not work around that by manually
copying outcome-filtered task lists.

## Starting Point

Current process state:

```text
project boundary:
  Barcarolle is a target-repository benchmark compiler, not an ACUT harness or
  general SWE task factory.

predictive validity:
  not established.

current Phase 1 goal:
  traction evidence, narrative validation, and project/proposal support.

paid ACUT cells:
  blocked by default.

three-repo supply:
  attrs, boltons, click.

click source-quality boundary:
  repaired enough for the source-quality part of the three-repo story.

adapter policy:
  report Codex and Kilo separately first; pooled summaries are secondary.
```

Latest candidate evidence:

```text
old weighted target-profile compiler:
  failed paid pilot; keep as negative-control/reference only.

repo_unweighted / repo_stratified / temporal_recent:
  simple baselines.

coverage_constrained_unweighted:
  best Barcarolle candidate in no-paid retrospective pseudo-future analysis;
  MAE 0.209 versus best simple baseline temporal_recent_baseline MAE 0.2149.

block_randomized_stratified and block_plus_shrinkage_weighted:
  not supported by the latest retrospective analysis; keep as research
  branches or diagnostics, not primary candidates.

completed_blocked_split_supplement:
  numerically strong diagnostic, but post-hoc and only six slices; do not
  promote as primary evidence.
```

This runbook should answer:

```text
Can Barcarolle now present a concrete, reproducible
coverage_constrained_unweighted candidate policy and a frozen validation
protocol that are ready for adversarial review before any further paid ACUT
work?
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-candidate-policy-validation-protocol-pre-adversarial-review-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md and PROCESS.md first.
Use uv for repo-local Python tooling. Follow AGENTS.md step-level acceptance and
commit requirements: after each step, or after a small group of tightly related
steps, commit the changed files with an appropriately scoped commit.

Main goal: promote coverage_constrained_unweighted into a deterministic,
outcome-blind Barcarolle candidate selection policy; freeze the next validation
protocol; and create a sanitized adversarial-review packet. Stop before
submitting the packet to any external reviewer or GPT-5.5-Pro.

This runbook is no-paid. Do not run paid ACUT cells. Do not call paid LLMs. Do
not invoke GPT-5.5-Pro or any external reviewer. Do not rerun cells. Do not
change paid outcomes, score tables, selected task IDs, split labels, source
eligibility, task statements, or completed decisions.

Outcome-blindness is a hard requirement. The candidate policy tool must not read
terminal outcomes, pass/fail labels, adapter outcomes, H_future outcomes, or
score tables while selecting tasks, computing policy diagnostics, picking seeds,
or freezing the protocol. If the implementation needs score outcomes for a
summary, separate it into a clearly labeled post-selection diagnostic command.

Use adapter-stratified reporting first. The validation protocol must report
Codex and Kilo separately by default. Pooled results may appear only as
secondary diagnostics with the estimator defined before future outcomes are
joined.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. What action it suggests next.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
Codex/Kilo logs, solver workspaces, verifier workspaces, target repo clones,
raw public API responses, raw target diffs, raw test patches, .venv, caches, or
large raw outputs. Commit only small sanitized configs, tools, tests, tables,
reports, manifests, digests, review-packet indexes, and decision files.
```

## Required Inputs

Read these coordination files first:

```text
AGENTS.md
PROCESS.md
docs/architecture/system-design.md
docs/experiments/phase-1-retrospective-predictive-signal-analysis-runbook.md
docs/experiments/phase-1-click-llm-assisted-source-context-repair-runbook.md
docs/experiments/phase-1-blocked-split-supplement-fairness-and-gap-diagnostics-runbook.md
```

Use these canonical decision and signal artifacts when present:

```text
experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_decision.json
experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_baseline_comparison.json
experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_adapter_metrics.json
experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_uncertainty.json
experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_design_registry.json
experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_selection_freeze.json
experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_window_plan.json

experiments/phase1_compiler/results/phase1_click_llm_source_context_repair_decision.json
experiments/phase1_compiler/results/phase1_click_llm_source_context_repair_quality_overlay.json

experiments/phase1_compiler/results/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.json
experiments/phase1_compiler/results/phase1_blocked_split_supplement_fairness_gap_diagnostics_adapter_fairness_audit.json

experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_candidate_designs.json
experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_validation_results.json
experiments/phase1_compiler/results/phase1_local_algorithm_bakeoff_paid_readiness_gate.json

experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_task_table.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_split_plan.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_baseline_plan.json
experiments/phase1_compiler/results/phase1_three_repo_paid_validation_score_tables_manifest.json
```

Useful implementation references:

```text
experiments/phase1_compiler/tools/phase1_retrospective_predictive_signal.py
experiments/phase1_compiler/tools/phase1_local_algorithm_bakeoff.py
experiments/phase1_compiler/tools/phase1_blocked_split_redesign.py
experiments/phase1_compiler/tests/test_phase1_retrospective_predictive_signal.py
experiments/phase1_compiler/tests/test_phase1_local_algorithm_bakeoff.py
experiments/phase1_compiler/tests/test_phase1_blocked_split_redesign.py
```

If an input is missing or moved, record it in the preflight report and continue
with available committed artifacts when the run can still stay outcome-blind.

## Output Layout

Use this prefix for new artifacts:

```text
phase1_candidate_policy_validation_protocol
```

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_candidate_policy_validation_protocol.yaml
  tools/
    phase1_candidate_policy_validation_protocol.py
  tests/
    test_phase1_candidate_policy_validation_protocol.py
  results/
    phase1_candidate_policy_validation_protocol_preflight.json
    phase1_candidate_policy_validation_protocol_policy_spec.json
    phase1_candidate_policy_validation_protocol_input_freeze.json
    phase1_candidate_policy_validation_protocol_selection_manifest.json
    phase1_candidate_policy_validation_protocol_outcome_blindness_audit.json
    phase1_candidate_policy_validation_protocol_validation_protocol.json
    phase1_candidate_policy_validation_protocol_success_criteria.json
    phase1_candidate_policy_validation_protocol_baseline_registry.json
    phase1_candidate_policy_validation_protocol_review_packet_manifest.json
    phase1_candidate_policy_validation_protocol_claim_boundary.json
    phase1_candidate_policy_validation_protocol_decision.json
  reports/
    phase1_candidate_policy_validation_protocol_process.md
    phase1_candidate_policy_validation_protocol_policy_spec.md
    phase1_candidate_policy_validation_protocol_selection_manifest.md
    phase1_candidate_policy_validation_protocol_outcome_blindness_audit.md
    phase1_candidate_policy_validation_protocol_validation_protocol.md
    phase1_candidate_policy_validation_protocol_success_criteria.md
    phase1_candidate_policy_validation_protocol_adversarial_review_packet.md
    phase1_candidate_policy_validation_protocol_decision.md
```

Create a small sanitized review packet under:

```text
experiments/phase1_compiler/external_review/
  phase1_candidate_policy_validation_protocol_review_20260530/
    README_FOR_ADVERSARIAL_REVIEW.md
    EVIDENCE_INDEX.md
    REVIEW_QUESTIONS.md
    CLAIM_BOUNDARY.md
    MANIFEST.sha256
```

The review packet should prefer links to canonical committed reports over copied
evidence. If the packet needs self-contained snippets, keep them short,
sanitized, and free of raw prompts, raw completions, raw ACUT transcripts, raw
diffs, raw tests, secrets, workspaces, caches, and cloned repos.

Do not modify or stage this existing unrelated untracked bundle unless the user
explicitly asks:

```text
experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/
```

## Candidate Policy Requirements

The promoted policy is `coverage_constrained_unweighted`.

Minimum policy definition:

```text
policy_id:
  coverage_constrained_unweighted_v1

primary purpose:
  choose a small repo-specific benchmark set that maximizes coarse
  solver-visible feature coverage under a fixed task budget without using
  outcome data or task-level score weights.

inputs:
  eligible task inventory
  repo id
  task source/provenance fields
  repaired source-quality overlay
  solver-visible statement/context quality fields
  coarse work-distribution fields available before outcomes
  budget per repo or per window
  deterministic seed

forbidden inputs:
  terminal_status
  verified_pass / verified_fail
  pass_rate
  adapter outcome
  B_eval/H_future observed outcome
  score table rows
  raw ACUT transcripts
  hidden verifier output

score model:
  unweighted pass-rate estimator by adapter and repo/window slice.

selection objective:
  maximize coverage of preregistered coarse feature buckets first, then
  minimize imbalance, then use deterministic seeded tie-breaks.

fallback:
  if feature support is too sparse, degrade to repo_stratified or
  repo_unweighted with an explicit insufficient-support label.
```

The worker may refine the exact feature bucket names, but they must be coarse,
solver-visible or public-before-outcome, and auditable. Avoid high-cardinality
matching that repeats the old weighted target-profile failure mode.

The policy must output:

```text
selected task ids
excluded task ids with reasons
feature coverage table
coverage gaps
fallback status
seed and tie-break policy
input artifact digests
outcome_blindness_audit
```

## Validation Protocol Requirements

The validation protocol must be frozen before any future paid ACUT calls.

Required protocol sections:

```text
study_mode:
  preferred: true future holdout if new outcome-unseen tasks exist
  fallback: preregistered rolling-origin / pseudo-future replay

primary candidate:
  coverage_constrained_unweighted_v1

mandatory baselines:
  temporal_recent_baseline
  repo_unweighted_same_budget
  repo_stratified_by_target_profile
  seeded_random_same_budget

optional research branches:
  block_randomized_stratified
  block_plus_shrinkage_weighted
  old weighted target-profile as negative/reference only

primary reporting:
  adapter-stratified MAE and catastrophic miss rate

secondary reporting:
  equal-mix pooled estimator only if defined before outcomes are joined

success criteria:
  candidate beats the best simple baseline on primary MAE by a preregistered
  margin or satisfies a preregistered majority-of-slices rule;
  improvement must not be driven only by one repo or one adapter;
  catastrophic miss rate must not worsen materially versus best baseline;
  no policy violations;
  source-quality and endpoint/accounting checks pass.

claim boundary:
  traction evidence if retrospective or underpowered;
  predictive validity only if future outcome-unseen validation meets the
  frozen thresholds.
```

The protocol must explicitly say how it handles:

- Codex/Kilo adapter stratification;
- invalid/non-scoreable cells;
- endpoint compliance and cost accounting;
- task source-quality overlays;
- missing repo or sparse window support;
- seed stability;
- already-inspected outcomes;
- no-paid local analysis versus future paid validation.

## Adversarial Review Packet Requirements

The packet is for a later human-initiated GPT-5.5-Pro or external expert review.
This runbook only prepares it.

The packet must include:

```text
1. One-page context:
   What Barcarolle is, what it is not, and what claim is currently being made.

2. Evidence index:
   Links to canonical reports and result files, with one-line descriptions.

3. Candidate policy summary:
   The exact coverage_constrained_unweighted_v1 rule, inputs, forbidden inputs,
   seed policy, fallback policy, and expected outputs.

4. Validation protocol summary:
   Study design, baselines, metrics, adapter handling, success criteria, and
   paid/no-paid boundary.

5. Known weaknesses:
   Retrospective signal is weak and underpowered; Codex slice did not improve;
   improvement is not uniform across repos; blocked/shrinkage candidates failed
   latest comparison; completed blocked split is post-hoc.

6. Review questions:
   Ask the reviewer to challenge the policy, validation protocol, success
   thresholds, adapter reporting, claim boundary, and proposal narrative.

7. Manifest:
   SHA-256 hashes for packet files and the most important referenced result
   files.
```

Recommended review questions:

```text
1. Is coverage_constrained_unweighted_v1 a defensible near-term mainline
   candidate given the current evidence, or is it too close to a simple
   coverage heuristic to carry the Barcarolle compiler claim?

2. Does the proposed rolling-origin or future-holdout protocol actually test
   predictive validity, or does it still leave a post-hoc/transductive loophole?

3. Are the baselines strong enough, especially temporal_recent_baseline,
   repo_unweighted_same_budget, repo_stratified_by_target_profile, and seeded
   random same-budget?

4. Are the success criteria too weak, too strong, or vulnerable to a single
   repo/adapter driving the conclusion?

5. Does adapter-stratified reporting correctly treat Codex and Kilo as ACUT
   configurations rather than model-only comparisons?

6. Is the proposal narrative better stated as predictive benchmark compiler,
   auditable repo-specific benchmark construction with early predictive signal,
   or something narrower?
```

## Step 0: Preflight And Worktree State

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, and worktree
   status.
2. Read `AGENTS.md` and `PROCESS.md`.
3. Confirm the run is no-paid and no external-review submission will happen.
4. Record available/missing required inputs.
5. Write:

```text
experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_preflight.json
experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_process.md
```

Acceptance:

- preflight records existing untracked unrelated files;
- no paid or external LLM calls made;
- missing inputs are explicit;
- first process note says whether the run can proceed outcome-blind.

Commit:

```text
Record candidate policy validation protocol preflight
```

## Step 1: Freeze Candidate Policy Spec

Actions:

1. Define `coverage_constrained_unweighted_v1` in config.
2. Define allowed input fields and forbidden outcome fields.
3. Define coarse feature buckets, budget policy, seed/tie-break policy,
   fallback rules, and output schema.
4. Write policy spec JSON and Markdown.

Acceptance:

- policy spec can be read without consulting score tables;
- forbidden fields include terminal outcomes and adapter outcomes;
- fallback does not silently switch to a more favorable design;
- old weighted, blocked, and shrinkage designs remain baselines/research
  branches, not the primary candidate.

Commit:

```text
Freeze coverage constrained unweighted policy spec
```

## Step 2: Implement Outcome-Blind Policy Tooling

Actions:

1. Add a deterministic CLI tool under
   `experiments/phase1_compiler/tools/phase1_candidate_policy_validation_protocol.py`.
2. Implement commands sufficient to:
   - load config;
   - validate forbidden fields are absent from policy-selection inputs;
   - build the policy input freeze;
   - select candidate tasks or produce a blocker if support is insufficient;
   - emit coverage and exclusion manifests;
   - emit an outcome-blindness audit.
3. Add focused tests.

Acceptance:

- tests prove the selector rejects outcome-bearing inputs;
- tests prove deterministic seed/tie-break behavior;
- tests prove fallback labels are explicit;
- generated manifests include input digests and selected/excluded task IDs;
- no score table is read by the selection command.

Suggested commands:

```bash
uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_candidate_policy_validation_protocol.py
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_candidate_policy_validation_protocol.py run --config experiments/phase1_compiler/configs/phase1_candidate_policy_validation_protocol.yaml
```

Commit:

```text
Implement outcome blind candidate policy tooling
```

## Step 3: Freeze Validation Protocol And Success Criteria

Actions:

1. Write the validation protocol JSON and Markdown.
2. Define the exact baselines, candidate, optional research branches, metrics,
   adapter reporting, invalid-cell handling, source-quality gates, endpoint
   checks, and cost/accounting gates.
3. Define success criteria for:
   - traction evidence;
   - future predictive-validity claim;
   - paid-readiness gate;
   - stop/blocker conditions.
4. Make clear that no paid run is authorized by this runbook.

Acceptance:

- protocol is frozen before future paid calls;
- baselines are stronger than a weak strawman;
- adapter-stratified reporting is primary;
- success criteria cannot be satisfied by pooled improvement alone;
- future predictive-validity claim requires future outcome-unseen validation or
  a preregistered rolling-origin design with sufficient support.

Commit:

```text
Freeze candidate policy validation protocol
```

## Step 4: Prepare Adversarial Review Packet

Actions:

1. Create the review packet directory.
2. Write:
   - `README_FOR_ADVERSARIAL_REVIEW.md`
   - `EVIDENCE_INDEX.md`
   - `REVIEW_QUESTIONS.md`
   - `CLAIM_BOUNDARY.md`
   - `MANIFEST.sha256`
3. Link to canonical reports instead of copying large evidence.
4. Include known weaknesses and direct adversarial questions.
5. Write packet manifest JSON and packet summary report.

Acceptance:

- packet is self-explanatory to a reviewer with repository access;
- packet is small and sanitized;
- packet does not include raw prompts, completions, transcripts, workspaces,
  raw diffs, raw tests, secrets, cloned repos, or caches;
- packet explicitly says it has not been submitted;
- manifest hashes are reproducible.

Commit:

```text
Prepare candidate policy adversarial review packet
```

## Step 5: Closeout Decision

Actions:

1. Write final claim boundary and decision JSON/Markdown.
2. Update `PROCESS.md` if handoff state changed.
3. Run focused tests and `git diff --check`.
4. Record exact commands and results in the process report.
5. Stop with one of these labels:

```text
ready_for_adversarial_review
blocked_policy_not_outcome_blind
blocked_insufficient_policy_inputs
blocked_validation_protocol_not_defensible
blocked_review_packet_not_sanitized
```

Acceptance:

- decision says whether the packet is ready for later adversarial review;
- decision says no external review was submitted;
- decision says no paid ACUT or LLM calls were made;
- tests and `git diff --check` status are recorded;
- next action is review submission or reviewer-response triage, not a paid run.

Suggested verification:

```bash
uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_candidate_policy_validation_protocol.py
uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_retrospective_predictive_signal.py
git diff --check
```

Commit:

```text
Close candidate policy validation protocol prep
```

## Final Report Expectations

The closeout report should be short and concrete:

```text
What happened:
  candidate policy implemented/frozen, validation protocol frozen, review packet
  prepared.

Why it matters:
  Barcarolle now has a concrete object for adversarial review before spending
  more paid ACUT budget.

What action it suggests next:
  submit the packet to GPT-5.5-Pro or another adversarial reviewer; then triage
  reviewer objections before any paid validation.
```

Do not draft the next runbook unless the user explicitly asks after reading the
review or closeout decision.
