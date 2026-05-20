# 2026-05-08 Codex NFL Output-Contract Replay Repair

status: `delivered`
updated: 2026-05-08T11:54:00Z
repo: `/Users/chenmohan/gits/barcarolle`
branch: `codex/nfl-output-contract-replay`

## Summary

Gate 1 remains strict and now passes for the targeted blocker cell. Revision 1 proved the captured `frontier-click-specialist x click__rbench__003` response was a model-output `invalid_unified_diff`. Continuation 2 then strengthened the live output contract to `anchored-search-replace-json-v3` and ran exactly one new targeted live cell. That v3 live cell produced `search_replace_edits`, generated a patch, and passed verifier replay on a separate clean workspace.

Continuation 3 then ran the controlled Click 004-008 expansion with the same v3 output contract and the four core ACUTs only. The 20 primary live cells completed with 11 passed, 5 verifier-replay failed, 4 model-output invalid submissions, 0 infra failures, and 0 timeouts. No extra attempts or non-Click families were run.

Continuation 5 made no live model calls and did not alter the historical Click 004-008 normalized artifacts. The repaired-verifier replay of the three existing Click 005 patch artifacts passed all three cells, so those historical Click 005 verifier failures should now be treated as verifier fixture defects. The Click 005 `cheap-click-specialist` invalid submission remains a model-output contract failure.

Continuation 6 ran only the five reviewer-approved attempt-2 retry cells. Click 005 `cheap-click-specialist` passed after the anchor/context repair. Click 008 did not improve after context hardening: the four retry cells produced 0 passed, 1 verifier-replay failure, and 3 model-output invalid submissions. No infra failures, timeouts, credential blockers, or provider quota/funds blockers occurred.

Continuation 7 made no live model calls and inspected only existing Click 008 attempt-1/attempt-2 artifacts plus relevant local runner code/tests. It found the attempt-2 Click 008 prompt package was contaminated before model prompting because no-op verification ran in the same workspace later used for prompt context, and the Click 008 verifier copies hidden tests into that workspace. The local engineering fix is now in place: no-op verification uses a separately prepared `__noop` workspace, preserving strict Gate 1 and clean replay semantics.

Continuation 8 made no live model calls and ran a bounded Click 008 prompt-packaging dry-run after that fix. The no-op verifier used a `__noop` workspace, the direct runner prompt package used a separate runner workspace, and the prompt retained focused `src/click/core.py` `class Option(Parameter):` context while excluding hidden verifier test names and the hidden `tests/test_termui.py` SHA. The real `cost_ledger.jsonl` remained unchanged at 72 records.

## Implementation

- `openclaw_direct_runner.py` now advertises `anchored-search-replace-json-v3`.
- The live prompt requests a single-key `{"edits": [...]}` JSON object and explicitly rejects `unified_diff`, raw diff text, markdown, prose, and extra top-level keys.
- Prompt snapshots and live request profiles now include `output_contract_schema`.
- Edit bundles with unsupported top-level keys fail as `output_contract_violation`.
- The earlier atomic search/replace, exact-anchor, and invalid unified-diff diagnostics remain in place.
- Continuation 5 tightened the v3 prompt guidance: models are told to omit anchors when `old` is unique, use anchors only for repeated `old` strings, and treat non-matching anchors as invalid even when `old` occurs once.
- Anchor mismatch and old-occurrence mismatch failures now carry machine-readable diagnostics including `old_text_sha256`, `old_text_char_count`, a diagnostic code, and an actionable recommendation.
- Prompt-required Click tasks with four context files now use compact per-file budgeting plus focused exact source excerpts. For Click 008, the dry-run prompt snapshot confirmed `src/click/core.py` includes a focused `class Option(Parameter):` excerpt even though the full file is truncated.
- Continuation 7 isolates pre-model no-op verification in a separate `run_id__noop` workspace so verifier fixture mutations cannot leak into the runner workspace used for prompt packaging.
- Batch result payloads now record `noop_workspace`, `noop_prepare`, and `noop_install` alongside the existing runner and verify workspace evidence.
- Continuation 8 locally verified that isolation on Click 008 with a no-model dry run; no source code changes were needed.

## Verification

