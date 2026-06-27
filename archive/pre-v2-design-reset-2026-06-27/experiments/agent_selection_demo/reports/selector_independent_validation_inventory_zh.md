# Selector Independent Validation Inventory

生成日期：2026-06-14

## 结论

存在一个可直接使用的 no-paid corrected final path：

```text
phase1_blocked_split_heldout_three_repo
```

它来自 committed sanitized Phase 1 artifacts，不需要新 paid calls。它不是之前 boltons demo `hrd_70_30` 开发 slice，也不是旧 story 里已经用于 selector variant choice 的 Holdout。它可以作为 correction runbook 的主 no-paid replay source。

边界要说清楚：这个 source 是 retrospective pseudo-future held-out split，不是强 chronological rolling-origin proof。它能支持 demo-level independent decision validation；不能支持 full predictive validity 或 global Agent ranking。

## No-paid sources

| Source | Mode | Selection tasks | Later tasks | Agents | Outcome grid | Final proof status |
| --- | --- | ---: | ---: | --- | --- | --- |
| `phase1_blocked_split_heldout_three_repo` | retrospective pseudo-future | 30 | 30 | `codex_workspace`, `kilo_workspace` | 119/120 cells scoreable or policy-usable; 1 non-scoreable B_eval attrs cell | primary no-paid corrected replay |
| `phase1_original_three_repo_split_heldout` | retrospective pseudo-future | 49 | 47 | `codex_workspace`, `kilo_workspace` | materially more missing/non-scoreable cells | sensitivity/development only |
| `phase1_repo_specific_earliest_time_bucket_cutoff` | true rolling-origin diagnostic | attrs 4, boltons 24, click 4 | attrs 26, boltons 11, click 26 | `codex_workspace`, `kilo_workspace` | sparse B_eval for attrs/click | diagnostic only |

Primary path detail:

| Repo | B_eval tasks | H_future tasks | B_eval rows | B_eval scoreable | H_future rows | H_future scoreable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| attrs | 10 | 10 | 20 | 19 | 20 | 20 |
| boltons | 10 | 10 | 20 | 20 | 20 | 20 |
| click | 10 | 10 | 20 | 20 | 20 | 20 |

This path uses `experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_window_plan.json`, `phase1_retrospective_predictive_signal_selection_freeze.json`, and `phase1_retrospective_predictive_signal_score_join_manifest.json`. Phase 1 records `frozen_before_score_join`; the corrected selector protocol will still freeze its own selected IDs and decision thresholds before joining final outcomes for this runbook.

## Fresh paid fallback sources

| Source | Ready task supply | Current-Agent outcomes | Readiness | Status |
| --- | ---: | ---: | --- | --- |
| Existing boltons unused demo tasks | 4 | 0 | certified tasks exist | not enough for primary 10+10 final design |
| attrs second-repo slice | 28 | 0 | local repo exists; target profile missing | possible fallback after readiness gate |
| click second-repo slice | 0 in current demo package | 0 | target profile exists; local repo/certified package missing | not ready |

Boltons unused tasks:

- `boltons__supply_expansion_20260526__159`
- `boltons__supply_expansion_20260526__157`
- `boltons__supply_expansion_20260526__158`
- `boltons__supply_expansion_20260526__160`

They are useful only as supplemental paid smoke/control material because four tasks cannot support the runbook's recommended `k_selection=10`, `k_later=10` paid design.

Attrs has 28 certified current-outcome-unseen tasks from:

- `experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_certified_tasks.jsonl`：18 tasks；
- `experiments/phase0_headroom/certified_tasks/attrs_supply_expansion_20260526_certified_tasks.jsonl`：10 tasks。

This is the smallest plausible fresh paid fallback if the no-paid replay fails only because the outcome grid is missing. At inventory time it is not the primary path because the current demo config lacks an attrs target profile/package gate, and no-paid Phase 1 replay is available.

## Inventory decision

Use `phase1_blocked_split_heldout_three_repo` for Package 3/4. Do not spend paid cells before exhausting it.

If Package 4 fails because the final grid is missing, use the attrs fallback after a readiness gate. If Package 4 fails because the frozen selector recommends wrongly, abstains, or does not beat strong random baselines, do not retune on that final block; complete the negative result unless another independent final source remains.
