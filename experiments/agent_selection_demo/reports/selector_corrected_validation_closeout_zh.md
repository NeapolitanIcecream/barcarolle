# Selector Corrected Validation Closeout

生成日期：2026-06-14

## Terminal state

Terminal state: `accepted_negative_terminal_state`.

Preferred terminal state achieved: `false`.

Primary blocker: `selector_does_not_recommend`.

Secondary blocker: `strong_random_not_beaten`.

## Package closeout

1. Package 1 relabeled the previous `hrd_70_30` result as `hypothesis_generating_selector_development_result`.
2. Package 2 found a valid no-paid independent replay path: `phase1_blocked_split_heldout_three_repo`.
3. Package 3 froze `hrd_v2_70_30`, `k=6` per repo, before final outcome join.
4. Package 4 ran the no-paid independent replay.
5. Package 5 was skipped because the failure was not missing cells.
6. Package 6 records the negative closeout and updates `PROCESS.md`.

## Checklist answers

1. Previous selector relabeled correctly: yes.
2. Final validation source: no-paid Phase 1 `blocked_split_heldout`, attrs/boltons/click, top-2 `codex_workspace` and `kilo_workspace`.
3. Selector frozen before final outcomes: yes; see `selector_corrected_protocol.json`.
4. Selector config: `hrd_v2_70_30`, `k=6` per repo, metadata-informativeness arm, quality/risk gates.
5. Selection recommendation: no recommendation; decision state `need_more_evidence`.
6. Later/Holdout result: Kilo is later top at `16/30`; Codex is `7/30`.
7. Recommendation regret: actual recommendation regret is `null` because no recommendation was made. Forced-top diagnostic regret for Kilo is `0.0`.
8. MAE versus strongest random: selector `0.088889`; stratified random mean `0.090146`; absolute improvement `0.001257`, below `0.02`.
9. Decision metrics better than random: not enough for preferred state because there is no recommendation. False recommendation rate is `0.0`, matching strongest random; mean regret is not applicable for the selector.
10. New paid cells and dollars: `0` cells, `$0.00`.
11. Tests and hygiene passed: demo tests `31 passed`; Phase 1 retrospective signal tests `6 passed`; `git diff --check` exit `0`; prohibited tracked artifact scan exit `1` with no matches.
12. Exact claim supported: the frozen corrected selector should request more evidence on this independent pseudo-future block.
13. Still unproved: Selection recommends an Agent and later validates it; full predictive validity; global Agent ranking; cross-repo selector superiority.

## Exact rates

| Agent | Selection | Later/Holdout |
| --- | ---: | ---: |
| `codex_workspace` | `6/18` (`0.333333`) | `7/30` (`0.233333`) |
| `kilo_workspace` | `11/18` (`0.611111`) | `16/30` (`0.533333`) |

Decision detail:

- State: `need_more_evidence`
- Reason: `paired_uncertainty_or_discordant_tasks_too_weak`
- Selection top: `kilo_workspace`
- Selection margin: `0.277778`
- Pair stats: 18 common-valid tasks, 6 Kilo wins, 11 ties, 1 Kilo loss

## Random baselines

| Baseline | Seeds | Unique samples | MAE mean | Recommendation coverage | False recommend | Mean regret |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `uniform_random_same_budget` | 1000 | 981 | `0.108588` | `0.122` | `0.0` | `0.0` |
| `quality_filtered_random` | 1000 | 981 | `0.108588` | `0.122` | `0.0` | `0.0` |
| `stratified_random` | 1000 | 371 | `0.090146` | `0.178` | `0.0` | `0.0` |

The strongest random baseline is `stratified_random`. The selector does not beat it by the runbook threshold.

## Why no paid cells

The no-paid result is not inconclusive because of missing cells. It is interpretable and negative:

- outcome rows: `96`;
- policy-valid rows: `96`;
- scoreable rows: `95`;
- missing-or-NA rows: `0`.

Package 5 paid cells are therefore skipped. Spending paid cells after this result would change the validation target rather than filling a missing frozen grid.

## Next experiment

Smallest next experiment: use development-only evidence to redesign the decision wrapper or add leakage-safe historical Agent-disagreement features, then preregister a new independent final slice. If paid validation is needed, attrs is the plausible second-repo source after adding an attrs target profile and passing package readiness gates.