Commands run:

```text
jq empty experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_repaired_verifier_replay_20260508.json
python3 -m py_compile experiments/core_narrative/tools/openclaw_direct_runner.py experiments/core_narrative/tools/test_openclaw_direct_runner.py
python3 -m pytest -q experiments/core_narrative/tools/test_openclaw_direct_runner.py -k 'prompt_contract or prompt_required_context or anchor_mismatch_diagnostics or old_occurrence_mismatch_diagnostics'
python3 -m pytest -q experiments/core_narrative/tools/test_openclaw_direct_runner.py
python3 -m pytest -q experiments/core_narrative/tools/test_codex_nfl_direct_runner.py experiments/core_narrative/tools/test_codex_nfl_experiment_runner.py
python3 experiments/core_narrative/tools/codex_nfl_direct_runner.py --workspace experiments/core_narrative/workspaces/codex_nfl_output_contract_v3_click_004_008_sanity__click__rbench__008 --task experiments/core_narrative/tasks/click/rbench/click__rbench__008/task.yaml --acut experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml --attempt 1 --run-id local_click008_context_packaging_dryrun --artifact-dir /tmp/.../artifacts --output /tmp/.../runner.json --llm-ledger /tmp/.../ledger.jsonl --projected-cost-usd 0 --dry-run --context-path src/click/core.py --context-path src/click/parser.py --context-path tests/test_options.py --context-path tests/test_termui.py
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments.core_narrative.tools.test_openclaw_direct_runner.OpenClawDirectRunnerTests.test_prompt_contract_requests_only_anchored_edit_json experiments.core_narrative.tools.test_openclaw_direct_runner.OpenClawDirectRunnerTests.test_edit_bundle_with_extra_top_level_keys_is_contract_violation experiments.core_narrative.tools.test_openclaw_direct_runner.OpenClawDirectRunnerTests.test_live_model_uses_responses_payload_for_responses_endpoint
python3 -m py_compile experiments/core_narrative/tools/openclaw_direct_runner.py experiments/core_narrative/tools/codex_nfl_direct_runner.py experiments/core_narrative/tools/codex_nfl_experiment_runner.py
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments.core_narrative.tools.test_openclaw_direct_runner experiments.core_narrative.tools.test_codex_nfl_direct_runner experiments.core_narrative.tools.test_codex_nfl_experiment_runner
python3 -m py_compile experiments/core_narrative/tools/openclaw_direct_runner.py experiments/core_narrative/tools/codex_nfl_direct_runner.py experiments/core_narrative/tools/codex_nfl_experiment_runner.py experiments/core_narrative/tools/llm_budget_gate.py experiments/core_narrative/tools/reconcile_cost_accounting.py experiments/core_narrative/tools/summarize_results.py
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments.core_narrative.tools.test_openclaw_direct_runner.OpenClawDirectRunnerTests.test_prompt_contract_requests_only_anchored_edit_json experiments.core_narrative.tools.test_openclaw_direct_runner.OpenClawDirectRunnerTests.test_edit_bundle_with_extra_top_level_keys_is_contract_violation experiments.core_narrative.tools.test_openclaw_direct_runner.OpenClawDirectRunnerTests.test_live_model_uses_responses_payload_for_responses_endpoint experiments.core_narrative.tools.test_codex_nfl_direct_runner.CodexNflDirectRunnerTests.test_task003_style_ambiguous_edit_is_invalid_without_partial_mutation
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/llm_budget_gate.py --ledger experiments/core_narrative/results/cost_ledger.jsonl --projected-cost-usd 40 --coordinator-decision-ref experiments/core_narrative/results/codex_nfl_output_contract_v3_gate1_decision_20260508.json --acut-id frontier-click-specialist --split rbench --attempt 1 --output experiments/core_narrative/results/codex_nfl_output_contract_v3_click_004_008_budget_gate_20260508.json
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/codex_nfl_experiment_runner.py --run-prefix codex_nfl_output_contract_v3_replay_20260508 --tasks click__rbench__003 --acuts frontier-click-specialist --attempt 1 --mode mock --mock-response experiments/core_narrative/results/raw/codex_nfl_output_contract_repair_replay_source_20260508/captured_live_model_text.redacted.txt --llm-ledger experiments/core_narrative/results/cost_ledger.jsonl --output experiments/core_narrative/results/codex_nfl_output_contract_v3_replay_targeted_20260508.json --install-timeout-seconds 240 --runner-timeout-seconds 360
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/codex_nfl_experiment_runner.py --run-prefix codex_nfl_output_contract_v3_live_20260508 --tasks click__rbench__003 --acuts frontier-click-specialist --attempt 1 --mode live --llm-ledger experiments/core_narrative/results/cost_ledger.jsonl --output experiments/core_narrative/results/codex_nfl_output_contract_v3_live_targeted_20260508.json --install-timeout-seconds 240 --runner-timeout-seconds 360
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/summarize_results.py experiments/core_narrative/results/normalized/codex_nfl_output_contract_v3_live_20260508__frontier-click-specialist__click__rbench__003__attempt1.json --output experiments/core_narrative/results/normalized/codex_nfl_output_contract_v3_summary_20260508.json
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/reconcile_cost_accounting.py --ledger experiments/core_narrative/results/cost_ledger.jsonl --output experiments/core_narrative/results/codex_nfl_output_contract_v3_cost_reconciliation_2026-05-08.json
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/codex_nfl_experiment_runner.py --run-prefix codex_nfl_output_contract_v3_click_004_008_20260508 --tasks click__rbench__004 click__rbench__005 click__rbench__006 click__rbench__007 click__rbench__008 --acuts cheap-generic-swe frontier-generic-swe cheap-click-specialist frontier-click-specialist --attempt 1 --mode live --llm-ledger experiments/core_narrative/results/cost_ledger.jsonl --coordinator-decision-ref experiments/core_narrative/results/codex_nfl_output_contract_v3_gate1_decision_20260508.json --output experiments/core_narrative/results/codex_nfl_output_contract_v3_click_004_008_live_20260508.json --install-timeout-seconds 240 --runner-timeout-seconds 360
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/summarize_results.py experiments/core_narrative/results/normalized/codex_nfl_output_contract_v3_click_004_008_20260508__*.json --output experiments/core_narrative/results/normalized/codex_nfl_output_contract_v3_click_004_008_summary_20260508.json
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/reconcile_cost_accounting.py --ledger experiments/core_narrative/results/cost_ledger.jsonl --output experiments/core_narrative/results/codex_nfl_output_contract_v3_click_004_008_cost_reconciliation_2026-05-08.json
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments.core_narrative.tools.test_codex_nfl_experiment_runner.CodexNflExperimentRunnerTests.test_run_one_noop_verify_uses_separate_workspace_before_prompting
python3 -m py_compile experiments/core_narrative/tools/codex_nfl_experiment_runner.py experiments/core_narrative/tools/test_codex_nfl_experiment_runner.py
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments.core_narrative.tools.test_codex_nfl_experiment_runner
jq empty experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_attempt2_failure_analysis_20260508.json
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/codex_nfl_experiment_runner.py --run-prefix codex_nfl_output_contract_v3_click_008_prompt_packaging_verification_complete_20260508 --tasks click__rbench__008 --acuts cheap-generic-swe --attempt 1 --mode dry-run --llm-ledger /tmp/barcarolle_click008_prompt_packaging_verification_complete_ledger.jsonl --output /tmp/barcarolle_click008_prompt_packaging_verification_complete_batch.json --install-timeout-seconds 240 --runner-timeout-seconds 360
jq empty experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_prompt_packaging_verification_20260508.json
jq -e '.decision.status == "passed" and .workspaces.separate == true and .prompt_package_evidence.core_option_context.present == true and .prompt_package_evidence.hidden_context_absence.absent == true and .ledger_evidence.real_cost_ledger_unchanged == true and .checks.model_call_made == false and .checks.direct_runner_dry_run_completed == true' experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_prompt_packaging_verification_20260508.json
```

