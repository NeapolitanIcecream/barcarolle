# Agent 选型 Demo Strict Completion Closeout

生成日期：2026-06-13

## 执行状态

执行分支：`codex/agent-selection-demo-2026-06-12`。

本 closeout 覆盖 strict runbook：

```text
docs/research/agent-selection-demo-strict-completion-runbook-2026-06-13.md
```

结论：mandatory packages 已完成；Kilo frozen top-2 repeat 仍是 infrastructure blocker；second repo `python-attrs/attrs` 是 supply-ready 但不是 immediate-paid-matrix-ready；Agent tuning feedback summary 已有 runnable generator。

## Mandatory package status

| Package | Status | Canonical output |
| --- | --- | --- |
| 1. state audit and gap list | completed | `demo_remaining_gap_audit_zh.md` |
| 2. tooling/artifact hygiene audit | completed | `demo_tooling_artifact_hygiene_audit_zh.md` |
| 3. Kilo timeout and usage root-cause work | completed | `kilo_timeout_usage_root_cause_zh.md` |
| 4. Kilo smoke/gate and frozen top-2 repeat attempt | completed with blocker | `top2_repeat_completion_zh.md` |
| 5. no-paid second-repo gate | completed | `second_repo_gate_zh.md` |
| 6. runnable Agent tuning feedback summary generator | completed | `agent_tuning_feedback_summary_zh.md` |
| 7. final package and process update | completed by this package | `final_agent_selection_demo_package_zh.md` and `PROCESS.md` |

Focused commits were made after packages 1-6; this closeout package records the final package and process update.

## Demo-level claim

Can claim:

- Barcarolle completed a real `mahmoud/boltons` target-repo Agent selection demo.
- It ran full Agent harnesses, captured workspace diffs, replayed scoreable diffs in clean verifier workspaces, and recorded quality, latency, cost-observation kind, usage coverage, and failure labels.
- The original selection recommendation was contradicted by fresh holdout.
- The demo shows why target-repo Agent selection needs holdout checks, repeatability/uncertainty reporting, cost-usage audit, and adapter reliability gates.

Cannot claim:

- predictive validity is proven;
- a global Codex/Kilo/GPT/Claude ranking exists;
- Kilo's holdout lead is stable;
- top-2 repeat produced a valid ranking;
- second-repo paid scoring is ready today;
- tuning has already improved any Agent.

## Kilo/repeat status

Kilo timeout/usage work improved the infrastructure around the blocker:

- adapter and workspace subprocess paths now clean process groups on timeout;
- the outer workspace runner gives adapter cleanup grace instead of racing the adapter timeout;
- sanitized rows now record whether the outer adapter command timed out;
- Kilo successful `step_finish` token events are parsable, and recovered smoke rows now have observed usage.

But the frozen repeat blocker remains:

- previous Kilo top-2 repeat rows: `boltons__clean_ext__017` and `boltons__hist__019`, both `acut_harness_error`, exit `124`, empty stdout/patch, no usage.
- strict completion attempt added one new Kilo row: `boltons__hist__020`, also `acut_harness_error`, exit `124`, latency `900.692s`, empty stdout/patch, no usage.
- `--stop-on-unscoreable` stopped the remaining Kilo paid repeat cells after that fresh timeout.

Current top-2 repeat accounting:

- scheduled cells: `20`
- completed cells: `13`
- scoreable cells: `10`
- Codex repeat: `7/10`
- Kilo repeat: `0/0` scoreable from `3` completed timeout rows
- conclusion: `infrastructure blocker still unresolved`

## Second-repo readiness

Second repo candidate: `python-attrs/attrs`.

No paid second-repo cells were run.

Gate result: `conditional_no_go_for_immediate_paid_matrix`.

Evidence:

- local checkout/setup works under ignored path;
- visible subset passed: `216 passed in 2.18s`;
- committed phase0 attrs JSONLs expose `28` certified rows;
- committed source-repair overlay promotes `3` more rows, bringing attrs to `31` release-eligible;
- one manual hidden verifier replay probe passed for `attrs__hist__008`;
- several older `test_make.py` replay probes exposed current dependency/Python drift, so verifier pinning is required.

Minimum repair before paid second-repo matrix:

- add `attrs_target_profile.json`;
- remove boltons-specific `repo_id` and fallback statement assumptions from demo package building;
- materialize or formally reference the 31-task attrs release manifest;
- pin the attrs verifier environment for historical tasks;
- rerun a no-paid attrs repository gate with reference replay samples and split/freeze dry run.

