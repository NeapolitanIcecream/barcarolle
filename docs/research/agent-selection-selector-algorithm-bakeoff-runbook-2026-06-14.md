# Agent Selection Selector Algorithm Bakeoff Runbook 2026-06-14

Status: mandatory long-running runbook for implementing the full selector
algorithm family suggested by GPT-5.5-Pro, running ablations, and finding the
best demo-level Agent-selection story that the current data can honestly
support.

This runbook follows the corrected validation result:

- the previous boltons `hrd_70_30` result is development evidence only;
- the independent Phase 1 pseudo-future block showed Kilo ahead in Selection
  and later/Holdout, but the conservative wrapper did not recommend;
- MAE barely beat the strongest random baseline and should be treated as
  auxiliary for the demo, not as a hard proof gate.

The goal now is algorithm exploration, not proof of full predictive validity.
Implement all practical selector families, run a clean bakeoff and ablations,
then freeze the most promising demo selector/decision rule for the strongest
available validation slice.

## Demo Objective

Primary demo objective:

> Selection recommends an Agent, and later/Holdout validates that choice.

Primary success metrics:

- recommendation state is `recommend`;
- recommended Agent is later/Holdout top, or recommendation regret is `<= 5pp`;
- top-pair direction agrees between Selection and later/Holdout;
- recommendation beats same-budget random on decision quality, such as lower
  false-recommendation rate, lower regret, or higher validated recommendation
  rate.

Auxiliary metrics:

- MAE between Selection pass rate and later/Holdout pass rate;
- relative MAE improvement:

```text
(random_MAE - selector_MAE) / random_MAE
```

- random percentile or beats/ties share.

Do not use MAE as a strict one-vote veto for the demo. If a selector gives a
validated Agent recommendation with low regret but small MAE edge, report that
honestly: it supports demo-level selection behavior, not predictive-validity
proof.

## Non-goals

- Do not claim full predictive validity.
- Do not claim a globally best Agent/model.
- Do not treat the prior boltons HRD subset as independent validation.
- Do not retune on a final slice and then present the same slice as proof.
- Do not make the final story depend on invented terminology.
- Do not ask for manual intervention; choose conservative defaults and keep
  going.

## Required Reading

Read before coding:

- `AGENTS.md`
- `PROCESS.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0614-0.md` if present
- `experiments/agent_selection_demo/reports/selector_corrected_validation_closeout_zh.md`
- `experiments/agent_selection_demo/reports/selector_corrected_validation_story_zh.md`
- `experiments/agent_selection_demo/results/selector_corrected_validation_closeout.json`
- `experiments/agent_selection_demo/results/selector_independent_validation_inventory.json`
- `experiments/agent_selection_demo/results/selector_validation_correction_audit.json`
- `experiments/agent_selection_demo/results/selector_final_eval.json`
- `experiments/agent_selection_demo/results/selector_hrd_eval.json`
- `experiments/agent_selection_demo/tools/agent_selection_demo.py`

## Algorithm Families To Implement

Implement all families below unless a family is impossible from available data;
if so, implement a documented lightweight approximation and record the reason.

### 1. RSQ v2: Recency-Stratified Quota

Role: strong metadata baseline.

Minimum features:

- repo;
- source/window;
- recency bucket;
- module/path bucket;
- change-size or difficulty proxy;
- quality/risk/flakiness filters;
- source/module caps.

### 2. FLC: Feature-space Facility Location / Core-set

Role: stronger representative baseline.

Minimum behavior:

- vectorize task metadata into a small feature vector;
- choose `k` medoids using greedy facility-location coverage;
- include quality/risk penalty and redundancy cap;
- no Agent outcomes required.

### 3. HRD v3: Hybrid Representative + Informativeness

Role: primary decision-aware selector.

Minimum behavior:

- split budget into representative and informative tasks, with variants
  `70/30`, `60/40`, and `50/50`;
- representative arm can use RSQ v2 or FLC;
- informative arm should use leakage-safe features in priority order:
  1. historical current-Agent disagreement available before the origin;
  2. historical generic Agent disagreement;
  3. task difficulty near the middle of observed pass-rate range;
  4. metadata informativeness fallback.

