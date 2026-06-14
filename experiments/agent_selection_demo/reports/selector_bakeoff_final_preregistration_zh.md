# Selector Bakeoff Final Preregistration

生成日期：2026-06-14

## Status

- Status: `frozen_before_final_outcome_join`。
- Final source: `phase1_original_three_repo_split_heldout_final_candidate` (`original_three_repo_split_heldout`)。
- Independence: `locked_no_paid_final_replay_not_used_for_threshold_or_variant_selection`。
- Caveat: Original split has more missing/non-scoreable cells than the primary blocked split, so final reporting must be limited.

## Frozen selector

- Final config: `cod_lite`；family `cod_lite`；k per repo `10`；k total `30`。
- Backup config: `hrd_v3_70_30`；family `hrd_v3`；k total `30`。
- Decision wrapper: v2 thresholds `{'action_margin': 0.1, 'bootstrap_iterations': 1000, 'confidence_level': 0.8, 'lcb_tolerance': 0.1, 'min_common_valid': 8, 'tie_epsilon': 0.05}`；zero-loss requirement `False`。

## Frozen task IDs

- Selected before final outcome join: `attrs::attrs__v2__044, attrs::attrs__v2__048, attrs::attrs__v2__187, attrs::attrs__v2__210, attrs::attrs__v2__223, attrs::attrs__v2__227, attrs::attrs__v2__244, attrs::attrs__v2__250, attrs::attrs__v2__253, attrs::attrs__v2__264, boltons::boltons__v2__007, boltons::boltons__v2__068, boltons::boltons__v2__092, boltons::boltons__v2__093, boltons::boltons__v2__102, boltons::boltons__v2__122, boltons::boltons__v2__128, boltons::boltons__v2__132, boltons::boltons__v2__142, boltons::boltons__v2__231, click::click__third__109, click::click__third__198, click::click__third__201, click::click__third__203, click::click__third__204, click::click__third__214, click::click__third__217, click::click__third__220, click::click__third__274, click::click__third__275`。
- Later/Holdout before final outcome join: `attrs::attrs__v2__056, attrs::attrs__v2__052, attrs::attrs__v2__157, attrs::attrs__v2__158, attrs::attrs__v2__196, attrs::attrs__v2__202, attrs::attrs__v2__206, attrs::attrs__v2__215, attrs::attrs__v2__219, attrs::attrs__v2__220, attrs::attrs__v2__228, attrs::attrs__v2__231, attrs::attrs__v2__235, attrs::attrs__v2__261, attrs::attrs__v2__271, boltons::boltons__v2__006, boltons::boltons__v2__008, boltons::boltons__v2__009, boltons::boltons__v2__076, boltons::boltons__v2__086, boltons::boltons__v2__087, boltons::boltons__v2__091, boltons::boltons__v2__095, boltons::boltons__v2__103, boltons::boltons__v2__141, boltons::boltons__v2__140, boltons::boltons__v2__144, boltons::boltons__v2__163, boltons::boltons__v2__164, boltons::boltons__v2__169, boltons::boltons__v2__170, boltons::boltons__v2__232, click::click__third__050, click::click__third__091, click::click__third__166, click::click__third__197, click::click__third__199, click::click__third__206, click::click__third__207, click::click__third__202, click::click__third__205, click::click__third__208, click::click__third__213, click::click__third__216, click::click__third__234, click::click__third__238, click::click__third__250`。

## Random baselines

- Families: `uniform_random_same_budget, quality_filtered_random, source_recency_stratified_random, module_stratified_random`。
- Seeds: `0..999`。

## Leakage and paid boundary

- Final outcome-derived feature columns blank: `True`。
- New paid cells planned: `0`.
- If a paid fallback becomes necessary, hard cap is `70` cells and endpoint env must be `LLM_BASE_URL` plus `LLM_API_KEY`.
