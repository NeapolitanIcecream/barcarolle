# Weighted Design Paid Pilot Process

Run ID: `phase1_weighted_design_paid_pilot_20260526`.
Updated: `2026-05-26T04:23:08Z`.

## Work Queue

- Step 0: `completed` - Preflight And Approval Record; commit target `Record weighted design paid pilot preflight`.
- Step 1: `completed` - Build Frozen Pilot Matrix And Package Inspection; commit target `Build weighted design paid pilot matrix`.
- Step 2: `completed` - Tooling, Endpoint, And Entry Gate; commit target `Record weighted design paid pilot entry gate`.
- Step 3: `completed` - Run Paid Smoke Batch; commit target `Run weighted design paid pilot smoke batch`.
- Step 4: `completed` - Run Remaining Attrs Paid Cells; commit target `Run weighted design paid pilot attrs cells`.
- Step 5: `completed` - Run Remaining Boltons Paid Cells; commit target `Run weighted design paid pilot boltons cells`.
- Step 6: `completed` - Integrity Audit And Score Import; commit target `Audit weighted design paid pilot score tables`.
- Step 7: `completed` - Compute Weighted And Baseline Metrics; commit target `Compute weighted design paid pilot metrics`.
- Step 8: `completed` - Baseline Comparison And Error Analysis; commit target `Compare weighted design paid pilot baselines`.
- Step 9: `completed` - Final Decision And Closeout; commit target `Record weighted design paid pilot decision`.

## Boundary Records

- Paid pilot approval is granted by the runbook.
- Paid endpoint rule is `LLM_BASE_URL` plus `LLM_API_KEY`; values are never recorded.
- Historical reference remains historical-only and is not rerun.
- Follow-up runbook written by worker: `false`.

## Commit Log

- Step 0: `c7b71d37` - `Record weighted design paid pilot preflight`.
- Step 1: `264befc7` - `Build weighted design paid pilot matrix`.
- Step 2: `f039d30d` - `Record weighted design paid pilot entry gate`.
- Step 3: `01940700` - `Run weighted design paid pilot smoke batch`.
- Step 4: `5e9239b4` - `Run weighted design paid pilot attrs cells`.
- Step 5: `b405ab3f` - `Run weighted design paid pilot boltons cells`.
- Step 6: `7aeae3d4` - `Audit weighted design paid pilot score tables`.
- Step 7: `7ef4f678` - `Compute weighted design paid pilot metrics`.
- Step 8: `8eacfb99` - `Compare weighted design paid pilot baselines`.
- Step 9: final decision commit contains this closeout report.

## Verification Commands

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_weighted_design_paid_pilot.py`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools/test_workspace_acut_run.py`
- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests`
- `git diff --check`

## Closeout

- `schema_version`: `barcarolle.phase1_weighted_design_paid_pilot_output.v1`.
- `generated_at`: `2026-05-26T04:23:08Z`.
- `run_id`: `phase1_weighted_design_paid_pilot_20260526`.
- `final_decision`: `weighted_pilot_complete_threshold_not_met`.
- `new_paid_acut_calls_made`: `True`.
- `new_paid_llm_calls_made`: `True`.
- `paid_cells_planned`: `44`.
- `paid_cells_completed`: `44`.
- `scoreable_cells`: `44`.
- `observed_or_conservative_cost_usd`: `22.0`.
- `primary_release_candidate_id`: `barcarolle_weighted_time_family_matched`.
- `baseline_candidate_ids`: `['repo_unweighted_same_budget', 'repo_stratified_by_target_profile']`.
- `weighted_design_gap`: `{'attrs': 0.3148, 'boltons': 0.7481}`.
- `baseline_gaps`: `{'repo_unweighted_same_budget': {'attrs': 0.25, 'boltons': 0.125}, 'repo_stratified_by_target_profile': {'attrs': 0.25, 'boltons': 0.125}}`.
- `weighted_design_beats_unweighted_and_stratified`: `False`.
- `primary_threshold_result`: `{'gap_threshold': 0.15, 'met': False, 'primary_candidate_id': 'barcarolle_weighted_time_family_matched', 'per_repo_abs_gaps': {'attrs': 0.3148, 'boltons': 0.7481}, 'max_abs_gap': 0.7481}`.
- `precision_status`: `pilot_result_insufficient_precision`.
- `policy_status`: `pass`.
- `scoreability_status`: `pass`.
- `historical_reference_remained_historical_only`: `True`.
- `followup_runbook_written_by_worker`: `False`.
- `raw_artifacts_committed`: `False`.
- `smallest_next_action_recommended`: `Have the coordinating session interpret the committed pilot decision and choose any bounded follow-up category.`.
- `disallowed_claims_made`: `[]`.
