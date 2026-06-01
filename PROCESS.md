# Barcarolle Process Notes

This file records repository-wide process decisions that future coding-agent
sessions should know before planning or executing Barcarolle work.

It is not a runbook, lab notebook, experiment report, or artifact manifest.
Detailed evidence stays in the relevant committed reports, results, runbooks,
and manifests. This file keeps only the current decision state and durable
operating constraints.

Last updated: 2026-06-01.

## Maintenance Rules

- Read this file after `AGENTS.md` when working on experiments, runbooks,
  paid-validation planning, ACUT adapters, benchmark design, or research
  interpretation.
- Update this file when a task changes the active research direction, paid/no
  paid boundary, mainline algorithm, reporting policy, benchmark claim boundary,
  or cross-session handoff state.
- Keep entries short and link to the canonical report instead of copying its
  evidence. If an entry needs more than a short paragraph, write or update a
  report and summarize it here.
- Do not store secrets, raw prompts, raw completions, raw ACUT transcripts,
  solver workspaces, verifier workspaces, raw diffs, raw test patches, cloned
  target repositories, caches, or large raw outputs here.
- Do not use this file to draft the next runbook unless the user explicitly
  asks for that. Record recommended action categories, not full execution plans.
- Compress stale entries when the file becomes hard to scan. Prefer preserving:
  current decisions, active blockers, claim boundaries, and links to canonical
  reports.

Suggested size target: keep this file under roughly 200 lines. If it grows past
that, compress older sections into a dated summary and leave links to the
source reports.

## Active Process Snapshot

### Project Boundary

Barcarolle remains a target-repository benchmark compiler for coding-agent
evaluation and tuning. It must not become an ACUT agent harness, general SWE
task factory, agent-license product, public leaderboard, or one-shot
chat-completion diff generator.

Canonical instruction source: `AGENTS.md`.

### Current Research State

Phase 1 has produced useful exploratory evidence but has not established
predictive validity.

The current phase goal is to produce traction evidence, validate the research
narrative, and support project/proposal decisions. Do not require every next
step to prove the final predictive-validity claim before it is useful.

The current defensible claim is:

```text
Barcarolle can build audited repo-specific benchmark pilot packages and expose
where naive weighting, split construction, source quality, and claim boundaries
are insufficient. Adapter differences are valid ACUT configuration evidence
when the endpoint, task input, workspace, verifier, policy, and accounting
checks are clean enough. A no-paid retrospective pseudo-future analysis found
directional, underpowered signal for a coverage-constrained unweighted
candidate over simple baselines, but Barcarolle has not established formal
predictive validity or a preregistered held-out future claim.
```

Canonical reports:

- `experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md`
- `experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md`
- `experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md`
- `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md`

### Algorithm Mainline

Do not promote the old weighted target-profile compiler.

The old metadata-weighted design failed the paid pilot and the local bakeoff
confirmed that the objective is underidentified. For paid primary reporting,
keep `repo_stratified` / simple stratified designs as the conservative
baseline until a stronger design has better local evidence.

This is not a ban on algorithm exploration. Blocked, shrinkage-weighted,
coverage-constrained, temporal, or other compiler variants may be explored
openly when they are labeled as research candidates and evaluated against
clear baselines. The near-term goal is useful traction data and narrative
validation, not premature algorithm lock-in.

The retrospective predictive-signal analysis gives coverage-constrained
unweighted selection weak directional traction, but not enough to replace the
conservative mainline or justify paid reruns by itself. The completed blocked
split supplement remains diagnostic/post-hoc; do not promote it as a primary
design claim.

Canonical reports:

- `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`
- `experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_validation_results.md`
- `experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_paid_readiness_gate.md`
- `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md`

### Paid-Run Boundary

Do not run more paid ACUT cells by default.

The latest supplement is fair enough to interpret as exploratory evidence, but
it remains post-hoc/exploratory and does not justify immediate paid reruns. A
future paid run needs a tighter preregistration, explicit adapter handling,
source-quality caveats, uncertainty reporting, and a clear reason why local
no-paid analysis is insufficient.

Canonical reports:

- `experiments/phase1_compiler/reports/phase1_blocked_split_missing_cell_supplement_paid_execution_decision.md`
- `experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_action_matrix.md`

### Adapter Reporting

Report adapter-level results first. Treat pooled cross-adapter summaries as
secondary unless a runbook preregisters a pooled estimator.

