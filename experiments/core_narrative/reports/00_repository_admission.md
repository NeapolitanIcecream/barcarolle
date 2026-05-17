# Phase 0 Repository Admission

Protocol: `external-calibrated-repo-benchmark-v1`
Status: `external_and_b_primary_frozen`
Generated at: `2026-05-15T16:49:01.231198Z`

## External Dataset Snapshot

| Dataset | Split | Total rows | Candidate repo counts | Revision |
|---|---:|---:|---|---|
| `SWE-bench/SWE-bench_Verified` | `test` | 500 | `sympy`=75, `django`=231, `sphinx`=44 | `91aa3ed51b709be6457e12d00300a6a596d4c6a3` |
| `SWE-bench/SWE-bench` | `test` | 2294 | `sympy`=386, `django`=850, `sphinx`=187 | `7074ef12ea2a6f70a228943c1336553333c22786` |

## Candidate Repositories

| Repo | Verified E | E after smoke | Full E | Recent B design | B primary | Ref pass | No-op fail | Recommendation | Blockers |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `sympy` | 75 | 48 | 386 | 828 | 20 | 1.0 | 1.0 | `primary_external_and_b_frozen` | none |
| `django` | 231 | None | 850 | 448 | None | None | None | `backup` | none |
| `sphinx` | 44 | None | 187 | 182 | None | None | None | `backup` | none |

## Local Infra

- Docker available: `True`
- SWE-bench Python module available: `True`
- Codex CLI version: `codex-cli 0.130.0`

## SWE-bench Gold Smoke

- Smoke id: `external_calibrated_sympy_e_v1_gold_smoke_20260515_w48`
- Repo: `sympy/sympy`
- Instance ids: `sympy__sympy-15017, sympy__sympy-19783, sympy__sympy-14976, sympy__sympy-13615, sympy__sympy-18211, sympy__sympy-15599, sympy__sympy-22914, sympy__sympy-24562, sympy__sympy-20916, sympy__sympy-21847, sympy__sympy-13091, sympy__sympy-13372, sympy__sympy-12419, sympy__sympy-23824, sympy__sympy-24066, sympy__sympy-24661, sympy__sympy-13877, sympy__sympy-13798, sympy__sympy-15976, sympy__sympy-20154, sympy__sympy-20438, sympy__sympy-18763, sympy__sympy-21930, sympy__sympy-20428, sympy__sympy-15349, sympy__sympy-13757, sympy__sympy-22080, sympy__sympy-16886, sympy__sympy-16450, sympy__sympy-13852, sympy__sympy-13480, sympy__sympy-16792, sympy__sympy-13031, sympy__sympy-24443, sympy__sympy-23950, sympy__sympy-18698, sympy__sympy-23262, sympy__sympy-20801, sympy__sympy-12481, sympy__sympy-20590, sympy__sympy-19954, sympy__sympy-19495, sympy__sympy-14531, sympy__sympy-19040, sympy__sympy-14248, sympy__sympy-17630, sympy__sympy-23413, sympy__sympy-16597`
- Completed/resolved/errors: `48` / `48` / `0`
- Pass: `True`
- Raw gold patch/eval/test artifacts retained: `False`

## Recommendation

- Phase 0 status: `external_and_b_primary_frozen`
- Next repo for infra smoke: `sympy`
- Primary repo for B generation: `sympy`
- Final primary repo declared: `True`

## Boundary

This artifact does not authorize ACUT runs. It keeps raw SWE-bench statements, patches, test patches, and commit SHAs out of the public artifact. If B admission is present, any remaining verifier-gate weakness must be resolved or explicitly accepted before primary execution.
