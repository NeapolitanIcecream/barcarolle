# Phase 1 Two-Repo Task Outcome Matrix

Generated: `2026-05-23T11:25:27+00:00`.

## Summary

- Status: `valid`.
- Planned cells: `32`.
- Scoreable cells: `31`.
- Verified pass cells: `22`.
- Verified fail cells: `9`.
- Policy violations: `1`.
- Frozen design match: `matched`.
- Predictive validity established: `False`.

Policy violations remain non-scoreable. The single policy violation is expected to be
`attrs__hist__027` / `kilo_workspace` in `H_future`.

## Repo And Split Outcomes

| Repo/split | Planned | Scoreable | Pass | Fail | Policy violations | Pass rate |
|---|---:|---:|---:|---:|---:|---:|
| `attrs/B_eval` | `8` | `8` | `7` | `1` | `0` | `0.875000` |
| `attrs/H_future` | `8` | `7` | `1` | `6` | `1` | `0.142857` |
| `boltons/B_eval` | `8` | `8` | `7` | `1` | `0` | `0.875000` |
| `boltons/H_future` | `8` | `8` | `7` | `1` | `0` | `0.875000` |

## Cell Matrix

| Repo | Split | Adapter | Task | Status | Scoreable | Module | Changed | Tests | Context |
|---|---|---|---|---|---:|---|---:|---:|---|
| `boltons` | `B_eval` | `codex_workspace` | `boltons__clean_ext__001` | `verified_pass` | `True` | `iterutils` | `2` | `1` | `issue:231` |
| `boltons` | `B_eval` | `kilo_workspace` | `boltons__clean_ext__001` | `verified_pass` | `True` | `iterutils` | `2` | `1` | `issue:231` |
| `boltons` | `B_eval` | `codex_workspace` | `boltons__clean_ext__008` | `verified_pass` | `True` | `setutils` | `2` | `1` | `issue:240` |
| `boltons` | `B_eval` | `kilo_workspace` | `boltons__clean_ext__008` | `verified_pass` | `True` | `setutils` | `2` | `1` | `issue:240` |
| `boltons` | `B_eval` | `codex_workspace` | `boltons__clean_ext__010` | `verified_pass` | `True` | `setutils` | `2` | `1` | `issue:252` |
| `boltons` | `B_eval` | `kilo_workspace` | `boltons__clean_ext__010` | `verified_pass` | `True` | `setutils` | `2` | `1` | `issue:252` |
| `boltons` | `B_eval` | `codex_workspace` | `boltons__hist__011` | `verified_pass` | `True` | `iterutils` | `3` | `1` | `pr:253` |
| `boltons` | `B_eval` | `kilo_workspace` | `boltons__hist__011` | `verified_fail` | `True` | `iterutils` | `3` | `1` | `pr:253` |
| `boltons` | `H_future` | `codex_workspace` | `boltons__clean_ext__017` | `verified_pass` | `True` | `timeutils` | `2` | `1` | `issue:319` |
| `boltons` | `H_future` | `kilo_workspace` | `boltons__clean_ext__017` | `verified_pass` | `True` | `timeutils` | `2` | `1` | `issue:319` |
| `boltons` | `H_future` | `codex_workspace` | `boltons__hist__022` | `verified_fail` | `True` | `iterutils` | `3` | `1` | `pr:312` |
| `boltons` | `H_future` | `kilo_workspace` | `boltons__hist__022` | `verified_pass` | `True` | `iterutils` | `3` | `1` | `pr:312` |
| `boltons` | `H_future` | `codex_workspace` | `boltons__hist__023` | `verified_pass` | `True` | `tbutils` | `2` | `1` | `pr:332` |
| `boltons` | `H_future` | `kilo_workspace` | `boltons__hist__023` | `verified_pass` | `True` | `tbutils` | `2` | `1` | `pr:332` |
| `boltons` | `H_future` | `codex_workspace` | `boltons__hist__027` | `verified_pass` | `True` | `cacheutils` | `3` | `1` | `pr:349` |
| `boltons` | `H_future` | `kilo_workspace` | `boltons__hist__027` | `verified_pass` | `True` | `cacheutils` | `3` | `1` | `pr:349` |
| `attrs` | `B_eval` | `codex_workspace` | `attrs__hist__001` | `verified_pass` | `True` | `_make` | `3` | `1` | `issue:611` |
| `attrs` | `B_eval` | `kilo_workspace` | `attrs__hist__001` | `verified_pass` | `True` | `_make` | `3` | `1` | `issue:611` |
| `attrs` | `B_eval` | `codex_workspace` | `attrs__hist__003` | `verified_fail` | `True` | `_make` | `3` | `1` | `pr:506` |
| `attrs` | `B_eval` | `kilo_workspace` | `attrs__hist__003` | `verified_pass` | `True` | `_make` | `3` | `1` | `pr:506` |
| `attrs` | `B_eval` | `codex_workspace` | `attrs__hist__004` | `verified_pass` | `True` | `_make` | `2` | `1` | `issue:626` |
| `attrs` | `B_eval` | `kilo_workspace` | `attrs__hist__004` | `verified_pass` | `True` | `_make` | `2` | `1` | `issue:626` |
| `attrs` | `B_eval` | `codex_workspace` | `attrs__hist__008` | `verified_pass` | `True` | `__init__/_next_gen` | `7` | `2` | `pr:669` |
| `attrs` | `B_eval` | `kilo_workspace` | `attrs__hist__008` | `verified_pass` | `True` | `__init__/_next_gen` | `7` | `2` | `pr:669` |
| `attrs` | `H_future` | `codex_workspace` | `attrs__hist__012` | `verified_fail` | `True` | `_make` | `4` | `1` | `issue:680` |
| `attrs` | `H_future` | `kilo_workspace` | `attrs__hist__012` | `verified_fail` | `True` | `_make` | `4` | `1` | `issue:680` |
| `attrs` | `H_future` | `codex_workspace` | `attrs__hist__013` | `verified_fail` | `True` | `_next_gen` | `3` | `1` | `pr:687` |
| `attrs` | `H_future` | `kilo_workspace` | `attrs__hist__013` | `verified_fail` | `True` | `_next_gen` | `3` | `1` | `pr:687` |
| `attrs` | `H_future` | `codex_workspace` | `attrs__hist__023` | `verified_fail` | `True` | `_make` | `2` | `1` | `issue:593` |
| `attrs` | `H_future` | `kilo_workspace` | `attrs__hist__023` | `verified_pass` | `True` | `_make` | `2` | `1` | `issue:593` |
| `attrs` | `H_future` | `codex_workspace` | `attrs__hist__027` | `verified_fail` | `True` | `_funcs` | `5` | `1` | `issue:766` |
| `attrs` | `H_future` | `kilo_workspace` | `attrs__hist__027` | `policy_violation` | `False` | `_funcs` | `5` | `1` | `issue:766` |

## Sanitization

This artifact includes score-table statuses and safe task metadata only. It
does not include raw verifier logs, hidden test material, raw patches,
prompts, completions, or ACUT transcripts.