Regression coverage added or preserved:

- Prompt contract requests anchored edit JSON rather than hand-written diffs.
- Edit-bundle JSON with extra top-level keys is rejected as `output_contract_violation`.
- Click 003-style late ambiguous edit cannot leave earlier edits applied.
- Exact anchors can disambiguate repeated `old` strings and generate a patch.
- Corrupt unified diffs remain model-output invalid submissions, not infrastructure failures.

The earlier local runner suite passed 30 tests before Continuation 5.

Continuation 5 focused checks passed: 5 focused direct-runner tests, the full direct-runner file (`22 passed`), and the Codex direct/batch runner files (`12 passed`). The no-model Click 008 dry run produced a prompt snapshot with `effective_max_file_chars=25000`, `prompt_truncated=false`, and a focused `src/click/core.py` `class Option(Parameter):` excerpt.

## Targeted Evidence

No-new-spend replay of old captured text:

| Field | Value |
|---|---|
| Run | `codex_nfl_output_contract_v3_replay_20260508__frontier-click-specialist__click__rbench__003__attempt1` |
| Mode | `mock` replay |
| New model call | `false` |
| Status | `invalid_submission` |
| Failure owner | `model_output` |
| Failure class | `invalid_unified_diff` |
| Patch ready | `false` |
| Clean patch replay attempted | `false` |

