# Selector Corrected Protocol

生成日期：2026-06-14

## Protocol status

- Status: `frozen_before_final_outcome_join`。
- Final validation source: `no_paid_independent_rolling_origin`。
- Source mode: `retrospective_pseudo_future_blocked_split_heldout`。
- Previous boltons HRD result label: `hypothesis_generating_selector_development_result`。
- No paid calls are planned for this package.

## Selector

- Primary selector: `hrd_v2_70_30`。
- Budget: `6` per repo, `18` total。
- Representative / metadata-informativeness split: `70/30`。
- Reason for k: The primary no-paid source has exactly ten B_eval tasks per repo; k=6 preserves same-budget random baseline variation while keeping at least twelve common-valid paired cells in aggregate.
- The HRD arm is called `metadata_informativeness`; no leakage-safe historical Agent-disagreement matrix is available for this final block.

## Candidate support

| Repo | B_eval candidates | Selected |
| --- | --- | --- |
| attrs | 9 | 6 |
| boltons | 10 | 6 |
| click | 10 | 6 |

## Frozen task IDs

- Selected before outcome join: `attrs::attrs__v2__157, attrs::attrs__v2__202, attrs::attrs__v2__207, attrs::attrs__v2__215, attrs::attrs__v2__235, attrs::attrs__v2__271, boltons::boltons__v2__009, boltons::boltons__v2__076, boltons::boltons__v2__103, boltons::boltons__v2__128, boltons::boltons__v2__154, boltons::boltons__v2__231, click::click__third__091, click::click__third__206, click::click__third__220, click::click__third__238, click::click__third__250, click::click__third__274`。
- Later/Holdout before outcome join: `attrs::attrs__v2__052, attrs::attrs__v2__158, attrs::attrs__v2__210, attrs::attrs__v2__218, attrs::attrs__v2__220, attrs::attrs__v2__223, attrs::attrs__v2__244, attrs::attrs__v2__253, attrs::attrs__v2__261, attrs::attrs__v2__264, boltons::boltons__v2__006, boltons::boltons__v2__091, boltons::boltons__v2__093, boltons::boltons__v2__122, boltons::boltons__v2__132, boltons::boltons__v2__135, boltons::boltons__v2__140, boltons::boltons__v2__144, boltons::boltons__v2__163, boltons::boltons__v2__232, click::click__third__050, click::click__third__109, click::click__third__198, click::click__third__203, click::click__third__205, click::click__third__208, click::click__third__214, click::click__third__234, click::click__third__271, click::click__third__288`。

## Random baselines and decision rule

- Baselines: `quality_filtered_random, stratified_random, uniform_random_same_budget`。
- Random seeds: `0..999`。
- Agents: `codex_workspace, kilo_workspace`。
- Action margin: `0.05`。
- Minimum common-valid selected cells: `12`。

## Leakage audit

- Selector scoring inputs are metadata fields only.
- `phase1_retrospective_predictive_signal_score_join_manifest.json` is explicitly withheld until Package 4.
- Forbidden fields include pass/fail flags, terminal status, scoreable flags, and pass-rate fields.

## Claim boundary

If Package 4 succeeds, the claim is demo-level independent decision validation on a Phase 1 pseudo-future held-out block. It still does not prove full predictive validity, global Agent ranking, or cross-domain superiority.
