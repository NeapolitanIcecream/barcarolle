# M2 Unsafe Patch-Artifact Repair

Date: 2026-05-10

## Scope

- Contract: `anchored-search-replace-json-v3`.
- Repair focus: `unsafe_patch_artifact_source_attribution`.
- Fixture replay made no model calls and ran no verifier.

## Prior Live Artifact Inspection

- Status: `inspected`.
- Failure class: `unsafe_generated_text`.
- Unsafe reason counts: `{'full_url': 1}`.
- Patch artifact attribution: `{'classification': 'source_derived_full_url', 'reason_counts': {'full_url': 1}, 'full_url_count': 1, 'full_url_role_counts': {'source_removed': 1}, 'source_derived_full_url_count': 1, 'model_generated_full_url_count': 0, 'ambiguous_full_url_count': 0, 'non_url_reason_counts': {}, 'all_full_urls_source_derived': True, 'all_unsafe_reasons_source_derived': True, 'url_occurrences': [{'line_number': 9, 'diff_line_role': 'source_removed', 'url_sha256': '2f280692da015eee2e9bd27aef6658d569a4b144d68595c90e074d6c13f81bc5', 'url_char_count': 44, 'content_recorded': False}], 'url_occurrences_truncated': False, 'content_recorded': False}`.
- Redacted source match count: `1`.

## Fixture Matrix

| Fixture | Classification | Status | Owner | Class | Patch-ready | Intent |
| --- | --- | --- | --- | --- | ---: | --- |
| `redacted_source_old_safe_replacement_source_url_artifact` | `artifact_policy_source_derived_overbreadth` | `invalid_submission` | `artifact_policy` | `unsafe_generated_text` | `False` | redacted source old text may match raw source once, but source-derived raw URL patch lines are attributed |
| `model_generated_raw_url_replacement_true_positive` | `safety_policy_true_positive` | `invalid_submission` | `model_output` | `unsafe_generated_text` | `False` | model-generated raw URL replacement remains a true unsafe generated-text hit |
| `redaction_placeholder_persistence_rejection` | `redaction_placeholder_persistence_rejected` | `invalid_submission` | `model_output` | `search_replace_redacted_source_mismatch` | `False` | redaction placeholders must not persist into replacement text |
| `missing_raw_artifact_ambiguity` | `provider_or_artifact_ambiguous` | `missing_replay_input` | `infrastructure` | `missing_raw_response_artifact` | `False` | missing provider artifact remains ambiguous rather than treated as generated unsafe text |

## Aggregate

- Classification counts: `{'artifact_policy_source_derived_overbreadth': 1, 'provider_or_artifact_ambiguous': 1, 'redaction_placeholder_persistence_rejected': 1, 'safety_policy_true_positive': 1}`.
- Failure classes: `{'missing_raw_response_artifact': 1, 'search_replace_redacted_source_mismatch': 1, 'unsafe_generated_text': 2}`.
- Patch-ready count: `0`.

## Post-Repair Live Smoke

- Status: `completed`.
- Model call made: `True`.
- Failure classes: `{'unsafe_generated_text': 1}`.
- Blockers: `None`.
- Unsafe diagnostics: `[{'acut_id': 'cheap-generic-swe', 'task_id': 'click__rwork__006', 'status': 'invalid_submission', 'failure_class': 'unsafe_generated_text', 'failure_owner': 'model_output', 'model_call_made': True, 'unsafe_reason_counts': {'full_url': 1}, 'unsafe_content_attribution': {'all_full_urls_source_derived': True, 'all_unsafe_reasons_source_derived': True, 'ambiguous_full_url_count': 0, 'classification': 'source_derived_full_url', 'content_recorded': False, 'full_url_count': 1, 'full_url_role_counts': {'source_removed': 1}, 'model_generated_full_url_count': 0, 'non_url_reason_counts': {}, 'reason_counts': {'full_url': 1}, 'source_derived_full_url_count': 1, 'url_occurrences': [{'content_recorded': False, 'diff_line_role': 'source_removed', 'line_number': 9, 'url_char_count': 44, 'url_sha256': '2f280692da015eee2e9bd27aef6658d569a4b144d68595c90e074d6c13f81bc5'}], 'url_occurrences_truncated': False}, 'patch_artifact_written': False, 'redacted_preview_written': True, 'redacted_source_match_count': 1, 'content_recorded': False}]`.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_unsafe_artifact_repair.py \
  --prior-live-smoke experiments/core_narrative/results/m2_anchored_occurrence_repair_live_smoke_20260510.json \
  --run-prefix m2_unsafe_artifact_repair_20260510 \
  --raw-root experiments/core_narrative/results/raw \
  --workspace-root experiments/core_narrative/workspaces \
  --live-smoke-batch experiments/core_narrative/results/m2_unsafe_artifact_repair_live_smoke_20260510.json \
  --force \
  --output experiments/core_narrative/results/m2_unsafe_artifact_repair_20260510.json \
  --report experiments/core_narrative/reports/2026-05-10_m2_unsafe_artifact_repair_report.md
```

## Claim Boundaries

This report does not claim M2 passed, ranking reversal, task-solving improvement, capability uplift, G_score predictivity, G0-G5 outcomes, license, admission, or authorization. It only reports anchored-contract unsafe artifact attribution and post-repair live-smoke availability.
