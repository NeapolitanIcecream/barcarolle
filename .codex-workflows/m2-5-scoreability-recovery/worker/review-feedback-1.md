# Review To Worker

status: issues_found

## Summary
The delivered work covers the requested milestones at a high level: M2.5 uses a real `workspace-diff-v1` git-diff path, preserves the fixed 2 ACUT x 3 RWork live denominator, and truthfully reports live scoreability as failed; R0 separates ACUT-visible statements from audit provenance for all 14 Click tasks; S1 preserves G_score as unavailable-not-zero and avoids predictivity/ranking/admission/license claims.

I found two evidence-hygiene/reproducibility issues to close before this is acceptable.

## Findings
1. M2.5 normalized live results contradict the actual patch/replay evidence for patch-ready cells. In `experiments/core_narrative/tools/m2_5_workspace_diff_runner.py:461`, `enrich_normalized_metadata()` derives `patch_ready` from verifier outcome status (`passed`/`failed`/`timeout`) instead of the collected workspace diff. When clean replay returns `invalid_submission` because `git apply --check` fails, the normalized artifact says the patch was not persisted and replay was not attempted, even though a non-empty workspace diff exists and `verify_command.json` shows `apply_and_verify.py` ran. Example: `experiments/core_narrative/results/normalized/m2_5_workspace_diff_live_20260510__cheap-generic-swe__click__rwork__003__attempt1.json:23` records `verifier_ready_patch_available: false` and `clean_replay_attempted: false` with `patch_size_bytes: 2132`; the same file records the apply failure at line 4, and `experiments/core_narrative/results/raw/m2_5_workspace_diff_live_20260510__cheap-generic-swe__click__rwork__003__attempt1/verify_command.json:1` proves the clean replay command was invoked. The unsafe cell also loses the unsafe attribution in normalized `workspace_diff`: `...click__rwork__006__attempt1.json:52` says `unsafe_content_detected: false`, while its raw adapter result records `unsafe_content_detected: true` at `adapter_result.json:197`. This makes the machine-readable per-cell evidence internally inconsistent even though the aggregate gate fails correctly.

2. The M2.5 report reproduction blocks are not exact/current-state reproducible. `experiments/core_narrative/tools/m2_5_workspace_diff_runner.py:1022` emits only `--mode`, `--run-prefix`, `--output`, and `--report`. The delivered runs used `--force`, and the noop run also used `--skip-noop-check`; the generated reports, for example `experiments/core_narrative/reports/2026-05-10_m2_5_workspace_diff_noop.md:28` and `experiments/core_narrative/reports/2026-05-10_m2_5_workspace_diff_scoreability_recovery.md:28`, omit those flags. Re-running the report command in the current tree will hit existing-artifact blockers, and the noop command is not the same run configuration that produced the delivered JSON/report.

## Required Closure
Fix M2.5 metadata so patch availability/persistence comes from the workspace-diff collection, clean replay attempted comes from whether `verify_patch()` was invoked, and replay failure is represented separately from patch availability. Preserve adapter unsafe-patch attribution in the normalized result when the live adapter rejects a patch before the second collection sees an empty workspace. Add a regression test for a non-empty workspace diff whose clean replay returns `invalid_submission`.

Make M2.5 report reproduction commands exact for the generated artifacts, including `--force` and mode-specific flags such as `--skip-noop-check`, or explicitly label live reruns as budget/env-gated while still giving the exact delivered command.
