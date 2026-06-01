# Phase 1 Proposal Roadmap And Claim Planning

Status: planning draft, realigned after M2 placeholder triage, 2026-06-01.

This document organizes the current Barcarolle proposal direction after the
final-shape proposal report v1. It is not a runbook, final proposal,
experiment report, or paid-validation authorization.

Use this document to keep short-term proposal work aligned with the long-term
north star and with the P0 placeholders in
`docs/research/phase-1-proposal-report-v1.md`. Sections labeled `Draft` need
confirmation or follow-up milestone work before they become proposal-ready
claims.

## 1. North Star

Stable direction:

```text
Predictive validity is the north star.
```

Barcarolle ultimately asks:

```text
Can a repo-specific benchmark compiled by Barcarolle predict how an agent
configuration will perform later on real work in the same target repository?
```

This is the long-term research target, not a claim already established by
Phase 1.

The key estimand is future target-repo performance, not leaderboard rank:

```text
future target-repo work -> ACUT success rate
Barcarolle benchmark score -> prediction of that future success rate
```

## 2. Short-Term Proposal Claim

Draft proposal claim:

```text
Barcarolle targets predictive validity for repo-specific coding-agent
benchmarks. Phase 1 does not prove predictive validity, but it establishes that
the problem is real, measurable, and technically tractable: benchmark
construction choices materially affect prediction quality, naive methods fail
in diagnosable ways, and early retrospective evidence suggests a path toward
improved selection policies.
```

Chinese working version:

```text
Barcarolle 的北极星是 repo-specific benchmark 的预测效度。Phase 1 尚未证明
预测效度，但已经证明这个问题值得做：不同 benchmark 编译策略会改变对 agent
未来表现的估计，朴素加权方法会失败且失败原因可诊断，简单 coverage /
temporal / stratified 策略已出现弱信号，下一阶段有明确的算法和验证路径。
```

This claim is stronger than "auditable benchmark construction" but weaker than
"predictive validity is established."

Do not use these claims:

```text
Barcarolle is already a validated predictive benchmark compiler.
coverage_constrained_unweighted_v1 has proven predictive validity.
The current results authorize a paid validation run.
Codex/Kilo differences are model-only superiority evidence.
```

## 3. Reader And Argument Frame

Target readers:

- project/proposal reviewers deciding whether Barcarolle should be funded or
  continued;
- coding-agent evaluation researchers skeptical of benchmark overclaiming;
- agent developers who need repo-specific evaluation and tuning feedback.

Reader questions the proposal must answer:

- Why is repo-specific predictive validity a meaningful research target?
- Why is this not just another SWE task generator?
- What evidence shows the problem is real rather than speculative?
- What did Phase 1 prove, and what did it not prove?
- What algorithmic and validation work remains?
- Why is the next phase worth funding despite not yet proving the north star?

Core argument:

```text
Public/general SWE benchmarks and scalable task generators address task
production and general capability. Barcarolle addresses benchmark construction
under target-repository shift: which tasks, splits, weights, baselines, and
uncertainty rules should be used to estimate future work in one repo?
```

## 4. Current Evidence Classification

### Evidence Strong Enough For Proposal Use

- Project boundary is clear: Barcarolle is a target-repository benchmark
  compiler, not an ACUT harness, generic task factory, or leaderboard.
- Workspace ACUT protocol and artifact hygiene exist and have produced paid
  exploratory outcomes.
- Naive weighted target-profile matching failed in a diagnosable way.
- Adapter-stratified reporting is now a stable policy.
- Click source-quality repair removed a visible third-repo source-context
  caveat for the source-quality part of the story.
- The candidate policy and validation protocol review packet are prepared.

### Traction Evidence Only

- Retrospective pseudo-future analysis found weak directional signal for
  coverage-constrained unweighted selection over simple baselines.
- The signal is underpowered and not uniform across adapters or repos.
- Current evidence is useful for proposal motivation, not for predictive
  validity.

### Negative Or Diagnostic Evidence

- Old weighted target-profile compiler should stay a negative-control or
  reference design.
- Completed blocked split supplement is post-hoc diagnostic evidence, not a
  primary predictive-validity result.
- Blocked and shrinkage candidates did not outperform simple baselines in the
  latest retrospective comparison.

### Evidence Gaps

