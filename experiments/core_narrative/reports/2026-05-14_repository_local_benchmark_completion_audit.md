# Repository-Local Benchmark Completion Audit

Status: `not_complete_blocked_before_task_admission_and_primary_runs`

Objective file: `/Users/chenmohan/Downloads/barcarolle-research-0514-1.md`

## Verdict

The 2026-05-14 experiment is not complete as a full C/R/W* benchmark run. The completed work is a repository-admission and protocol-gate phase. That phase blocks Click primary execution because Click has only 14 W* task-design candidates in the frozen `2026-02-14` to `2026-05-14` window, below the 20-task gate.

Do not mark the active goal complete from the current state. The next concrete unblocked step is Rich task admission, including Golden-Oracle construction for source-only W* candidates, or a separately preregistered gate revision.

## Prompt-To-Artifact Checklist

| Requirement | Status | Evidence | Gap |
|---|---|---|---|
| Pivot main line to repository-local benchmark generation and tuning validation; NFL only bonus | covered | `configs/repository_local_benchmark_20260514.yaml` | none |
| Freeze C/R/W* split at T0 `2026-05-14`; W* fixed to `2026-02-14`..`2026-05-14` | covered | `results/repository_local_benchmark_admission_20260514.json`, `configs/repository_local_benchmark_20260514.yaml` | none |
| Task 1: repository admission for Click/Rich/Black with counts, feasibility, family diversity, dependency risk, recommendation | partially covered | `reports/2026-05-14_repository_local_benchmark_admission.md` | Dependency-risk and measured test-runtime feasibility are not fully measured. |
| Task 2: Click C/R/W* construction with no-op/reference/leakage/family/difficulty/digests | blocked, not done | `reports/2026-05-14_repository_local_benchmark_gate.md` | Click W* supply is below gate; no 0514 Click denominator was admitted. |
| Task 3: Golden-Selector/Taskwright/Oracle/Auditor role isolation with prompt hashes, artifact digests, admission decisions | specified, not executed | `configs/repository_local_benchmark_20260514.yaml` | No 0514 role-run outputs or prompt hashes exist. |
| Task 4: ACUT/intervention manifests A0-A5, A4 limited to public statement + repo tree/source | partially covered | A0/A2/A3/A5 existing, A1/A4 Click variants added, `tools/repository_localization_hints.py` | Rich execution needs Rich or repository-neutral intervention variants. |
| Task 5: run R and W* one primary attempt per ACUT/task with fixed denominator and hidden verifier | not done | Gate report records non-action | No denominator was admitted; no primary attempts authorized or run. |
| Task 6: analyze R_score, W*_score, paired deltas, R-selected, W*-best, regret, correlation, family effects, ablation | not done | none | No primary result table exists. |
| Output: repository admission report | covered | `reports/2026-05-14_repository_local_benchmark_admission.md` | none |
| Output: task generation validity report | not done | none | No 0514 task admission was run. |
| Output: R/W* primary result report | not done | none | No primary attempts were run. |
| Output: decision-validity report | gate only | `reports/2026-05-14_repository_local_benchmark_gate.md` | R -> W* decision validity cannot be assessed without runs. |
| Output: threats-to-validity report | gate only | `reports/2026-05-14_repository_local_benchmark_gate.md` | Full experiment threats remain pending. |
| Prohibitions: do not use W* results to modify R, ACUT outputs to choose W*, old M5/M6 denominator mixing, post-hoc gate lowering, W* freshness overclaiming | covered for actions taken | Gate and protocol artifacts | Verified only for repository-admission/gate phase because no primary results exist. |

## Evidence Inspected

- `experiments/core_narrative/results/repository_local_benchmark_admission_20260514.json`
- `experiments/core_narrative/reports/2026-05-14_repository_local_benchmark_admission.md`
- `experiments/core_narrative/reports/2026-05-14_repository_local_benchmark_gate.md`
- `experiments/core_narrative/configs/repository_local_benchmark_20260514.yaml`
- ACUT manifests for A0-A5, including the newly added A1 and A4 Click variants.
- `experiments/core_narrative/tools/repository_local_benchmark_admission.py`
- `experiments/core_narrative/tools/repository_localization_hints.py`

## Additional Feasibility Observation

Rich ambient collect-only check:

```text
cwd: experiments/core_narrative/external_repos/rich
command: python3 -m pytest -q --collect-only tests
exit_code: 2
observed: 919 tests collected before 4 collection errors
missing imports: markdown_it, attr
```

`pyproject.toml` declares `markdown-it-py` as a project dependency and `attrs` as a dev dependency, so Rich task admission should use an isolated install that includes project and dev/test dependencies. This does not block Rich repository admission, but it remains a concrete dependency-readiness task before smoke-tested task admission.

## Verification Commands

Completed during the gate phase:

```text
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments/core_narrative/tools/test_repository_local_benchmark_admission.py experiments/core_narrative/tools/test_repository_localization_hints.py
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments/core_narrative/tools/test_m6_w3_freeze_integrity_audit.py experiments/core_narrative/tools/test_m6_w3_task_admission.py
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments/core_narrative/tools/test_apply_source_derived_url_policy.py experiments/core_narrative/tools/test_workspace_mode_runner.py experiments/core_narrative/tools/test_rgw_status_semantics.py
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/validate_acut_manifest.py experiments/core_narrative/configs/acuts/cheap-click-inert-control-v1.yaml experiments/core_narrative/configs/acuts/cheap-click-localization-tool-v1.yaml
python3 -m json.tool experiments/core_narrative/results/repository_local_benchmark_gate_20260514.json
git diff --check
```

These commands verify the committed gate tools and manifests. They do not verify the missing task admission, model runs, or R/W* analysis because those phases have not been executed.

## Next Work

Proceed with Rich task admission if the 0514 line continues. Rich passed repository admission, but W* has only a small direct source+test oracle surface; reaching 20 accepted W* tasks will require Golden-Oracle construction for source-only candidates before any ACUT primary attempt.