New v3 live cell:

| Field | Value |
|---|---|
| Run | `codex_nfl_output_contract_v3_live_20260508__frontier-click-specialist__click__rbench__003__attempt1` |
| Status | `passed` |
| Patch kind | `search_replace_edits` |
| Patch ready | `true` |
| Clean patch replay attempted | `true` |
| Separate replay workspace | `true` |
| Verifier exit code | `0` |
| Changed paths | `click/core.py`, `click/termui.py` |
| Provider usage cost | `0.232660` USD |
| Ledger cumulative after live run | `2.391728` USD |

## Gate 1 Re-Decision

Gate artifact: `experiments/core_narrative/results/codex_nfl_output_contract_v3_gate1_decision_20260508.json`.

| Condition | Result |
|---|---|
| `infra_failed_rate == 0` | pass |
| `verifier_repair_after_live == false` | pass |
| `unclassified_failure_rate <= 20%` | pass |
| `all_runs_have_clean_patch_replay == true` | pass |
| `frontier_click_specialist_attempt1_completed == true` | pass |
| `meaningful_film_contrast_exists == true` | pass |

Decision: Gate 1 can pass for the targeted blocker cell. That decision justified the subsequent controlled Click 004-008 expansion recorded below; Gate 1 was not weakened for the expansion.

## Click 004-008 Expansion

Live batch: `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_004_008_live_20260508.json`.

| Field | Value |
|---|---|
| Tasks | `click__rbench__004` through `click__rbench__008` |
| ACUTs | `cheap-generic-swe`, `frontier-generic-swe`, `cheap-click-specialist`, `frontier-click-specialist` |
| Attempt | `1` only |
| Mode | `live` |
| Result count | `20` |
| Passed | `11` |
| Failed verifier replay | `5` |
| Model-output invalid submissions | `4` |
| Infra failures | `0` |
| Timeouts | `0` |
| Pass rate | `0.55` |

By task:

| Task | Outcome |
|---|---|
| `click__rbench__004` | `4 passed` |
| `click__rbench__005` | `3 failed`, `1 invalid_submission` |
| `click__rbench__006` | `4 passed` |
| `click__rbench__007` | `3 passed`, `1 invalid_submission` |
| `click__rbench__008` | `2 failed`, `2 invalid_submission` |

By ACUT:

| ACUT | Outcome |
|---|---|
| `cheap-generic-swe` | `2 passed`, `1 failed`, `2 invalid_submission` |
| `frontier-generic-swe` | `3 passed`, `1 failed`, `1 invalid_submission` |
| `cheap-click-specialist` | `3 passed`, `1 failed`, `1 invalid_submission` |
| `frontier-click-specialist` | `3 passed`, `2 failed` |

Failure taxonomy:

| Group | Count | Notes |
|---|---:|---|
| Model-output invalid submission | `4` | `2 search_replace_anchor_mismatch`, `2 search_replace_old_occurrence_mismatch` |
| Verifier replay failed | `5` | Nonzero verifier exits after a patch was generated and clean-replayed; exit-code distribution was `3` with code `4` and `2` with code `1` |
| Infrastructure failure | `0` | None |
| Timeout | `0` | None |

