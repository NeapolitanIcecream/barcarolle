# Phase 1 Reference-Pass Failure Audit Decision

Status: completed.

1. Was there a local validation-code bug? No local validation-code bug was found in the sampled evidence.
2. If yes, what was fixed and how was it tested? No production validation fix was applied in this run; the audit tool tests cover parsing, classification, and raw-output redaction.
3. If no, what is the main reason reference_pass failed so often? The sampled evidence points to historical environment model gaps: dependency version drift, pytest config incompatibility, and Python-version drift. Unsampled unique signatures remain unknown.
4. How many tasks changed category? 76 reference-pass failures were reclassified from a single gate label into the taxonomy counts below.
5. Does this reopen attrs/boltons supply expansion? two_repo_supply_blocker_still_exists_screen_new_repo.
6. What should the coordinating session decide next? Use the categories below; no follow-up runbook was drafted by this worker.

## Root Cause Counts

| label | count |
| --- | ---: |
| dependency_version_drift | 1 |
| pytest_collection_or_config_error | 5 |
| python_version_drift | 6 |
| unclassified_reference_fail | 64 |

## Recommended Next Action Categories

- design_historical_environment_synthesis_or_reclassification_policy
- sample_more_unique_failure_signatures_before_overclaiming
- continue_new_repo_screen_if_counts_remain_below_30

## Verification

- `uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_reference_pass_failure_audit.py experiments/phase1_compiler/tests/test_phase1_two_repo_certified_supply_expansion.py -q`: passed, 13 tests.
- `uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q`: passed, 178 tests.
- `git diff --check`: passed.
