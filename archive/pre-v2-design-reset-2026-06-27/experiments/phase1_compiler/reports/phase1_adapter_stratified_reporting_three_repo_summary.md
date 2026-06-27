# Adapter-Stratified Three-Repo Summary

Status: `complete`.

What happened: the completed three-repo paid pilot remains `three_repo_paid_pilot_threshold_met`, but the adapter supplement shows Codex and Kilo separately.
Why it matters: Kilo passed more cells than Codex on the same 60 paired tasks, so a pooled adapter headline hides a material harness effect.
Action suggested next: report adapter-level results first in future cross-harness paid runs, and mark pooled summaries as secondary or retrospective diagnostics unless preregistered.

## Claim Boundary

- Completed paid pilot decision changed: `false`.
- New paid cells run by this supplement: `0`.
- Predictive validity established: `false`.
- Pooled adapter summary status: retrospective diagnostic evidence only.

The original paid pilot is still pilot evidence only. This supplement explains adapter behavior inside that completed result; it does not rewrite the terminal outcomes, the task list, the split assignment, or the paid decision label.

## Adapter Results

| Adapter | Passes | Cells | Pass rate | Token-estimated USD | Cost/cell | Median latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `codex_workspace` | 22 | 60 | 0.3667 | 32.22309 | 0.53705 | 115.059s |
| `kilo_workspace` | 32 | 60 | 0.5333 | 19.044243 | 0.31740 | 52.5495s |

What happened: Kilo passed 10 more cells than Codex.
Why it matters: the adapter choice changes the observed pass rate by 0.1666.
Action suggested next: do not treat the two adapters as interchangeable evidence.

## Paired Disagreement

| Outcome | Count |
| --- | ---: |
| Both pass | 16 |
| Both fail | 22 |
| Codex only pass | 6 |
| Kilo only pass | 16 |
| Disagreement | 22/60 = 0.3667 |

What happened: the adapters disagreed on 22 of 60 paired tasks.
Why it matters: more than one third of task-level outcomes depended on adapter behavior.
Action suggested next: future reports should include a paired-disagreement table whenever adapters share tasks.

## Repo Breakout

| Repo | Codex pass rate | Kilo pass rate | Kilo minus Codex |
| --- | ---: | ---: | ---: |
| `attrs` | 0.5000 | 0.5500 | 0.0500 |
| `boltons` | 0.2000 | 0.3500 | 0.1500 |
| `click` | 0.4000 | 0.7000 | 0.3000 |

What happened: the largest adapter gap was on `click`, where Kilo passed 14/20 and Codex passed 8/20.
Why it matters: the adapter effect is not uniform across repositories.
Action suggested next: future paid designs should either choose one scoreable adapter before outcomes or block/report by adapter.

## Split Breakout

| Adapter | B_eval pass rate | H_future pass rate | Absolute gap |
| --- | ---: | ---: | ---: |
| `codex_workspace` | 0.2667 | 0.4667 | 0.2000 |
| `kilo_workspace` | 0.5333 | 0.5333 | 0.0000 |

| Adapter | Repo | B_eval | H_future | Absolute gap |
| --- | --- | ---: | ---: | ---: |
| `codex_workspace` | `attrs` | 0.7000 | 0.3000 | 0.4000 |
| `codex_workspace` | `boltons` | 0.0000 | 0.4000 | 0.4000 |
| `codex_workspace` | `click` | 0.1000 | 0.7000 | 0.6000 |
| `kilo_workspace` | `attrs` | 0.7000 | 0.4000 | 0.3000 |
| `kilo_workspace` | `boltons` | 0.3000 | 0.4000 | 0.1000 |
| `kilo_workspace` | `click` | 0.6000 | 0.8000 | 0.2000 |

What happened: Codex shows a larger pooled B_eval/H_future split gap than Kilo.
Why it matters: split-level conclusions also depend on adapter behavior.
Action suggested next: keep adapter and split visible before interpreting pooled pilot gaps.
