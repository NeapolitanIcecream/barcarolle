# Phase 1 Historical Environment Synthesis Process

Status: Steps 0-8 completed at 2026-05-26T08:55:59Z.

Plain-language summary: preflight passed. This run is local-only. Paid ACUT calls, paid replication, paid task-solving, and paid LLM statement generation are disabled. Historical target commands will use `uv run --no-project --isolated` so they do not inherit the Phase 1 compiler Python 3.11 project constraint.

## Ledger

- Step 0: Preflight - `completed`.
- Step 1: Input inventory - `completed`.
- Step 2: Historical environment tool and tests - `completed`.
- Step 3: Known failures replay under historical profiles - `completed`.
- Step 4: Reference gate subclassification - `completed`.
- Step 5: Recovered supply projection - `completed`.
- Step 6: Third repo local environment gate - `completed`.
- Step 7: Decision - `completed`.
- Step 8: Verification and closeout - `completed`.

## Preflight Notes

- Branch: `codex/restart-benchmark-compiler`.
- HEAD: `7000e6839cf1512a945e11690d024e9a76155388`.
- uv: `uv 0.11.16 (Homebrew 2026-05-21 aarch64-apple-darwin)`.
- Phase 1 Python: `Python 3.11.13`.
- Required uv run flags available: `--no-project`=true, `--isolated`=true, `--managed-python`=true, `--python`=true, `--exclude-newer`=true, `--with`=true, `--with-editable`=true.
- Scratch, workspace, cache, and external repo paths are ignored by git.
- Existing untracked runbook file is treated as input and is not part of the Step 0 experiment output commit.
