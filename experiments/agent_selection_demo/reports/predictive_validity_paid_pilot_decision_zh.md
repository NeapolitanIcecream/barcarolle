# Predictive-validity Paid-pilot Decision

生成日期：2026-06-13

## Decision

Decision label：`no_paid_pilot_needed_for_demo_story`.

本 runbook 不运行新的 paid Agent cells。

原因：

- Package 5 已经用 committed sanitized outcomes 产出 numeric predictive metrics；
- best Barcarolle candidate `coverage_constrained_unweighted` 以 MAE `0.209011` 小幅 beat best simple baseline `temporal_recent_baseline` MAE `0.214900`；
- 这足以完成 demo 的 predictive-validity layer：directional retrospective traction, not proof；
- 新 paid cells 不会把 retrospective result 变成 predictive-validity proof，反而会扩大当前 demo 的 scope。

新增 paid cells：`0`。

## Current evidence status

| Question | Answer |
| --- | --- |
| Existing no-paid metric enough for demo story? | yes |
| Predictive validity proven? | no |
| Paid pilot required now? | no |
| Paid cells run in this package? | `0` |
| 40-cell boundary respected? | yes, because no cells were run |
| Kilo paid cells run? | `0` |

## Future bounded pilot preregistration

Machine-readable future plan：

```text
experiments/agent_selection_demo/results/predictive_validity_paid_pilot_plan.json
```

The plan is a later-execution preregistration, not an execution record. It freezes the intended boundary if a future session needs one bounded paid pilot after gates pass.

Planned maximum:

```text
2 repos x 2 complete Agent configurations x 10 future tasks = 40 cells
```

Candidate repos:

- `boltons`
- `click`

Why not run it now:

- current demo story already has no-paid retrospective metrics;
- Kilo repeat remains blocked in the demo path and must not receive new paid cells unless timeout gates pass;
- a future proof still needs true future or strict preregistered rolling-origin execution, not a quick paid add-on after seeing results.

## Stop conditions preserved

Future paid execution must stop before any paid call if:

- `LLM_BASE_URL` or `LLM_API_KEY` is missing;
- endpoint/model proof fails;
- secret isolation fails;
- Kilo is included and Kilo timeout gate fails;
- projected cells exceed `40`;
- raw prompts, completions, transcripts, solver/verifier workspaces, provider logs, or secrets would need to be committed;
- scoreable-cell rate cannot reach the preregistered gate.

## Claim boundary

The current demo can claim:

- rolling-origin/pseudo-future infrastructure exists;
- no-paid retrospective metrics show small directional traction against simple baselines;
- fresh boltons holdout contradiction motivates predictive-validity validation.

The current demo cannot claim:

- predictive validity is established;
- a paid future pilot was completed;
- Kilo holdout lead is stable;
- any global Agent or model ranking.

## Acceptance

- Clear no-paid decision produced.
- Future pilot plan exists and stays inside the 40-cell boundary.
- Paid cells used: `0`.
- No claim exceeds achieved evidence.