## Feedback generator

Runnable command:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler python experiments/agent_selection_demo/tools/agent_selection_demo.py tuning-feedback-summary --output experiments/agent_selection_demo/reports/agent_tuning_feedback_summary_zh.md
```

Outputs:

- `experiments/agent_selection_demo/reports/agent_tuning_feedback_summary_zh.md`
- `experiments/agent_selection_demo/results/agent_tuning_feedback_summary.json`

The generator reads only committed sanitized score tables, metrics, cost fields, and repeatability summary. It does not read raw prompts, raw completions, transcripts, solver workspaces, verifier workspaces, or provider logs. It explicitly frames the output as feedback input, not as tuning-result evidence.

## Paid cells used

Paid cells run inside the strict completion pass: `1`.

Breakdown:

- Kilo smoke/debug cells: `0` fresh paid cells. Existing smoke was recovered no-paid from ignored raw artifacts after the parser fix.
- Frozen top-2 repeat cells: `1` fresh Kilo cell, `top2_repeat__kilo_gpt_5_4__boltons__hist__020`, which timed out.
- Second-repo cells: `0`.

Pre-existing demo and repeat cells from earlier runs are preserved as historical artifacts, but they were not newly run in this strict completion pass.

## Tests and hygiene

Final validation run:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q
```

Result: `13 passed in 0.02s`.

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/phase0_headroom/tools/test_workspace_acut_run.py experiments/phase0_headroom/tools/test_cli_workspace_adapters.py experiments/phase0_headroom/tools/test_workspace_usage_import.py -q
```

Result: `38 passed in 4.48s`.

```text
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_attrs_source_repair.py -q
```

Result: `5 passed in 0.76s`.

```text
git diff --check
```

Result: passed.

Narrow artifact scan:

```text
git ls-files experiments/agent_selection_demo | rg '(__pycache__|\.pyc$|raw|transcript|workspace|\.DS_Store|\.pytest_cache|\.venv)' || true
```

Result: no hits.

Broader scan over demo, phase0 tools, and phase1 tools only hit committed phase0 tooling paths with `workspace` in their filenames. These are source/test files, not raw paid-call transcripts or solver/verifier workspaces.

## Canonical entry points

- Final narrative: `experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md`
- Closeout: `experiments/agent_selection_demo/reports/demo_completion_closeout_zh.md`
- Kilo root cause: `experiments/agent_selection_demo/reports/kilo_timeout_usage_root_cause_zh.md`
- Repeat completion/blocker: `experiments/agent_selection_demo/reports/top2_repeat_completion_zh.md`
- Second-repo gate: `experiments/agent_selection_demo/reports/second_repo_gate_zh.md`
- Feedback summary: `experiments/agent_selection_demo/reports/agent_tuning_feedback_summary_zh.md`
- Machine-readable repeat summary: `experiments/agent_selection_demo/results/top2_repeatability_check.json`
- Machine-readable feedback summary: `experiments/agent_selection_demo/results/agent_tuning_feedback_summary.json`
- Process handoff: `PROCESS.md`

## Recommended next work

For Kilo stability: continue adapter/provider timeout diagnosis before any broader repeat.

For second repo: repair attrs packaging and verifier pinning, then rerun a no-paid attrs repository gate. Do not start paid second-repo cells until that gate passes.

For Agent tuning: use the runnable feedback summary as backlog input only; run a controlled before/after tuning experiment before claiming improvement.

## Predictive-validity completion addendum

本 addendum 覆盖 predictive-validity completion pass。它补上 strict completion pass 当时仍标为 future work 的部分。

### 1. Frozen estimand

Frozen estimand:

```text
How accurately a benchmark selection frozen at origin T predicts a complete Agent's later verified pass rate on the same target repository.
```

Agent unit 是完整 Agent：`model + harness + prompt/tools/runtime policy`。

Primary metric 是 pass-rate MAE，平均单位是 `(repo, origin/window, Agent)` slices。

### 2. Rolling-origin infrastructure

Feasibility command:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler python experiments/agent_selection_demo/tools/agent_selection_demo.py predictive-validity-feasibility --output experiments/agent_selection_demo/reports/predictive_validity_feasibility_zh.md
```

