# Phase 1 Proposal Claim Boundary

Status: internal claim guardrail aligned with proposal report v1 and M2
placeholder triage, 2026-06-01.

This document defines what the Phase 1 proposal report may claim now, what it
may claim only with care, what remains draft pending evidence, and what is
prohibited. It is a guardrail for proposal writing and review triage; it is not
a validation protocol and not a paid-run authorization.
The final-shape report draft is
`docs/research/phase-1-proposal-report-v1.md`; this document remains the
claim-boundary guardrail rather than the report itself.

## Boundary Summary

The north star remains predictive validity for repo-specific benchmarks:

```text
Can a Barcarolle-compiled repo-specific benchmark predict future target-repo
ACUT performance?
```

Phase 1 does not establish that north-star claim. The current proposal boundary
is:

```text
Barcarolle has produced traction evidence and a credible research path toward
repo-specific predictive validity. Phase 1 shows that benchmark construction
choices matter, that naive weighted target-profile matching failed in a
diagnosable way, that adapter-stratified reporting and source-quality repair
improve interpretability, and that an outcome-blind candidate selector can now
be hardened against stronger baselines and future-validation criteria.
```

This is the strongest safe short-term claim. It should not be shortened into
"Barcarolle has proven predictive validity."

## Allowed Now

These claims are supported by current committed evidence and can appear in the
proposal report with ordinary caution.

### Project Boundary

Barcarolle is a target-repository benchmark compiler for coding-agent
evaluation and tuning. It is not the ACUT harness, a general SWE task factory,
an agent-license product, or a public leaderboard. Evidence: `AGENTS.md`,
`docs/architecture/system-design.md`.

### Phase 1 Produced Interpretable Pilot Evidence

The weighted pilot, three-repo pilot, retrospective analysis, source repair,
and candidate policy artifacts are clean enough to support exploratory
interpretation and proposal planning. Evidence:

- `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`
- `experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md`
- `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md`
- `experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md`
- `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_decision.md`

### Naive Weighted Matching Failed In A Diagnosable Way

The old weighted target-profile design failed the paid pilot and was not
promoted. Local analysis identified the objective as underidentified under
sparse support and small-N validation. Evidence:
`experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`,
`experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md`,
`/Users/chenmohan/Downloads/barcarolle-research-0526.md`.

### Adapter-Stratified Reporting Is Required

Adapter-level results are primary. Pooled cross-adapter summaries are secondary
unless a future runbook preregisters a pooled estimand. Codex/Kilo differences
are ACUT-configuration evidence, not model-only superiority evidence. Evidence:
`experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md`,
`experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md`.

### Click Source-Quality Repair Supports The Three-Repo Story

The repaired click overlay is clean enough for source-quality narrative support
without rerunning or rewriting paid outcomes. Evidence:
`experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md`.

### Retrospective Signal Is Traction Evidence

The no-paid retrospective pseudo-future analysis found weak directional signal
for `coverage_constrained_unweighted` over the best simple baseline, but the
support is underpowered and adapter/repo fragile. Evidence:
`experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md`,
`experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md`.

## Allowed In Proposal With Care

These claims can appear only with qualifiers and limitations close by.

### Short-Term Proposal Claim

Safe wording:

```text
Phase 1 does not prove predictive validity, but it establishes that the
problem is real, measurable, and technically tractable: construction choices
materially affect repo-specific estimates, naive weighting fails in diagnosable
ways, and early retrospective evidence plus policy hardening define a credible
path toward future validation.
```

Required caveat: no current result establishes predictive validity.

### Current Candidate Object

Safe wording:

```text
coverage_constrained_unweighted_v1_with_labeled_fallbacks
```

The candidate may be called deterministic and outcome-blind based on the frozen
policy spec and outcome-blindness audit. It should not be called a validated
predictive compiler. Evidence:
`experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_policy_spec.md`,
`experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_outcome_blindness_audit.md`.

Required caveat: `boltons` falls back because of insufficient feature support.

### Task Supply v2