- No strict true-future holdout result yet.
- No adapter-general success claim: current retrospective signal is better for
  Kilo and worse for Codex.
- Current coverage candidate has labeled fallback behavior; boltons fallback is
  a real claim-boundary issue.
- Baseline suite and success criteria need no-paid hardening before any paid
  validation.
- Task supply / feature support still needs stronger v2 work before a broad
  paid-readiness claim.

## 5. GPT-5.5-Pro Review Priority Policy

The GPT-5.5-Pro 2026-05-30 review is useful but not controlling. Its advice is
input to project strategy, not a replacement for the north-star framing.

### Accept Immediately

- Do not authorize paid validation now.
- Keep predictive validity as the north star but avoid claiming it is proven.
- Split pseudo-future traction from predictive-validity evidence.
- Recast the current candidate as a composite selector with labeled fallbacks,
  unless follow-up work removes the fallback issue.
- Replace loose `margin OR majority` success criteria with a joint gate.
- Treat adapter-stratified support as primary; pooled improvement cannot rescue
  an adapter failure.
- Explain boltons fallback explicitly.

### Consider For Short-Term No-Paid Work

- Many-seed random baseline and percentile reporting.
- Baseline envelope against the best preregistered simple baseline.
- Stricter temporal baseline with same budget, same eligibility, and frozen
  tie-breaks.
- Quantitative support thresholds for repos, windows, adapter cells, and
  fallback share.
- A power/budget note explaining what a future paid run can and cannot detect.

### Defer Unless Needed For Proposal Argument

- Full Task Supply v2 expansion.
- External generator adapter implementation.
- Hierarchical beta-binomial or complex uncertainty models.
- Full multi-ACUT residual predictive-validity study.
- Broad repo replacement or public benchmark packaging.

### Do Not Accept As Short-Term Scope Expansion

- Turning Barcarolle into a task generator project.
- Treating external task systems as trusted default supply.
- Requiring every long-term methodological improvement before the proposal can
  be written.

## 6. Active Proposal Report Pull List

The active proposal report is now
`docs/research/phase-1-proposal-report-v3.md`. V1 remains the structural
reference, and V2 remains the evidence-safe source draft and traceability
artifact.

The former V1 pull-list items have either been filled, translated into V3, or
routed to later approval decisions. Remaining work is now reviewer/coordinator
review of V3 plus decisions about approval artifact format, staffing/duration,
budget ceiling for gated ACUT evaluation, and deliverable owner categories.

## 7. Milestone Roadmap

### M1: Proposal Report Shape And Claim Boundary

Status: complete.

Purpose:

```text
Create the proposal-report scaffolding, claim boundary, and final-shape v1
draft that govern remaining pre-proposal work.
```

Completed runbooks:

```text
docs/experiments/phase-1-proposal-report-skeleton-runbook.md
docs/experiments/phase-1-proposal-report-argument-rewrite-runbook.md
docs/experiments/phase-1-proposal-report-final-shape-rewrite-runbook.md
```

Outputs:

- active proposal report v1;
- superseded proposal report v0 source draft;
- argument map;
- evidence/TODO matrix;
- list of claims allowed now, claims needing evidence, and prohibited claims.

### M2: P0 Placeholder And External Review Triage

Status: complete.

Purpose:

```text
Classify proposal report v1 P0 placeholders, GPT-5.5-Pro 0530 findings, and
0526-1 task-supply guidance into milestone ownership without filling the
placeholders, authorizing paid validation, or expanding task-generator scope.
```

Runbook:

```text
docs/experiments/phase-1-p0-placeholder-and-external-review-triage-runbook.md
```

Expected outputs:

- P0 placeholder triage table;
- external-review triage decision;
- updated milestone-to-placeholder map;
- updated claim boundary;
- short-term no-paid fix list;
- `PROCESS.md` update.

Completed M2 route summary:

- M3 owns evidence-package outputs: preliminary evidence summary,
  many-seed random baseline, baseline envelope, coverage-objective ablation,
  fallback-share accounting, concise source-supply status, and evidence index.
- M4 owns validation and candidate hardening: validation design, candidate
  pseudocode, release schema, fallback threshold, adapter estimand, invalid
  cell rules, joint success gate, support thresholds, source eligibility, and
  power/budget note.
- M5 owns reviewer-ready report integration: citations, figures, current
  evidence caveats, final wording, and explicit deferrals.