Evaluation command:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler python experiments/agent_selection_demo/tools/agent_selection_demo.py rolling-origin-eval --protocol experiments/agent_selection_demo/results/predictive_validity_protocol.json --window-inventory experiments/agent_selection_demo/results/predictive_validity_window_inventory.json --output experiments/agent_selection_demo/reports/rolling_origin_eval_zh.md
```

Outputs:

- `predictive_validity_window_inventory.json`
- `rolling_origin_eval.json`
- `rolling_origin_eval_slices.csv`

### 3. No-paid retrospective data

Inventory result:

- candidate repos: `attrs`, `boltons`, `click`
- windows: `5`
- metric slices: `208`
- baseline-comparison windows: `3`

Primary no-paid result:

- best simple baseline: `temporal_recent_baseline`, MAE `0.214900`
- best Barcarolle candidate: `coverage_constrained_unweighted`, MAE `0.209011`
- candidate minus best simple MAE: `-0.005889`
- catastrophic miss rate: `0.555556` for both
- rank top-agreement rate: `0.8125`
- mean recommendation regret: `0.041552`

### 4. Paid cells

Paid cells run for predictive-validity completion: `0`.

Decision: no paid pilot was needed for the demo story because the no-paid retrospective result already supplies numeric directional evidence. A future plan is capped at `40` cells in `predictive_validity_paid_pilot_plan.json`, but it was not executed.

### 5. Baseline result

The best promotable Barcarolle candidate beat the best simple baseline by a small MAE margin. This is `directional retrospective traction`, not predictive-validity proof. The result is still underpowered for a strong claim because it is retrospective/pseudo-future and the catastrophic miss rate did not improve.

### 6. Demo claim now

Can claim:

- target-repo Agent selection demo completed on `boltons`;
- selection recommendation was contradicted by fresh holdout;
- rolling-origin/pseudo-future infrastructure exists;
- no-paid retrospective metrics show small directional traction against simple baselines;
- paid-pilot boundary is defined and no new paid cells were spent.

### 7. Cannot claim

Cannot claim:

- predictive validity is established;
- current selector is generally superior;
- Kilo holdout lead is stable;
- any global Agent/model ranking;
- a bounded paid predictive-validity pilot completed.

### 8. Next experiment required

To move from directional evidence to proof, run a true future or strict preregistered rolling-origin validation: freeze repos, origins/cutoffs, task IDs, Agent configs, selectors, baselines, seeds, invalid-cell policy, score joins, and success thresholds before outcome join, then compare against the best simple baseline envelope with uncertainty reporting.

### 9. Tests and hygiene

Predictive-validity completion added focused demo tests for score-join deduplication, MAE/missing-cell policy, baseline envelope comparison, and recommendation regret.

Final validation:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q
```

Result: `17 passed in 0.04s`.

```text
PYTHONPATH=experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_retrospective_predictive_signal.py -q
```

Result: `6 passed in 0.68s`.

```text
git diff --check
```

Result: passed.

```text
git ls-files experiments/agent_selection_demo | rg '(__pycache__|\.pyc$|raw|transcript|workspace|\.DS_Store|\.pytest_cache|\.venv)'
```

Result: no hits. `rg` returned exit code `1`, which is expected when no prohibited tracked paths match.

### Predictive-validity canonical artifacts

- `experiments/agent_selection_demo/reports/predictive_validity_state_audit_zh.md`
- `experiments/agent_selection_demo/reports/predictive_validity_protocol_zh.md`
- `experiments/agent_selection_demo/reports/predictive_validity_feasibility_zh.md`
- `experiments/agent_selection_demo/reports/rolling_origin_eval_zh.md`
- `experiments/agent_selection_demo/reports/predictive_validity_retrospective_result_zh.md`
- `experiments/agent_selection_demo/reports/predictive_validity_paid_pilot_decision_zh.md`
- `experiments/agent_selection_demo/reports/predictive_validity_demo_story_zh.md`
- `experiments/agent_selection_demo/results/predictive_validity_evidence_ledger.json`
- `experiments/agent_selection_demo/results/predictive_validity_protocol.json`
- `experiments/agent_selection_demo/results/predictive_validity_window_inventory.json`
- `experiments/agent_selection_demo/results/rolling_origin_eval.json`
- `experiments/agent_selection_demo/results/rolling_origin_eval_slices.csv`
- `experiments/agent_selection_demo/results/predictive_validity_paid_pilot_plan.json`