Artifact checks passed: all 20 provider responses have `provider_response.redacted.json`, all 20 prompt snapshots are present, all 20 provider calls have cost-ledger records, and all 16 patch-ready cells attempted clean replay in a separate workspace.

## No-New-Spend Failure Triage

Triage artifact: `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_008_failure_triage_20260508.json`.

This triage inspected only existing Click 005 and Click 008 normalized results, redacted provider responses, prompt snapshots, submission patches where present, runner summaries, verifier outputs, and task/verifier fixtures. It made no live model calls, retries, extra attempts, broad repo expansion, or Click 009+ runs.

Box score in this scope:

| Task | Box-score outcome |
|---|---|
| `click__rbench__005` | `3 failed`, `1 invalid_submission`; verifier-replay failures all exited with code `4` |
| `click__rbench__008` | `2 failed`, `2 invalid_submission`; verifier-replay failures both exited with code `1` |

Film evidence changes the interpretation:

| Cluster | Cells | Owner/class | Readiness | Evidence-based interpretation |
|---|---:|---|---|---|
| Click 005 verifier collection | `3` | task/verifier semantics | patch-ready | Verifier stderr says pytest could not find `test_case_insensitive_choice_returned_exactly`; stdout says no tests ran. These should not be counted as ordinary model inability without a no-live replay against a repaired verifier. |
| Click 005 anchor mismatch | `1` | model output contract | not patch-ready | The `cheap-click-specialist` response had a unique `old` string in `click/types.py` but non-matching anchors, so no verifier replay occurred. This points to anchor-instruction/output-contract repair. |
| Click 008 prompt_required failures | `2` | ordinary incomplete implementation | patch-ready | Both verifier traces fail at `Option` construction with unexpected `prompt_required`; patches did not add the constructor support required by the task. |
| Click 008 invalid submissions | `2` | model output contract | not patch-ready | One response had a unique parser old string but bad anchor context; the other proposed a core.py old string that occurred zero times. Click 008 prompt snapshots also show `src/click/core.py` was truncated. |

Local verifier repair applied: `experiments/core_narrative/tasks/click/rbench/click__rbench__005/verifier/hidden/tests/test_options.py` now defines `test_case_insensitive_choice_returned_exactly`, matching the existing verifier/run.sh command and checking exact returned choice values. Historical normalized results still record the pre-repair verifier digest and original exit-code-4 outcomes; the repair does not change the recorded box score.

Continuation 5 completed that next step.

## Repaired-Verifier Replay

Replay artifact: `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_repaired_verifier_replay_20260508.json`.

The historical Click 005 box score remains unchanged: `3 failed`, `1 invalid_submission`, `0 passed` in the original Click 004-008 expansion. The replay is a separate no-new-spend artifact against the current repaired verifier.

| Cell | Source patch | Repaired-verifier replay |
|---|---|---|
| `cheap-generic-swe x click__rbench__005 x attempt1` | existing `submission.patch` from Click 004-008 expansion | `passed`, verifier exit code `0` |
| `frontier-generic-swe x click__rbench__005 x attempt1` | existing `submission.patch` from Click 004-008 expansion | `passed`, verifier exit code `0` |
| `frontier-click-specialist x click__rbench__005 x attempt1` | existing `submission.patch` from Click 004-008 expansion | `passed`, verifier exit code `0` |

Classification after replay:

| Click 005 group | Current interpretation |
|---|---|
| Three historical patch-ready verifier failures | Verifier fixture defects. Their existing patches pass once `test_case_insensitive_choice_returned_exactly` exists. |
| `cheap-click-specialist` invalid submission | Model-output contract failure. The response supplied non-matching anchors and never reached verifier replay. |
| Replay caveats | None for the three patch-ready cells. Replay used clean prepared workspaces, existing patches only, and no model/API calls. |

## Attempt-2 Live Retry

Live batch summary: `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_008_attempt2_live_20260508.json`.

Preflight passed before any live call: required LLM env vars were present, the cost ledger was writable with 67 records and no read errors, projected five-cell attempt-2 cost was `9.000000` USD, projected cumulative cost was `13.879213` USD, and the coordinator decision reference for attempt 2 was present.

