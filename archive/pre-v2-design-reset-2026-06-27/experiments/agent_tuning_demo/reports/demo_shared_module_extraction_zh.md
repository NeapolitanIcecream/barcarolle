# Agent Tuning Demo shared module extraction closeout

Generated at: `2026-06-15T08:41:01+00:00`.

Terminal state: `demo_shared_module_extraction_complete_no_paid`.
Paid calls run: `0`.
New Selection or Tuning experiments run: `false`.
Selection Demo code/results/reports touched: `false`.

## What changed

- Added `experiments/demo_common/` with shared file, cost/usage, failure-category, candidate lookup, adapter, and package-map helpers.
- Updated Phase 2 and Phase 2b Tuning tools to import those neutral helpers instead of `agent_selection_demo.py`.
- Added a Tuning-owned `selection_snapshot.py` loader that reads only `experiments/agent_tuning_demo/config/selection_input_snapshot.json`.
- Removed runtime reads of live Selection config/result files from the active Tuning tools.
- Removed Phase 2 runtime dependence on ignored raw Selection stdout by freezing sanitized tool summaries in the snapshot.

## Frozen inputs

Snapshot: `experiments/agent_tuning_demo/config/selection_input_snapshot.json` (`sha256:27fd4db587df89804b61a51814ae66491e3acac4cad648192ea79529c2e13851`).
Policy: Frozen Tuning-owned snapshot. Later Agent Selection Demo config/result changes do not refresh this file automatically; refresh requires an explicit runbook or deliberate snapshot regeneration.

| Source | Storage | Digest | Consumers |
| --- | --- | --- | --- |
| experiments/agent_selection_demo/config/demo_config.json | embedded_full_json | sha256:9a731e6581bda14907bc615c0606c25966932159e232085046d570c0df2743dd | phase2, phase2b |
| experiments/agent_selection_demo/results/frozen_split.json | embedded_full_json | sha256:856a11ebf23402a06b3b7421883666cc76e4af3089a56930b0d1c13779b4200c | phase2 |
| experiments/agent_selection_demo/results/selector_task_table.csv | embedded_rows_filtered_to_target_repo | sha256:c2b2c9869f177a86ac1eabc9c01239a7fceb538481ffc875cc5d364e23a6a311 | phase2b |
| experiments/agent_selection_demo/results/selection_score_table.csv | embedded_rows_filtered_to_target_agent | sha256:e8346a3bafa190015b1a899e4ca8325e4dc4a3f9b83169d99ea10f7cb6fd14d6 | phase2, phase2b |
| experiments/agent_selection_demo/results/holdout_score_table.csv | embedded_rows_filtered_to_target_agent | sha256:7e8b766bf430dce5e356e2444418d09e6b0976f30cdbf748c2ec40691e858e21 | phase2b |
| experiments/agent_selection_demo/results/predictive_validity_window_inventory.json | embedded_minimal_candidate_repos_field | sha256:f7540b44ba5dc771bb6d016a60c426285088f8e604a8d42d24ac472b9cdd1842 | phase2b |
| experiments/phase0_headroom/results/raw/workspace_acut/agent_selection_demo_2026_06_12_selection/{target_agent_id}/selection__{target_agent_id}__{task_id}/acut_stdout.txt | embedded_sanitized_tool_summary_by_task | sanitized per-task digests in snapshot | phase2 |

Future changes under `experiments/agent_selection_demo/results/` or `experiments/agent_selection_demo/config/` do not affect current Agent Tuning behavior because Phase 2 and Phase 2b resolve Selection-derived data through the committed snapshot. A later refresh must deliberately regenerate the snapshot and manifest.

## Deferred

- Selection Demo still has its existing helper implementations. Full adoption of `experiments/demo_common/` by Selection is deferred to avoid conflicting with parallel Selection work.
- No broad framework extraction was attempted; the shared module is intentionally narrow.

## Guard tests

- `experiments/agent_tuning_demo/tests/test_demo_shared_module_extraction_guards.py` prevents reintroducing `agent_selection_demo.py` imports in Tuning tools.
- The same guard prevents active Tuning tools from hard-coding live Selection config/result paths.
- It also asserts Phase 2/2b consume the frozen snapshot for Selection-derived inputs.

## Tests run

- `uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q` -> `34 passed`.
- `rg "import agent_selection_demo|from agent_selection_demo" experiments/agent_tuning_demo/tools` -> `passed_no_matches`.
- `rg "experiments/agent_selection_demo/results|experiments/agent_selection_demo/config" experiments/agent_tuning_demo/tools` -> `passed_no_matches`.
- Selection Demo tests not run because Selection Demo code was not touched.
- `git diff --check` -> `passed`.
- Hygiene scan -> `experiments/demo_common/workspace_inputs.py`; this is a source helper filename containing `workspace`, not a tracked solver/verifier workspace or raw artifact.

## Unsupported claims

- No new paid Agent, LLM, tuner, proposer, Selection, or Tuning experiment results were produced.
- This refactor does not prove tuned improvement, predictive validity, or cross-repo generalization.
- This refactor does not claim Agent Selection Demo has adopted the shared helpers.
