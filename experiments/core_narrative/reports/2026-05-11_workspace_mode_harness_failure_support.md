# Workspace-Mode Harness Failure Support

Date: 2026-05-11

Status: delivered as focused no-model coverage for the minimal workspace-mode execution chain.

## Scope

This report evaluates the harness-induced failure classes that motivated the
workspace-mode chain in `experiments/core_narrative`. It does not claim
task-solving improvement, admission, license, scorecard redesign, product-grade
redaction, or live batch recovery.

The new execution model is:

1. Prepare an isolated run workspace from the task base commit.
2. Expose only ACUT-visible task material in `.core_narrative/task.json`.
3. Let the ACUT naturally read, write, and run commands in that workspace.
4. Extract the candidate patch from final workspace state against the recorded
   `BASE_REF`.
5. Replay the patch in a fresh verification workspace from the same base.
6. Inject and run the hidden verifier only in the verification workspace.

## Support Matrix

| Previous harness failure mode | Current support | Evidence |
| --- | --- | --- |
| ACUT edits a tracked file but does not emit structured patch JSON | Supported | `test_tracked_file_edit_is_replayed_in_fresh_workspace_and_verified` extracts `git diff --binary --no-ext-diff --full-index --unified=3 "$BASE_REF" --`, replays it in a fresh workspace, and verifies pass. |
| ACUT produces no scoreable workspace diff | Supported | `test_no_workspace_diff_returns_no_diff_without_verifier` returns `no_diff` and does not run the verifier. |
| Candidate patch cannot apply in the fresh workspace | Supported | `test_invalid_candidate_patch_maps_to_patch_apply_error` returns `patch_apply_error`, distinct from `verified_fail`. |
| Fresh verification workspace base tree diverges from recorded run `BASE_TREE` | Supported | `test_verify_base_tree_mismatch_blocks_replay_before_hidden_verifier` returns `base_tree_mismatch` before patch replay or hidden verifier execution. |
| Hidden verifier or hidden tests visible to ACUT | Supported | `test_hidden_verifier_material_is_not_visible_in_acut_run_workspace` asserts verifier files and hidden marker files are absent from the run workspace. |
| ACUT creates an untracked source file and old patch extraction drops it | Supported for regular files | `test_untracked_source_file_is_deterministically_included_in_candidate_patch` includes regular untracked files with sorted intent-to-add handling. Non-regular files are recorded as `rejected_untracked_file`. |
| Harness-generated files pollute candidate patch | Supported | `test_harness_generated_untracked_files_do_not_enter_candidate_patch` excludes `.core_narrative/`, `.venv/`, `.pytest_cache/`, `__pycache__/`, `.egg-info/`, and related harness paths while preserving source edits. |
| Workspace preparation wrapper summary overwrites the child prepare payload | Supported | `test_prepare_result_preserves_prepare_payload_and_command_artifact` keeps distinct command and payload artifacts and asserts the prepare payload contains `status`, `task_package_path`, `statement_path`, and `warnings`. |
| ACUT exits nonzero after leaving a valid diff | Supported | `test_nonzero_acut_exit_does_not_override_successful_fresh_verification` returns `verified_pass` after fresh replay and records `acut_command_status=nonzero`. |
| ACUT changes HEAD or creates a commit | Supported | `test_head_drift_is_recorded_and_diff_still_uses_base_ref` records `head_drifted=true` and still extracts from the original `BASE_REF`. |
| ACUT command cannot launch | Supported as infrastructure boundary | `test_missing_acut_executable_maps_to_acut_command_error` returns `acut_command_error` without attempting verifier replay. |
| Candidate patch extraction fails after the ACUT starts | Supported as workspace infrastructure boundary | `test_candidate_patch_extraction_failure_after_acut_start_is_not_command_error` returns `candidate_patch_extraction_error`, preserving `acut_command_error` for launch failures. |

## Boundaries

- The evidence above is no-model harness coverage, not a live ACUT recovery
  batch.
- Fresh replay and hidden verifier semantics remain delegated to
  `apply_and_verify.py`; this change only replaces the ACUT artifact acquisition
  interface.
- Run-workspace local test output is captured as auxiliary evidence only. Final
  scoring comes from the fresh verification workspace.
- Unsafe or scope-violation status is only emitted when the existing checker can
  clearly classify the candidate patch.

## Verification

Commands run:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/test_workspace_mode_runner.py
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments/core_narrative/tools/test_workspace_mode_runner.py experiments/core_narrative/tools/test_run_task.py experiments/core_narrative/tools/test_codex_nfl_experiment_runner.py experiments/core_narrative/tools/test_m2_5_workspace_diff_runner.py
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest discover -s experiments/core_narrative/tools -p 'test_*.py'
PYTHONPYCACHEPREFIX=/tmp/barcarolle-core-narrative-pycache python3 -m py_compile experiments/core_narrative/tools/workspace_mode_runner.py experiments/core_narrative/tools/run_task.py experiments/core_narrative/tools/apply_and_verify.py experiments/core_narrative/tools/test_workspace_mode_runner.py
```

Observed results:

- `test_workspace_mode_runner.py`: passed, 12 tests.
- Focused compatibility set: passed, 47 tests.
- Full `experiments/core_narrative/tools` unittest discovery: passed, 218 tests.
- `py_compile`: passed with `PYTHONPYCACHEPREFIX`.