Terminology rule: if no leakage-safe historical Agent-disagreement signal is
used, call the arm `metadata_informativeness`, not `Agent disagreement`.

### 4. COD-lite: Contrast-Optimal Selector

Role: lightweight experimental-design selector.

Minimum behavior:

- choose tasks that maximize information about top-pair or all-pair Agent
  contrasts;
- use low-dimensional task features and historical outcomes only when allowed
  by the origin mask;
- implement greedy swap or greedy marginal-gain approximation;
- output why each selected task improves contrast information.

### 5. RO-LSP: Rolling-Origin Learned Scoring Policy

Role: low-capacity learned selector.

Minimum behavior:

- define a task scoring function over 5-10 interpretable features;
- train/search weights only on development origins;
- use grid search, coordinate search, ridge/logistic regression, or another
  simple low-capacity method;
- freeze weights before final evaluation;
- report leave-one-origin or leave-one-repo sensitivity.

### 6. SAES-lite: Sequential Adaptive Evidence Selector

Role: product-oriented selector for efficient Agent choice.

Minimum no-paid replay behavior:

- first choose a representative seed batch;
- simulate observing selected-batch outcomes;
- identify top-2 uncertainty;
- choose a second batch focused on informative/top-pair tasks;
- decide recommend/abstain/need-more-evidence after the second batch;
- record the sequential decision trace.

If online paid execution is not needed, implement SAES as offline replay over
existing outcome matrices.

## Decision Wrapper v2

Implement a demo-appropriate wrapper. It must be less conservative than the
previous `losses == 0` rule.

Default recommendation rule:

```text
recommend top_agent if:
  selection_top_margin >= action_margin
  and common_valid_tasks >= min_common_valid
  and paired_wins > paired_losses
  and bootstrap_lcb >= -lcb_tolerance
```

Recommended defaults:

- `action_margin`: `0.05` or `0.10`, calibrated on development only;
- `min_common_valid`: `8` for small demo slices, `12` for larger slices;
- `lcb_tolerance`: `0.05`;
- no zero-loss requirement.

Decision states:

- `recommend`;
- `abstain_indistinguishable`;
- `need_more_evidence`.

The report must show both:

- actual decision metrics under wrapper v2;
- forced-top diagnostics for intuition.

## Evaluation Structure

Use three evaluation layers.

### Layer A: Development Bakeoff

Inputs:

- previous boltons HRD slice;
- corrected Phase 1 independent block;
- additional Phase 1 sensitivity blocks from the inventory.

Purpose:

- tune selector families;
- tune decision wrapper thresholds;
- run ablations;
- understand failure modes.

This layer may use outcomes as development evidence. Do not call it final
validation.

### Layer B: Locked No-paid Final Replay

Use the strongest independent no-paid final source not already consumed for
threshold/variant selection. If no such source remains, explicitly say so.

If only one independent source exists, use it for final-style reporting but mark
the result as `limited_final_replay_after_development_on_sparse_sources`.

### Layer C: Optional Fresh Paid Final Slice

Use only if:

- a candidate selector and wrapper pass development gates;
- no independent no-paid final source remains;
- a fresh task source passes readiness;
- paid cells are necessary to validate the demo story.

Default fresh paid design if needed:

- top-2 Agents only;
- `k_selection = 10`;
- `k_later = 10`;
- primary cells: `40`;
- optional same-budget strong-random control: `20` cells;
- hard cap for this runbook: `70` new paid cells.

All paid calls must use `LLM_BASE_URL` plus `LLM_API_KEY`.

## Package 1: Gate Reframe And Current Evidence Audit

Produce:

```text
experiments/agent_selection_demo/reports/selector_bakeoff_gate_reframe_zh.md
experiments/agent_selection_demo/results/selector_bakeoff_gate_reframe.json
```

Required content:

