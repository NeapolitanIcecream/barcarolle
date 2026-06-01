# Proposal Report V5 Phase-Label Cleanup Process

Status: in progress, 2026-06-01.

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