Repaired attempt-1 interpretation after Click 005 replay:

| Group | Interpretation |
|---|---|
| Three Click 005 attempt-1 patch-ready verifier failures | Verifier fixture defects. All three existing patches passed against the repaired verifier. |
| Click 005 `cheap-click-specialist` attempt-1 invalid submission | Model-output contract failure. The response supplied non-matching anchors and never reached verifier replay. |
| Historical box score | Unchanged: Click 005 remains `3 failed`, `1 invalid_submission`, `0 passed` in the original expansion artifacts. |

Five-cell attempt-2 result table:

| Task | ACUT | Status | Failure class / verifier |
|---|---|---|---|
| `click__rbench__005` | `cheap-click-specialist` | `passed` | Patch ready; clean replay verifier exit `0` |
| `click__rbench__008` | `cheap-generic-swe` | `invalid_submission` | `search_replace_anchor_mismatch` in `src/click/parser.py` |
| `click__rbench__008` | `frontier-generic-swe` | `invalid_submission` | `search_replace_old_occurrence_mismatch` in `src/click/core.py` |
| `click__rbench__008` | `cheap-click-specialist` | `failed` | Patch ready; clean replay verifier exit `1`; verifier still rejects `prompt_required` as an unexpected keyword |
| `click__rbench__008` | `frontier-click-specialist` | `invalid_submission` | `search_replace_old_occurrence_mismatch` in `src/click/core.py` |

Interpretation:

| Question | Answer |
|---|---|
| Did the Click 005 invalid-submission repair succeed? | Yes. The only remaining Click 005 non-passing cell from attempt 1 passed on attempt 2 with strict clean replay. |
| Did Click 008 improve after context hardening? | No. The prompt packaging mechanically improved and included a focused `class Option(Parameter):` excerpt, but live outcomes did not improve: attempt 2 produced `0 passed`, `1 failed`, and `3 invalid_submission` versus attempt 1's `0 passed`, `2 failed`, and `2 invalid_submission`. |
| Should the next step be more live retries, no-spend analysis, or PR packaging? | No-spend analysis. More live retries are not justified until the three new Click 008 invalid submissions and the remaining `prompt_required` verifier failure are triaged from existing artifacts. PR packaging should wait for that interpretation or an explicit stop decision. |

Attempt-2 verification:

| Check | Result |
|---|---|
| JSON validation for new artifacts | Passed |
| Normalized result count under retry prefix | `5` |
| Redacted provider response count under retry prefix | `5` |
| Prompt snapshot count under retry prefix | `5` |
| Cost ledger records under retry prefix | `5` |
| Focused runner tests | Not run; no code changes were made in continuation 6 |

## Click 008 Attempt-2 Failure Analysis

Analysis artifact: `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_attempt2_failure_analysis_20260508.json`.

What changed before attempt 2: anchor guidance and mismatch diagnostics were tightened, prompt-required Click tasks used compact context budgeting, and Click 008 prompt snapshots included a focused `src/click/core.py` `class Option(Parameter):` excerpt. That was the intended hardening. The unintended issue was that the batch runner executed no-op verification before prompt packaging in the same workspace used by the direct runner.

What improved and what did not:

| Comparison | Attempt 1 | Attempt 2 |
|---|---:|---:|
| Click 008 passed | `0` | `0` |
| Click 008 verifier-replay failed | `2` | `1` |
| Click 008 invalid submissions | `2` | `3` |
| Infra failures/timeouts | `0` | `0` |

Observed attempt-2 failures were mostly output-contract failures: `cheap-generic-swe` had a `search_replace_anchor_mismatch`, `frontier-generic-swe` and `frontier-click-specialist` had `search_replace_old_occurrence_mismatch`, and `cheap-click-specialist` generated a patch but still failed verifier replay with `TypeError: __init__() got an unexpected keyword argument 'prompt_required'`.