- restate the demo gate as Agent-selection decision quality;
- record that MAE is auxiliary, with relative MAE formula;
- summarize current corrected validation numbers;
- list which artifacts are development evidence and which are potential final
  validation sources;
- define initial threshold grid for decision wrapper v2.

Acceptance:

- no paid calls;
- previous overclaim remains downgraded.

Commit after this package.

## Package 2: Feature And Outcome Matrix Upgrade

Build a selector feature table that can support all algorithms.

Produce:

```text
experiments/agent_selection_demo/results/selector_bakeoff_task_features.csv
experiments/agent_selection_demo/results/selector_bakeoff_outcome_matrix.csv
experiments/agent_selection_demo/results/selector_bakeoff_feature_manifest.json
experiments/agent_selection_demo/reports/selector_bakeoff_feature_manifest_zh.md
```

Feature requirements:

- repo/source/window/origin;
- task id and stable cluster id;
- module/path/test/change-size/recency buckets;
- quality/risk/flakiness/oracle fields or conservative fallbacks;
- historical difficulty;
- historical disagreement;
- pairwise informativeness where leakage-safe;
- metadata informativeness fallback;
- explicit `feature_leakage_status` per feature:
  - `metadata_only`;
  - `development_outcome_only`;
  - `leakage_safe_historical_outcome`;
  - `not_allowed_for_final`.

Acceptance:

- tests cover leakage mask behavior;
- final selector scoring can be audited to prove it did not use final outcomes.

Commit after this package.

## Package 3: Implement Selector Families

Implement or extend CLI/tooling for:

- RSQ v2;
- FLC;
- HRD v3 `70/30`, `60/40`, `50/50`;
- COD-lite;
- RO-LSP;
- SAES-lite;
- existing random baselines.

Produce:

```text
experiments/agent_selection_demo/results/selector_algorithm_registry.json
experiments/agent_selection_demo/reports/selector_algorithm_registry_zh.md
```

Acceptance:

- each selector can output selected task IDs and selection rationale;
- each selector is deterministic for a fixed seed/config;
- tests cover at least one deterministic example per family;
- if a family is approximated, the registry says exactly how.

Commit after this package.

## Package 4: Decision Wrapper v2 And Threshold Search

Implement wrapper v2 and run threshold search on development evidence only.

Produce:

```text
experiments/agent_selection_demo/results/selector_decision_wrapper_v2_eval.json
experiments/agent_selection_demo/reports/selector_decision_wrapper_v2_eval_zh.md
```

Threshold grid should include:

- action margin: `0.05`, `0.10`, `0.15`;
- min common valid: `8`, `12`;
- lcb tolerance: `0.0`, `0.05`, `0.10`;
- tie epsilon: `0.05`, `0.10`.

Primary wrapper score:

```text
validated_recommendation_rate
- false_recommendation_penalty
- regret_penalty
+ abstention_sanity_bonus
```

The exact scoring formula can be simple, but it must be documented.

Acceptance:

- no zero-loss requirement;
- tests cover one-discordant-loss-but-overall-win recommendation;
- reports show why the selected thresholds are demo-appropriate.

Commit after this package.

## Package 5: Development Bakeoff And Ablations

Run every selector family and ablation on development evidence.

Produce:

```text
experiments/agent_selection_demo/results/selector_algorithm_bakeoff_eval.json
experiments/agent_selection_demo/reports/selector_algorithm_bakeoff_eval_zh.md
```

Required ablations:

- representative-only;
- informativeness-only;
- HRD split `70/30`, `60/40`, `50/50`;
- with and without recency;
- with and without module/source caps;
- with and without historical outcome features, when leakage-safe;
- decision wrapper v1 versus wrapper v2.

Required metrics:

- recommendation coverage;
- validated recommendation rate;
- false recommendation rate;
- mean and max regret;
- top-pair direction agreement;
- top-1 agreement when meaningful;
- MAE and relative MAE improvement versus strongest random;
- random percentile or beats/ties share;
- leave-one-repo or leave-one-origin sensitivity where possible.

Acceptance:

