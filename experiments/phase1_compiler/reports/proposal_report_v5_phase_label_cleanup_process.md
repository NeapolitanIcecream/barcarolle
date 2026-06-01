# Proposal Report V5 Phase-Label Cleanup Process

Status: complete, 2026-06-01.

## Step 0: Preflight And Reader Contract

Preflight was run with no paid ACUT solver calls, no paid LLM calls, no
external reviewer calls, and no public browsing.

Repository state:

| Item | Value |
| --- | --- |
| Branch | `codex/restart-benchmark-compiler` |
| HEAD | `5ce1683df6014f5a570310faf70c507b63a71fcf` |
| Recorded time | `2026-06-01 17:03:27 CST` |
| Upstream state | Ahead of `origin/codex/restart-benchmark-compiler` by 15 commits |

Initial worktree status:

```text
## codex/restart-benchmark-compiler...origin/codex/restart-benchmark-compiler [ahead 15]
 M PROCESS.md
 M docs/research/phase-1-proposal-roadmap-and-claim-planning.md
?? docs/experiments/proposal-report-v5-reader-facing-phase-label-cleanup-runbook.md
```

Required input availability:

| Input | Status |
| --- | --- |
| `AGENTS.md` | available and read |
| `PROCESS.md` | available and read |
| `docs/research/phase-1-proposal-report-v4.md` | available and read |
| `docs/research/phase-1-proposal-report-reviewer-ready-checklist.md` | available and read |
| `docs/research/phase-1-proposal-roadmap-and-claim-planning.md` | available and read |
| `experiments/phase1_compiler/reports/phase1_proposal_report_v4_agent_tuning_integration_decision.md` | available and read |

V4 phase-label search:

```bash
rg -n "Phase 1|Phase 2|Phase 3|phase 1|phase 2|phase 3|M[0-9]|phase1|phase-1" docs/research/phase-1-proposal-report-v4.md
```

Observed matches:

```text
1:# Barcarolle Phase 1 Proposal Report V4
6:benchmark-compiler project. It presents Phase 1 as traction evidence and a
48:Phase 1 supports that request, but only as bounded traction:
50:| Approval question | Phase 1 answer | Proposal limit |
58:validity claim. Predictive validity remains unproven. Phase 1 shows that the
123:Phase 1 supplies traction evidence and a credible validation path. It does not
299:Phase 1 evidence matters because it answers three proposal questions: whether
319:Phase 1 showed that benchmark-side execution can preserve the ACUT boundary:
353:The safe interpretation is therefore narrow: Phase 1 shows that the problem is
549:Phase 1 shows that repo-specific benchmark compilation is a real, measurable,
570:| `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md` | diagnostic negative | Shows naive weighting can fail materially. | Weighted gaps: attrs `0.3148`, boltons `0.7481`. | Two-repo pilot; not a validation result. |
571:| `experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md` | diagnostic negative | Explains underidentified weighted objective. | Old weighted design not promoted. | Local analysis, not future validation. |
572:| `experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md` | technical tractability | Shows workspace ACUT protocol can run end to end. | `120/120` cells, scoreability `1.0`. | Exploratory pilot evidence. |
573:| `experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md` | source quality | Repairs click source-context caveat. | `30/30` click tasks repaired. | Does not rewrite completed outcomes. |
574:| `experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md` | adapter reporting | Supports named-configuration reporting. | Adapter differences treated as ACUT-configuration evidence. | Diagnostic supplement. |
575:| `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md` | retrospective traction | Compares candidate against 1000 random selections. | Overall beats/ties share `93.4%`. | Retrospective replay. |
576:| `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md` | retrospective traction | Compares candidate against best simple baselines. | Candidate `0.209` MAE vs best aggregate baseline `0.2149`. | Slice diagnostics are fragile. |
577:| `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_fallback_share.md` | fallback accounting | Quantifies composite selector behavior. | Overall fallback `0.3333`; boltons `1.0`. | Feature support must be repaired or claim narrowed. |
578:| `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md` | validation governance | Records current protocol interpretation. | Current candidate classified as traction-only and not sufficient for a future validity claim. | Future standards, not current proof. |
605:- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_claim_modes.md`
606:- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_candidate_policy.md`
607:- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_adapter_estimand.md`
608:- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_success_gate.md`
609:- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_support_thresholds.md`
610:- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_release_schema.md`
611:- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_power_budget_note.md`
616:`experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_citation_matrix.md`.
```

Reader contract:

- V5 is the reader-facing proposal report.
- Phase labels are internal coordination vocabulary, not proposal framing.
- Current evidence remains traction-only.
- Agent tuning remains the application path, not a proven outcome.
- Predictive validity and tuning-loop improvement remain unproven.

Step 0 acceptance:

- No paid or external calls were made.
- Process report lists V4 phase-label locations.
- No proposal text was changed in this step.

## Step 1: Create V5 And Remove Main-Body Phase Labels

Created `docs/research/barcarolle-proposal-report-v5.md` from V4 and revised
the title, status note, executive summary, claim boundary, and main evidence
section to use reader-facing proposal language.

Preserved from V4:

- the eleven-section proposal structure;
- the agent-tuning and regression-feedback application path;
- the evidence numbers and limitations;
- the project approval ask;
- the boundary that predictive validity and tuning-loop improvement remain
  unproven.

Main-body phase-label check:

```bash
sed -n '1,538p' docs/research/barcarolle-proposal-report-v5.md | rg -n "Phase 1|Phase 2|Phase 3|phase 1|phase 2|phase 3|M[0-9]|phase1|phase-1"
```

Result: no matches.

Whole-file phase-label check after Step 1 still showed appendix-only matches:
Appendix A retained one claim-boundary sentence with `Phase 1`, and Appendix B
through Appendix D still exposed raw `phase1_...` evidence paths. Those are
reserved for the Step 2 appendix and evidence-index cleanup.

Step 1 acceptance:

- V5 exists at `docs/research/barcarolle-proposal-report-v5.md`.
- The reader-facing title, status, headings, and main body contain no phase
  labels.
- Current evidence remains traction-only.
- Predictive validity remains unproven.

## Step 2: Clean The Claim Boundary And Evidence Appendix

Revised Appendix A so the supported current claim starts from completed pilot
work rather than internal phase framing. Revised Appendix B so the proposal
shows readable evidence labels instead of path-first internal artifact names.

Created the internal evidence manifest:

```text
experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md
```

The manifest preserves path-level traceability for:

- the V4 source draft and integration decision;
- each reader-facing evidence label in Appendix B;
- protocol-detail artifacts previously listed by raw path in Appendix C;
- the reviewer-ready citation matrix previously linked by raw path in
  Appendix D.

Appendix and raw-path checks:

```bash
rg -n "Phase 1|Phase 2|Phase 3|phase 1|phase 2|phase 3|M[0-9]|phase1|phase-1" docs/research/barcarolle-proposal-report-v5.md
rg -n "experiments/phase1_compiler|docs/research/phase-1|phase1_" docs/research/barcarolle-proposal-report-v5.md
```

Result: no matches in V5.

Step 2 acceptance:

- Appendix A has no phase labels.
- Appendix B is readable to a proposal reviewer.
- Raw internal paths are preserved in the internal evidence manifest.
- No evidence claim was strengthened.

## Step 3: Update Checklist And Handoff Documents

Updated the reviewer-ready checklist to make V5 the checked report and record
the phase-label cleanup, V4 preservation, tuning-proof boundary,
predictive-validity boundary, path-level traceability, and paid-evaluation
gates.

Updated the roadmap so:

- M5d is complete;
- V5 supersedes V4 as the active proposal report for proposal use;
- V4 remains the agent-tuning integration source draft;
- M6 waits on V5 acceptance and user/coordinator decisions;
- the immediate next step is V5 review, not another runbook.

Updated `PROCESS.md` so the active process snapshot names V5 as the active
proposal report and records stop label
`proposal_report_v5_phase_label_cleanup_complete`.

Handoff check:

```bash
rg -n "barcarolle-proposal-report-v5|phase_label_cleanup_complete|V5 supersedes V4|waiting on V5 acceptance|V4 remains" docs/research/phase-1-proposal-report-reviewer-ready-checklist.md docs/research/phase-1-proposal-roadmap-and-claim-planning.md PROCESS.md
```

Result: expected V5 and handoff references were present.

Step 3 acceptance:

- Handoff docs point to V5 where appropriate.
- The roadmap keeps internal milestone terms because it is an internal
  planning file.
- M6 waits on V5 acceptance and user/coordinator decisions.

## Step 4: Audit

Required audit commands:

```bash
rg -n "Phase 1|Phase 2|Phase 3|phase 1|phase 2|phase 3|M[0-9]|phase1|phase-1" docs/research/barcarolle-proposal-report-v5.md
rg -n "validated predictive benchmark compiler|established predictive validity|tuning validation established|improves agent tuning|multi-ACUT residual validity established" docs/research/barcarolle-proposal-report-v5.md
rg -n "/Users/chenmohan/Downloads" docs/research/barcarolle-proposal-report-v5.md
git diff --check
```

Audit results:

| Check | Result |
| --- | --- |
| V5 phase-label search | no matches |
| Prohibited-claim search | no matches |
| Local planning path search | no matches |
| `git diff --check` | passed |

Manual review answers:

| Question | Answer |
| --- | --- |
| Can a proposal reader understand the document without knowing our phase system? | yes |
| Does V5 still preserve the predictive-validity north star? | yes |
| Does V5 still preserve agent tuning as the product/application path? | yes |
| Does the evidence remain preliminary rather than overclaimed? | yes |
| Does the appendix support the argument instead of exposing internal process? | yes |

Step 4 acceptance:

- Text checks passed.
- Manual review answers are yes.
- `git diff --check` passed.

## Step 5: Closeout

Wrote closeout artifacts:

- `experiments/phase1_compiler/reports/proposal_report_v5_phase_label_cleanup_decision.md`
- `experiments/phase1_compiler/results/proposal_report_v5_phase_label_cleanup_decision.json`

Stop label:

```text
proposal_report_v5_phase_label_cleanup_complete
```

Closeout summary:

- V5 removes internal phase framing from the reader-facing proposal while
  preserving V4's argument, evidence, and agent-tuning application path.
- Reviewers now see a coherent project proposal instead of a report about an
  internal phase.
- After the user accepts V5, the next decisions are approval artifact format,
  staffing and duration assumptions, evaluation budget path, and deliverable
  owner categories.

Step 5 acceptance:

- Decision report states that V5 supersedes V4 as the active proposal report.
- Decision report states that reader-facing phase labels were removed.
- Decision report states that V4's agent-tuning integration was preserved.
- Decision report states that raw path traceability moved to an internal
  manifest.
- Decision report states that predictive validity and tuning-loop improvement
  remain unproven.
- Decision report states what remains before the approval artifact can start.