The deeper experiment-validity cause is context packaging. Click 008 `verifier/run.sh` copies files from `verifier/hidden` into the workspace before running pytest. In attempt 2, `noop_verify_command.json` and `direct_runner_command.json` used the same workspace, and no-op verification completed immediately before the direct runner started. The prompt snapshots then recorded `tests/test_termui.py` with the hidden verifier SHA and contained `test_prompt_required_with_required` / `test_prompt_required_false`. A clean prepared sanity workspace has a different `tests/test_termui.py` SHA and does not contain those tests. Focused `Option` context was present, so this was not a missing-Option-context problem.

Classification:

| Question | Answer |
|---|---|
| Why did Click 008 fail to improve? | The attempt-2 prompt package was contaminated by hidden verifier test files before model prompting, so it is not clean evidence that the prompt/context hardening failed. The scoreable cells still failed through model-output contract errors and one incomplete implementation. |
| Primary remaining failure type in the observed box score | `3/4` model-output contract failures and `1/4` ordinary incomplete implementation failure. |
| Primary root cause for experiment validity | Context-packaging failure caused by same-workspace no-op verification before prompt packaging. |
| Task/verifier-semantics issue? | No evidence of a Click 008 verifier defect like Click 005. The verifier ran and exposed incomplete `prompt_required` support in the patch-ready cell. |
| Local engineering fix exists? | Yes. No-op verification now runs in a separately prepared `run_id__noop` workspace; strict invalid-submission classification and clean replay are unchanged. |
| Further live spend justified now? | The local packaging threshold is now met. Live spend is technically defensible only as an explicitly approved, bounded Click 008 attempt-3 measurement across the four core ACUTs; no broader Click 009+ or speculative spend is justified by this pass. |

Minimal future live run, only if explicitly approved after this evidence threshold: `click__rbench__008` only, four core ACUTs only, attempt 3 only.

## Click 008 Prompt-Packaging Verification

Verification artifact: `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_prompt_packaging_verification_20260508.json`.

Continuation 8 ran the batch runner in `--mode dry-run` for `click__rbench__008 x cheap-generic-swe`. The completed dry run made no model/provider call: `model_call_made=false`, direct runner status `dry_run_completed`, and the only ledger record was a scratch `dry_run_no_model` record under `/tmp`, not the real cost ledger.

| Check | Result |
|---|---|
| No-op workspace | `...prompt_packaging_verification_complete_20260508__cheap-generic-swe__click__rbench__008__attempt1__noop` |
| Direct runner prompt workspace | `...prompt_packaging_verification_complete_20260508__cheap-generic-swe__click__rbench__008__attempt1` |
| Workspaces separate | `true` |
| No-op `tests/test_termui.py` SHA | `385d3e676c73a1b0b49a184e07eceb2160f5a79403a4cff07b1d58d41544e359` |
| Runner prompt `tests/test_termui.py` SHA | `2ba18dfb4f62eca1ec5fd8eb4503a084b12db5ee4b3e9b62e9b4e6f2b543675a` |
| Prompt `class Option(Parameter):` hits | `2` |
| Prompt hidden test-name hits | `0` |
| Prompt hidden SHA hits | `0` |
| Real `cost_ledger.jsonl` count before/after | `72` / `72` |

The Click 008 prompt-packaging fix is now locally verified. No further local engineering fix is required for the hidden-test contamination issue.

## Cost

The v3 replay made no model call and appended no ledger record. The v3 targeted live cell appended one provider-usage ledger record. The Click 004-008 expansion appended 20 additional provider-usage ledger records. The attempt-2 retry appended 5 provider-usage ledger records.

| Field | Value |
|---|---|
| Ledger records before live | `46` |
| Ledger records after live | `47` |
| New live provider usage cost | `0.232660` USD |
| New cumulative ledger/provider-usage estimate | `2.391728` USD |
| Expansion ledger records before | `47` |
| Expansion ledger records after | `67` |
| Expansion provider usage cost | `2.487485` USD |
| Expansion cumulative ledger/provider-usage estimate | `4.879213` USD |
| Attempt-2 retry ledger records before | `67` |
| Attempt-2 retry ledger records after | `72` |
| Attempt-2 retry provider-usage cost | `0.986359` USD |
| Attempt-2 retry tokens | `94,266` input, `71,759` output |
| Attempt-2 cumulative ledger/provider-usage estimate | `5.865572` USD |
| Continuation 8 real ledger records before/after | `72` / `72` |
| Continuation 8 real ledger records appended | `0` |
| Actual provider billed cost | unknown, no invoice-backed `actual_cost_usd` record |