- M6 owns the approval artifact after user decisions on format, no-paid
  staffing/duration, conditional paid budget ceiling, and owner categories.

### M3: Proposal Evidence Package

Status: complete.

Purpose:

```text
Fill the evidence-type P0 gaps that materially affect the proposal argument.
```

Likely scope:

- one-page preliminary evidence summary;
- many-seed random baseline distribution and candidate percentile;
- baseline-envelope comparison;
- coverage objective ablation;
- adapter/repo fragility summary;
- fallback-share analysis;
- concise source-supply status;
- report evidence index.

Runbook:

```text
docs/experiments/phase-1-proposal-evidence-package-runbook.md
```

Completed outputs:

- `docs/research/phase-1-proposal-evidence-package.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_coverage_ablation.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_fallback_share.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_source_supply_status.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_report_evidence_index.md`

M3 filled the evidence-producing placeholders but did not claim predictive
validity or authorize paid validation. The evidence is mixed: the candidate
beats the best simple aggregate baseline by MAE `0.0059` and beats/ties the
1000-seed random distribution on overall MAE in `93.4%` of seeds, but adapter,
repo, and window diagnostics remain fragile. The frozen candidate policy also
has labeled fallback: `6/18` selected tasks overall and `6/6` boltons tasks.

### M4: Validation Protocol And Candidate Policy Hardening

Status: complete.

Purpose:

```text
Harden the method-type P0 gaps before any paid validation discussion.
```

Completed scope:

- true-future versus pseudo-future claim split;
- composite policy with labeled fallback;
- fallback-share threshold;
- estimand and adapter-claim wording;
- catastrophic-miss and invalid-cell rules;
- joint success gate;
- quantitative support requirements;
- power/budget note;
- candidate policy pseudocode and release artifact schema.

Runbook:

```text
docs/experiments/phase-1-validation-protocol-and-candidate-policy-hardening-runbook.md
```

Completed outputs:

- `docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_claim_modes.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_candidate_policy.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_baseline_registry.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_adapter_estimand.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_success_gate.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_support_thresholds.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_release_schema.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_power_budget_note.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md`

M4 filled the method-type P0 gaps but classified the current M3 candidate as
not paid-ready under the hardened no-paid gate. The future primary margin is
MAE `0.02`; the M3 aggregate edge is `0.0059`. Codex fails adapter-level
support, boltons is `6/6` fallback, and the current study mode remains
retrospective. This is useful proposal traction and a clear validation path,
not a validation result.

### M5: Proposal Report Reviewer-Ready Revision

Status: complete.

Purpose:

```text
Fill or explicitly defer the remaining P0 placeholders in v1 and revise it
into a reviewer-ready proposal report.
```

Runbook:

```text
docs/experiments/phase-1-proposal-report-reviewer-ready-revision-runbook.md
```

Completed outputs:

- `docs/research/phase-1-proposal-report-v2.md`
- `docs/research/phase-1-proposal-report-reviewer-ready-checklist.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_process.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_citation_matrix.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_risk_register.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_decision.md`

M5 reframed the M4 gates as project-stage optimization and validation
standards, not pre-proposal proof requirements. The completed v2 report argues
for project approval from bounded traction: MAE is a meaningful
prediction-error metric, benchmark selection changes it, and the current
candidate beats/ties `93.4%` of 1000 same-budget random selections while still
falling short of future validation standards.

Post-M5 user review found a report-genre regression. V2 is evidence-safe but
not yet acceptable as the final proposal report because it leaks internal
milestone vocabulary, treats paid-evaluation execution safeguards as proposal
premises, and lets the back half read like a protocol/process packet rather
than a reader-facing project proposal.

### M5b: Proposal Report V3 Genre Repair

Status: complete.

Purpose:

```text
Repair v2 into a proposal report that preserves the M1/V1 final-shape
structure unless a reader-facing reason requires a change. Use v2's evidence,
citations, and claim boundary, but remove internal process vocabulary and
reframe paid ACUT evaluation as a normal budgeted project activity after
protocols and success criteria are frozen.
```

Runbook:

```text
docs/experiments/phase-1-proposal-report-v3-genre-repair-runbook.md
```

Completed outputs:

- `docs/research/phase-1-proposal-report-v3.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_v3_genre_repair_process.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_v3_genre_repair_decision.md`
- `experiments/phase1_compiler/results/phase1_proposal_report_v3_genre_repair_decision.json`

V3 superseded V2 for proposal use, then was superseded by later reader-facing
drafts. V2 remains an evidence-safe source draft and traceability artifact.

### M5c: Proposal Report V4 Agent-Tuning Integration

Status: complete.

Purpose:

```text
Make a targeted V4 revision that preserves V3's structure and claim boundary
while integrating agent tuning, configuration selection, and regression
feedback as the product/application path. Phase 2 multi-ACUT residual
predictive validity remains a later scientific extension, not this proposal's
main deliverable.
```

Runbook:

```text
docs/experiments/phase-1-proposal-report-v4-agent-tuning-integration-runbook.md
```

Completed outputs:

- `docs/research/phase-1-proposal-report-v4.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_v4_agent_tuning_integration_process.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_v4_agent_tuning_section_map.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_v4_agent_tuning_integration_decision.md`
- `experiments/phase1_compiler/results/phase1_proposal_report_v4_agent_tuning_integration_decision.json`

V4 superseded V3 as the active proposal report for proposal use. It remains
the agent-tuning integration source draft and traceability artifact, but V5 now
supersedes it for reader-facing proposal review.

### M5d: Reader-Facing Phase-Label Cleanup

Status: complete.

Purpose:

```text
Create a reader-facing V5 proposal report that removes internal phase labels
from the proposal itself. V4's structure, evidence, claim boundary, and
agent-tuning application path should be preserved, but "Phase 1" framing should
be replaced with preliminary/current/pre-proposal evidence language.
```

Runbook:

```text
docs/experiments/proposal-report-v5-reader-facing-phase-label-cleanup-runbook.md
```

Completed outputs:

- `docs/research/barcarolle-proposal-report-v5.md`
- `experiments/phase1_compiler/reports/proposal_report_v5_phase_label_cleanup_process.md`
- `experiments/phase1_compiler/reports/proposal_report_v5_phase_label_cleanup_decision.md`
- `experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md`
- `experiments/phase1_compiler/results/proposal_report_v5_phase_label_cleanup_decision.json`

V5 supersedes V4 as the active proposal report for proposal use and remains
the long-form source of truth for the approval packet. V4 remains the
agent-tuning integration source draft.

### M6: Proposal Approval Packet

Status: complete.

Purpose:

```text
Convert the report into the format needed for project approval.
```

Selected output format:

- editable PPTX approval deck as the primary artifact;
- one-page executive summary;
- concise evidence appendix;
- V5 report as the long-form source of truth.

Runbook:

```text
docs/experiments/proposal-approval-packet-m6-runbook.md
```

Completed outputs:

- `docs/research/m6-approval-packet/barcarolle-approval-deck-v1.pptx`
- `docs/research/m6-approval-packet/executive-summary-v1.md`
- `docs/research/m6-approval-packet/approval-deck-outline-v1.md`
- `docs/research/m6-approval-packet/appendix-evidence-index-v1.md`
- `docs/research/m6-approval-packet/approval-packet-checklist-v1.md`

M6 converted V5 into a decision-facing approval packet while preserving the
claim boundary: current evidence supports project approval and a credible
validation path, but predictive validity and tuning-loop improvement remain
unproven.

User-owned values still left as placeholders:

- staffing and duration;
- conditional paid-validation budget ceiling and approval path;
- reviewer-facing owner categories.

## 8. Work Not On The Short-Term Critical Path

These can be valuable after the proposal direction is stable, but should not
drive the next few days unless the v1 P0 placeholders expose a direct need:

- broad Task Supply v2 expansion;
- external SWE-smith / SWE-Bench++ / SWE-bench-Live adapters;
- generated oracle promotion;
- hierarchical uncertainty modeling;
- full multi-ACUT residual predictive-validity study;
- public benchmark packaging;
- broad productization of optimizer interfaces.

## 9. Immediate Next Step

Review the M6 approval packet and fill or explicitly leave visible the
user-owned staffing, duration, gated evaluation budget ceiling, approval-path,
and owner-category placeholders before sending the packet to reviewers.
Predictive validity remains future work; project-scale paid ACUT evaluation
should be budgeted and gated by frozen protocols rather than framed as
prohibited in the proposal report.
