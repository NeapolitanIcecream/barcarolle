# Repository-Local Benchmark Gate

Status: `blocked_before_primary_runs`

## Decision

The 2026-05-14 repository-local experiment is not authorized to run Click R/W* primary attempts under the frozen gate. Click has enough extended-R design supply but only 14 W* task-design candidates in the required `2026-02-14` to `2026-05-14` window, below the 20-task gate.

Rich is the only ready execution repository from the admission scan and should be used for the next task-admission phase if the 0514 line proceeds. Black remains blocked by the same W* supply gate.

## Evidence

| Repo | Ready | Strict R design | Extended R design | W* design | W* direct oracle | W* families | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| `click` | `false` | 2 | 53 | 14 | 11 | 4 | not authorized for full 0514 primary runs |
| `rich` | `true` | 47 | 74 | 25 | 9 | 5 | recommended execution repo for task admission |
| `black` | `false` | 20 | 46 | 16 | 12 | 4 | not authorized for full 0514 primary runs |

Source artifacts:

- `experiments/core_narrative/results/repository_local_benchmark_admission_20260514.json`
- `experiments/core_narrative/reports/2026-05-14_repository_local_benchmark_admission.md`
- `experiments/core_narrative/configs/repository_local_benchmark_20260514.yaml`

## Requested Outputs

- Repository admission report: produced.
- Task generation validity report: not produced because task admission has not been authorized or run.
- R/W* primary result report: not produced because no primary attempts are authorized before task admission.
- Decision-validity report: this gate report records the preregistered blocking decision.
- Threats-to-validity report: limited to the gate-level threats below.

## Threats

- The gate uses commit-history supply as repository admission, not task admission; no hidden verifier smoke has run.
- Source-only task-design candidates still require Golden-Oracle verifier construction before they can become tasks.
- Rich readiness does not imply Click evidence transfers directly; Rich needs repository-specific A1/A2/A3/A4 context variants before primary attempts.
- W* recency is only a split boundary and must not be described as proof that the work is absent from model training data.
- The old M5/M6 Click denominator is not a valid substitute for the 0514 W* denominator.

## Non-Actions

- No model calls were made.
- No R or W* primary attempts were run.
- No W* result was used to modify R.
- No ACUT output was used to choose W*.
- No success gate was changed after seeing results.