Do not treat pooled pass gaps hiding adapter-level differences as the main
research risk by default. Kilo plus `gpt-5.4-mini` may simply be a stronger ACUT
configuration than Codex plus `gpt-5.4-mini` under the current harnesses. The
benchmark-side responsibility is to verify that calls were made through the
intended endpoint and that task inputs, workspace setup, verifier setup, policy
checks, and accounting were fair enough.

Codex and Kilo differences are valid ACUT configuration evidence when endpoint,
model, task, workspace, verifier, policy, and accounting checks pass. Report
the difference as an ACUT configuration result. Do not describe Kilo/Codex
differences as model-only superiority unless adapter and harness differences
have explicitly been ruled out.

Canonical reports:

- `experiments/phase1_compiler/reports/phase1_adapter_stratified_reporting_decision.md`
- `experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_adapter_fairness_audit.md`

### Source Quality Boundary

The current three-repo pilot supply includes `click` as the third repo. The
original paid package carried a visible title-only/minor-risk source-context
caveat for click.

The 2026-05-29 click source-context repair run upgraded all 30 frozen click
tasks through sanitized public issue and pull-request context, with zero paid
LLM calls and zero paid ACUT cells. The active source-quality boundary can now
treat click as clean enough for the source-quality part of a three-repo story,
without rewriting completed paid outcomes or claiming predictive validity.

Canonical reports:

- `experiments/phase1_compiler/reports/phase1_source_context_statement_hardening_decision.md`
- `experiments/phase1_compiler/reports/phase1_blocked_split_redesign_decision.md`
- `experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md`

### LLM-Assisted Supply Enhancement

LLM assistance for task supply and solver-visible statement quality is allowed
when it is tightly controlled, provenance-recorded, and kept inside the
benchmark-compiler boundary. Earlier runbooks explicitly planned and tested
diff-assisted statement regeneration, source-context repair, and task-supply
generator bakeoffs.

Use LLMs for statement drafting, ambiguity review, source-context repair, or
generator-side supply enhancement only when the runbook permits it and the
endpoint/subscription rule for that run is explicit. Do not use LLM generation
to expose hidden oracle material, create unreviewed eval tasks, or turn
Barcarolle into a general SWE task factory. Generated or repaired statements
need leakage/sufficiency review before counting as release eligible.

Canonical reports and runbooks:

- `docs/experiments/phase-1-task-supply-v2-generator-bakeoff-runbook.md`
- `docs/experiments/phase-1-attrs-source-repair-runbook.md`
- `docs/experiments/phase-1-diff-assisted-statement-regeneration-runbook.md`
- `experiments/phase1_compiler/reports/phase1_diff_assisted_codex_loop_recovery_decision.md`
- `experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md`

### Open Follow-Ups

Current next action: execute
`docs/experiments/proposal-approval-packet-m6-runbook.md` to convert
`docs/research/barcarolle-proposal-report-v5.md` into a combined approval
packet. The packet should use a PPTX deck as the primary artifact, with a
one-page executive summary and concise evidence appendix. Leave staffing,
duration, evaluation budget ceiling, and approval-path values as placeholders
unless the user supplies them.

Do not run more paid ACUT cells by default. Future project-scale paid
evaluation should be budgeted and gated by frozen releases, baselines,
score-join rules, and success criteria. Predictive validity and tuning-loop
improvement remain unproven.

Historical proposal milestones M1 through M5d are complete and summarized in
`docs/research/phase-1-proposal-roadmap-and-claim-planning.md`. Do not reopen
old proposal drafts unless V5 has a blocking factual or claim-boundary issue.

Current canonical links:

- `docs/research/barcarolle-proposal-report-v5.md`
- `docs/experiments/proposal-approval-packet-m6-runbook.md`
- `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`
- `docs/research/phase-1-proposal-report-reviewer-ready-checklist.md`
- `experiments/phase1_compiler/reports/proposal_report_v5_phase_label_cleanup_decision.md`
- `experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md`
- `docs/research/phase-1-proposal-evidence-package.md`
- `docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_decision.md`

### Workspace State Note

As of 2026-06-01, the branch `codex/restart-benchmark-compiler` is ahead of
`origin/codex/restart-benchmark-compiler`. Several handoff/setup files remain
untracked, including proposal runbooks and external review bundles under
`experiments/phase1_compiler/external_review/`. Do not stage, delete, or
rewrite those untracked files unless the user asks.
