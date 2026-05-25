# Phase 1 Attrs H_future Task-Design Audit

Generated: `2026-05-25T01:34:18Z`.

This sidecar uses sanitized committed artifacts only. It does not use hidden verifier material, raw ACUT transcripts, raw public issue/PR bodies, or paid reruns.

## Summary

- Audited tasks: `4`.
- Material statement-quality risk: `4`.
- Probable truncation at old cap: `4`.
- PR-context risk: `1`.
- Scoreable outcomes in these tasks: `1` pass, `6` fail.
- Policy violations remain non-scoreable: `1`.

## Audit Questions

- Verifier/oracle machinery obviously broken: `no evidence from sanitized certification gates`.
- Task scope obviously wrong: `no`; scope metadata still points at target implementation files, though one cell remains a non-scoreable policy violation.
- Solver-facing statements likely incomplete: `yes`; all four audited tasks hit material statement-quality risk.
- Incompleteness plausibly explains failure: `yes for directional interpretation`; it is a confound, not a repaired score.

## Task Findings

### attrs__hist__012

- Source: `issue:680` (`issue`).
- Outcomes: `{'codex_workspace': 'verified_fail', 'kilo_workspace': 'verified_fail'}`; scoreable pass/fail `0/2`, policy violations `0`.
- Mechanism validity: certification gates all pass is `True`; scope metadata matches target non-test files is `True`.
- Statement quality: gate `material_risk`, risk reasons `['body_summary_hit_old_240_char_cap', 'statement_ends_mid_code_fence', 'statement_probably_truncated']`.
- Could statement incompleteness plausibly explain failure: `True`.
- Clean evidence label: `questionable_clean_predictive_evidence`.
- Manual audit label: `valid_but_statement_quality_risk`.
- Rationale: Mechanism and scope look plausible, but the solver-visible body summary ends inside a reproduction snippet at the historical 240-character cap.

### attrs__hist__013

- Source: `pr:687` (`pull_request`).
- Outcomes: `{'codex_workspace': 'verified_fail', 'kilo_workspace': 'verified_fail'}`; scoreable pass/fail `0/2`, policy violations `0`.
- Mechanism validity: certification gates all pass is `True`; scope metadata matches target non-test files is `True`.
- Statement quality: gate `material_risk`, risk reasons `['body_summary_hit_old_240_char_cap', 'statement_probably_truncated', 'pr_context_source']`.
- Could statement incompleteness plausibly explain failure: `True`.
- Clean evidence label: `exclude_in_sensitivity_view`.
- Manual audit label: `questionable_pr_context_and_statement_quality_risk`.
- Rationale: Highest concern: the source is PR-context, the behavior is subtle next-gen frozen subclass handling, and the body summary ends mid-word at the historical 240-character cap.

### attrs__hist__023

- Source: `issue:593` (`issue`).
- Outcomes: `{'codex_workspace': 'verified_fail', 'kilo_workspace': 'verified_pass'}`; scoreable pass/fail `1/1`, policy violations `0`.
- Mechanism validity: certification gates all pass is `True`; scope metadata matches target non-test files is `True`.
- Statement quality: gate `material_risk`, risk reasons `['body_summary_hit_old_240_char_cap', 'statement_ends_mid_code_fence', 'statement_probably_truncated']`.
- Could statement incompleteness plausibly explain failure: `True`.
- Clean evidence label: `questionable_clean_predictive_evidence`.
- Manual audit label: `mostly_valid_but_statement_quality_risk`.
- Rationale: Mechanism and scope look plausible, but the expected-result context is cut at the historical 240-character cap.

### attrs__hist__027

- Source: `issue:766` (`issue`).
- Outcomes: `{'codex_workspace': 'verified_fail', 'kilo_workspace': 'policy_violation'}`; scoreable pass/fail `0/1`, policy violations `1`.
- Mechanism validity: certification gates all pass is `True`; scope metadata matches target non-test files is `True`.
- Statement quality: gate `material_risk`, risk reasons `['body_summary_hit_old_240_char_cap', 'statement_probably_truncated', 'resolve_types_attribs_api_behavior_under_specified']`.
- Could statement incompleteness plausibly explain failure: `True`.
- Clean evidence label: `questionable_clean_predictive_evidence`.
- Manual audit label: `valid_scope_but_under_specified_statement_risk`.
- Rationale: Target scope appears plausible, but the statement likely under-specifies the public resolve_types(..., attribs=...) API behavior.

## Boundary

This audit weakens or qualifies interpretation of the original paid observation. It does not repair the paid result, rerun any cell, relabel the policy violation, or establish predictive validity.
