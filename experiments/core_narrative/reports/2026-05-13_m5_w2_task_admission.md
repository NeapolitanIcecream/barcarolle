# M5-W2 RWork-v2 Task Admission

Date: 2026-05-13

## Summary

RWork-v2 now has 10 admitted primary Click tasks, `click__rwork__101` through `click__rwork__110`. The family quotas match the M5-W2 protocol:

| Family | Tasks |
|---|---|
| option/default/envvar/flag_value semantics | `101`, `102`, `103` |
| CliRunner/testing/input-output isolation | `104`, `105` |
| prompt/termui/output rendering | `106`, `107` |
| type conversion / parameter normalization | `108`, `109` |
| mixed integration | `110` |

Admission smoke result: `10/10` accepted.

Evidence:

- materialization summary: `experiments/core_narrative/results/m5_w2_rwork_v2_materialize_20260513.json`;
- admission smoke summary: `experiments/core_narrative/results/m5_w2_rwork_v2_admission_smoke_20260513.json`;
- private raw smoke artifacts: `experiments/core_narrative/large_artifacts/m5_w2_admission_smoke_20260513/`.

## Admission Criteria

Each primary task passed both executable checks:

- no-op base verifier status was `failed`;
- source-target reference patch verifier status was `passed`.

The initial verifier command for `click__rwork__109` pointed at the wrong test module and failed with pytest exit code `4`; after correcting the verifier to `tests/test_basic.py`, the full 10-task admission smoke passed.

## Reserve Tasks

Four reserve candidates are preregistered in `experiments/core_narrative/configs/tasks/rwork_click_v2_reserve.yaml`. They are selected but not admitted. A reserve may replace a primary task only after its own no-op/reference admission smoke passes and the substitution is recorded before W2 primary scoring.
