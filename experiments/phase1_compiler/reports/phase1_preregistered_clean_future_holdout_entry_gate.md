# Phase 1 Preregistered Clean Future-Holdout Entry Gate

Status: ready for paid `B_eval`.

Generated: 2026-05-22T11:06:33Z.

## Adapter Preflights

| Prefix | Adapter | Endpoint proof | Required env | Status |
| --- | --- | --- | --- | --- |
| `phase1_future_holdout_b_eval_codex_preflight` | `codex_workspace` | `codex_eligible` | `true` | `ready` |
| `phase1_future_holdout_b_eval_kilo_preflight` | `kilo_workspace` | `kilo_eligible` | `true` | `ready` |
| `phase1_future_holdout_h_future_codex_preflight` | `codex_workspace` | `codex_eligible` | `true` | `ready` |
| `phase1_future_holdout_h_future_kilo_preflight` | `kilo_workspace` | `kilo_eligible` | `true` | `ready` |

## Package Selection

`B_eval` selected task ids:

```text
boltons__clean_ext__001
boltons__clean_ext__008
boltons__clean_ext__010
boltons__hist__011
```

`H_future` selected task ids:

```text
boltons__clean_ext__017
boltons__hist__022
boltons__hist__023
boltons__hist__027
```

Both selections match the frozen preregistration. Both future-holdout score
tables are header-only and contain no previous paid rows.

## Cost Gate

- Preferred batch: `16` cells
- Conservative per-cell estimate: `USD 0.50`
- Projected incremental spend: `USD 8.00`
- Current observed-or-conservative cumulative spend: `USD 37.6472432`
- Projected cumulative after preferred batch: `USD 45.6472432`
- Total stop cap: `USD 80.00`
- Paid parallelism: disabled

No paid ACUT task-solving calls have run in this step.