Task Supply v2 can be described as Layer 1 supply infrastructure that improves
candidate discovery, certification, and source-quality diagnostics. It should
not be framed as the central Barcarolle contribution. Evidence:
`experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md`,
`/Users/chenmohan/Downloads/barcarolle-research-0526-1.md`.

### Validation Path

The proposal may say that true future holdout or strict preregistered
rolling-origin validation is the path to predictive-validity evidence. It may
not say pseudo-future replay establishes predictive validity. Evidence:
`experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_validation_protocol.md`,
`/Users/chenmohan/Downloads/barcarolle-research-0530.md`.

## Draft Or Needs-Evidence Claims

These claims are plausible but not proposal-ready without the named evidence.

| Draft claim | Needed before proposal-ready use | Route |
| --- | --- | --- |
| Retrospective signal is robust enough to motivate a specific next candidate | Baseline envelope, many-seed random percentile, adapter/repo fragility summary | M3, M4 |
| Candidate policy has acceptable fallback behavior | Fallback share by repo/task slot; `boltons` repair or explicit fallback threshold | M3, M4 |
| Future protocol has adequate success criteria | Joint gate replacing loose margin-or-majority logic; support thresholds; invalid-cell sensitivity | M4 |
| Task Supply v2 is sufficient for paid validation | Certified-yield and source-quality status by repo/source reservoir | M3 or later |
| Paid validation is ready to discuss | External review triage, baseline strengthening, fallback decision, power/budget note | M2, M3, M4 |

## Prohibited Claims

These claims must not appear in the proposal as current findings.

- Barcarolle is already a validated predictive benchmark compiler.
- Phase 1 proves predictive validity.
- `coverage_constrained_unweighted_v1` predicts future target-repo work better
  than simple baselines in the formal validation sense.
- The current evidence authorizes a paid validation run.
- Pseudo-future replay establishes predictive validity.
- Pooled improvement rescues adapter-level failure.
- Codex/Kilo differences prove model-only superiority.
- The completed blocked split supplement is primary predictive-validity
  evidence.
- Task Supply v2, SWE-smith, SWE-Bench++, SWE-bench-Live, or any external task
  generator is the main Barcarolle research contribution.

## Reviewer-Ready Evidence Blockers

Before the argument draft becomes a reviewer-ready proposal report, the
following P0 items should be filled or explicitly marked as deferred:

- final short-term proposal claim wording;
- one-page Phase 1 evidence summary table;
- retrospective baseline comparison with adapter/repo fragility labels;
- fallback-share accounting and `boltons` fallback wording;
- pseudo-future versus predictive-validity boundary wording;
- baseline strengthening plan;
- paid-validation non-authorization statement;
- external review triage of GPT-5.5-Pro recommendations.

These blockers are routed in
`docs/research/phase-1-proposal-evidence-todo-matrix.md` and
`docs/research/phase-1-proposal-p0-placeholder-triage.md`.

## Milestone Sync

M2-M6 remain draft milestones, not new runbooks.

- M2 role: complete. It routed proposal report v1 P0/P1 placeholders, 0530
  review findings, and 0526-1 task-supply guidance into milestone ownership
  without filling placeholders or authorizing paid validation.
- M3 role: consolidate proposal-critical evidence such as baseline tables,
  adapter/repo fragility, fallback share, source-supply status, and the report
  evidence index.
- M4 role: harden validation protocol boundaries and success gates before any
  paid-validation question; this includes the candidate policy pseudocode,
  release schema, fallback threshold, adapter estimand, invalid-cell rules,
  joint gate, support thresholds, and power/budget note.
- M5 role: turn the argument draft into a reviewer-ready proposal report with
  citations, diagrams, current-evidence caveats, and placeholders resolved or
  explicitly deferred.
- M6 role: convert the report into the approval memo, report, deck, or
  combined packet after user decisions on format, staffing, budget ceiling,
  and owner categories.

This document intentionally does not draft those runbooks.

## Stop Boundary

If a future draft cannot keep these boundaries, it should stop with one of:

- `blocked_claim_boundary_unclear`
- `blocked_evidence_matrix_incomplete`
- `blocked_missing_core_inputs`

For the argument rewrite, the intended closeout label is
`proposal_report_argument_rewrite_complete` if verification passes.