- identifies top 2-3 candidate selector configs;
- explains why each candidate is plausible or rejected;
- does not promote a candidate solely because of MAE.

Commit after this package.

## Package 6: Freeze Final Candidate

Freeze one final candidate and one backup before final evaluation.

Produce:

```text
experiments/agent_selection_demo/results/selector_bakeoff_final_preregistration.json
experiments/agent_selection_demo/reports/selector_bakeoff_final_preregistration_zh.md
```

Required content:

- final selector config;
- backup selector config;
- decision wrapper thresholds;
- final validation source;
- selected task IDs before final outcome join where possible;
- later/Holdout task IDs;
- random baselines and seed list;
- success criteria;
- paid-cell boundary if final paid cells are needed.

If no clean final source remains after development use, choose one of:

- freeze a fresh paid final source if readiness passes;
- run limited final replay and label it correctly;
- produce a negative "no independent final source" closeout.

Acceptance:

- final protocol is frozen before final outcome join or paid cells;
- no selector variant can be swapped after seeing final results.

Commit after this package.

## Package 7: Final Replay Or Fresh Paid Validation

Run the frozen final evaluation.

Produce:

```text
experiments/agent_selection_demo/results/selector_bakeoff_final_eval.json
experiments/agent_selection_demo/reports/selector_bakeoff_final_eval_zh.md
```

If no-paid final replay is used:

- report independence level honestly.

If paid final cells are needed:

- preregistration must already exist;
- run adapter smoke/gates first;
- keep raw artifacts ignored;
- use `1800s` Agent timeout, `60s` cleanup grace, `1860s` outer timeout,
  `360s` verifier timeout, and endpoint/proxy timeout greater than Agent
  timeout unless config explicitly documents another value.

Final success for the demo:

- `recommend`;
- later/Holdout validates the recommendation or regret `<= 5pp`;
- top-pair direction agreement;
- decision quality better than same-budget random;
- MAE reported, but not a hard veto.

Commit after this package.

## Package 8: Final Story And Closeout

Produce:

```text
experiments/agent_selection_demo/reports/selector_algorithm_bakeoff_story_zh.md
experiments/agent_selection_demo/reports/selector_algorithm_bakeoff_closeout_zh.md
experiments/agent_selection_demo/results/selector_algorithm_bakeoff_closeout.json
```

Story requirements:

- short, Chinese, low terminology burden;
- say what algorithms were tried;
- say which selector was chosen and why;
- show Selection and later/Holdout pass rates;
- show whether the demo user could choose an Agent from Selection;
- show random-baseline comparison;
- say how much was spent;
- clearly state what remains unproved.

Closeout checklist:

1. Which algorithms were implemented?
2. Which ablations were run?
3. Which decision rule was selected?
4. Which selector won the development bakeoff?
5. What final validation source was used?
6. Did Selection recommend an Agent?
7. Did later/Holdout validate the recommendation?
8. What was recommendation regret?
9. How did decision quality compare with random?
10. What was MAE and relative MAE improvement?
11. How many new paid cells and dollars were used?
12. Which tests and hygiene checks passed?
13. What exact demo claim is supported?
14. What remains unproved?

Update `PROCESS.md` with concise links to the final artifacts and the corrected
claim boundary.

Commit after this package.

## Required Validation

Run at minimum:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q
```

```text
PYTHONPATH=experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_retrospective_predictive_signal.py -q
```

If paid cells or adapter/workspace code are touched:

```text
PYTHONPATH=experiments/phase0_headroom/tools uv run --project experiments/phase1_compiler pytest experiments/phase0_headroom/tools/test_cli_workspace_adapters.py experiments/phase0_headroom/tools/test_workspace_acut_run.py experiments/phase0_headroom/tools/test_workspace_usage_import.py -q
```

Always run:

```text
git diff --check
git ls-files experiments/agent_selection_demo | rg '(__pycache__|\.pyc$|raw|transcript|workspace|\.DS_Store|\.pytest_cache|\.venv)'
```

If `rg` exits `1` because there are no prohibited tracked artifacts, record it
as pass.

