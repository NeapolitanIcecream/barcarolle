# Phase 1 Preregistered Clean Future-Holdout Preflight

Status: passed.

Generated: 2026-05-22T10:56:23Z.

## Environment

- Branch: `codex/restart-benchmark-compiler`
- Starting HEAD: `276980a1048b46c878b2ccb31bdd94ec34b16b88`
- Python: `Python 3.9.6`
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`
- Codex CLI: `codex-cli 0.133.0`
- Kilo CLI: `7.3.1`
- Required endpoint env after sourcing `~/.zshrc`: present
- Secret values printed: `false`
- Paid ACUT calls made in preflight: `false`

## Worktree State

`git diff --check` passed.

Starting status:

```text
## codex/restart-benchmark-compiler...origin/codex/restart-benchmark-compiler [ahead 151]
?? docs/experiments/phase-1-preregistered-clean-future-holdout-paid-validation-runbook.md
```

The untracked runbook file is the runbook being executed in this session. No
conflicting existing changes were found.

Recent commits:

```text
276980a1 Refresh Phase 1 boundary after clean supply mining
baa95965 Decide Phase 1 clean outcome-unseen supply mining
e688df62 Integrate clean supply overlay with future holdout design
64ff119f Build Phase 1 clean outcome-unseen supply overlay
996619ff Mine Boltons clean outcome-unseen supply
7035ea48 Add Phase 1 clean outcome-unseen supply mining tooling
366c6207 Configure Phase 1 clean outcome-unseen supply mining
40101fe6 Record Phase 1 clean outcome-unseen supply preflight
```

## Frozen Design Gates

- Clean supply decision: `boltons_clean_supply_ready_for_preregistered_validation`
- Clean supply ready: `true`
- Preregistration status: `frozen`
- Selected repos: `boltons`
- `B_eval`: `boltons__clean_ext__001`, `boltons__clean_ext__008`, `boltons__clean_ext__010`, `boltons__hist__011`
- `H_future`: `boltons__clean_ext__017`, `boltons__hist__022`, `boltons__hist__023`, `boltons__hist__027`
- Existing future-holdout paid calls: `false`
- Existing `B_eval` scoreable cells: `0`
- Existing `H_future` scoreable cells: `0`
- Predictive validity established: `false`

## Baseline Checks

- `uv run --project experiments/phase1_compiler pytest -q` -> `56 passed in 0.31s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`

## Acceptance

All Step 0 entry gates passed. Paid work remains disabled until the local
tooling and paid-entry gates pass in later steps.