## Evidence

| Purpose | Path |
|---|---|
| V3 targeted summary | `experiments/core_narrative/results/codex_nfl_output_contract_v3_targeted_summary_20260508.json` |
| V3 Gate 1 decision | `experiments/core_narrative/results/codex_nfl_output_contract_v3_gate1_decision_20260508.json` |
| V3 no-new-spend replay batch | `experiments/core_narrative/results/codex_nfl_output_contract_v3_replay_targeted_20260508.json` |
| V3 no-new-spend replay normalized result | `experiments/core_narrative/results/normalized/codex_nfl_output_contract_v3_replay_20260508__frontier-click-specialist__click__rbench__003__attempt1.json` |
| V3 live batch | `experiments/core_narrative/results/codex_nfl_output_contract_v3_live_targeted_20260508.json` |
| V3 live normalized result | `experiments/core_narrative/results/normalized/codex_nfl_output_contract_v3_live_20260508__frontier-click-specialist__click__rbench__003__attempt1.json` |
| V3 live runner result | `experiments/core_narrative/results/raw/codex_nfl_output_contract_v3_live_20260508__frontier-click-specialist__click__rbench__003__attempt1/runner_result.json` |
| V3 live patch | `experiments/core_narrative/results/raw/codex_nfl_output_contract_v3_live_20260508__frontier-click-specialist__click__rbench__003__attempt1/submission.patch` |
| V3 normalized summary | `experiments/core_narrative/results/normalized/codex_nfl_output_contract_v3_summary_20260508.json` |
| V3 cost reconciliation | `experiments/core_narrative/results/codex_nfl_output_contract_v3_cost_reconciliation_2026-05-08.json` |
| Click 004-008 pre-expansion budget gate | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_004_008_budget_gate_20260508.json` |
| Click 004-008 live batch | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_004_008_live_20260508.json` |
| Click 004-008 normalized summary | `experiments/core_narrative/results/normalized/codex_nfl_output_contract_v3_click_004_008_summary_20260508.json` |
| Click 004-008 expansion summary | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_004_008_expansion_summary_20260508.json` |
| Click 004-008 decision artifact | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_004_008_decision_20260508.json` |
| Click 004-008 cost reconciliation | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_004_008_cost_reconciliation_2026-05-08.json` |
| Click 005/008 failure triage | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_008_failure_triage_20260508.json` |
| Click 005 repaired-verifier replay | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_repaired_verifier_replay_20260508.json` |
| Attempt-2 preflight budget gate | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_008_attempt2_budget_gate_20260508.json` |
| Attempt-2 combined live batch | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_008_attempt2_live_20260508.json` |
| Attempt-2 Click 005 source batch | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_008_attempt2_live_click005_20260508.json` |
| Attempt-2 Click 008 source batch | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_008_attempt2_live_click008_20260508.json` |
| Attempt-2 normalized summary | `experiments/core_narrative/results/normalized/codex_nfl_output_contract_v3_click_005_008_attempt2_summary_20260508.json` |
| Attempt-2 cost reconciliation | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_008_attempt2_cost_reconciliation_2026-05-08.json` |
| Attempt-2 scoped cost reconciliation | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_008_attempt2_cost_reconciliation_scoped_20260508.json` |
| Attempt-2 decision artifact | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_008_attempt2_decision_20260508.json` |
| Attempt-2 artifact-count check | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_008_attempt2_artifact_check_20260508.json` |
| Click 008 attempt-2 failure analysis | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_attempt2_failure_analysis_20260508.json` |
| Click 008 prompt-packaging verification | `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_prompt_packaging_verification_20260508.json` |

## Limitation

The expansion and retry remain controlled Click slices, not broader non-Click results. The Click 008 attempt-2 retry is not clean evidence that prompt/context hardening failed because hidden verifier context entered the prompt package. The local prompt-packaging fix is now verified without model spend. Any future live work should be explicitly approved and limited to Click 008 attempt 3 across the four core ACUTs; no Click 009+ expansion or broader speculative retry is justified by this evidence.
