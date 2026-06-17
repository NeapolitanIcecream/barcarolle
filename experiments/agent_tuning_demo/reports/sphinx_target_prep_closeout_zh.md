# Sphinx target-prep closeout

生成时间：`2026-06-17T10:51:22+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 简短建议

终态：`sphinx_ready_for_paid_baseline_preregistration`。

建议把 `sphinx-doc/sphinx` 推进到下一份 paid-baseline-preregistration runbook，但本轮不授权任何付费执行。下一步应冻结 Sphinx certification-expanded task manifest、Agents、baseline-discovery cells、endpoint proof、预算/timeout stop、score-join rules 和成功标准，然后停下等显式批准。

## 本轮测试了什么

- 写入 Sphinx target profile/package map：`experiments/agent_tuning_demo/config/sphinx_target_profile.json`。
- 当前 checkout targeted smoke：`tests/test_util/test_util.py` 和 `tests/test_config/test_config.py`。
- version-aware verifier preflight：5 个历史 changed-test replay 候选。
- bounded inventory：180 条候选，`pre_2022`、`2022_2023`、`2024_plus` 各 60 条。
- bounded no-paid certification/replay wave：24 条，三个时间桶各 8 条。
- simple rolling-origin policy：`fixed_task_count_40_20_20_stride20`。

## Certification / Replay Conversion

Preflight 在修复 profile/test-entry 边界后为 `4/5` 通过。修复内容很窄：只做 date-compatible historical profiles、把 `tests/roots` support files 与 pytest entry files 分开、补充 Sphinx 历史测试需要的 `html5lib`。

Certification wave 为 `16/24` 通过，conversion rate `0.6667`。失败标签：

- `reference_target_test_failure`: 5
- `base_passed_changed_tests_not_meaningful`: 2
- `reference_dependency_mismatch_or_install_failed`: 1

## Verifier Speed

当前 smoke 为 `2/2` 通过，等级 `ideal_under_60s`。Certification wave verifier duration：median `7.78s`，p95 `24.333s`，max `42.758s`。这对 targeted verifier 是 practical。

## Rolling-Origin Feasibility

用 180 条 inventory 和 0.6667 conversion 估算，projected certified count 约 `120`。主策略使用 task-time 升序、历史 train 累积、selected/future 不重叠：

| Origin | Train | Selected benchmark | Future | Baseline cells | Before/after tuning cells |
| --- | --- | --- | --- | --- | --- |
| `origin_40` | 40 | 20 | 20 | 80 | 40 |
| `origin_60` | 60 | 20 | 20 | 80 | 40 |
| `origin_80` | 80 | 20 | 20 | 80 | 40 |

Baseline discovery 估算为 `80` cells/window，三窗口合计 `240` cells。未来 paid tuning 的 before/after 估算为 `40` cells/window，三窗口合计 `120` cells。以上都不是本轮授权。

## 是否优于 attrs / click / boltons

是。Sphinx 比 attrs/click/boltons 更适合 Agent Tuning Demo 的下一目标：

- Sphinx 有 180 条 bounded inventory，按 wave conversion 投影约 120 条 certified support。
- Sphinx 支持 3 个 projected rolling-origin windows。
- Sphinx targeted verifier speed 在几十秒以内。
- attrs/click 仍是约 31/30 release-eligible 小池；boltons 约 57 projected release tasks，仍不足以支撑更强 multi-window tuning story。

## 仍不支持什么

- 没有运行任何 paid Agent cells、paid LLM calls、paid tuner/proposer calls、paid baseline discovery 或 before/after tuning experiments。
- rolling-origin windows 仍是由 24-row wave 和 180-row inventory 推出的 feasibility policy，不是已冻结的 full certified manifest。
- 本轮不证明 tuning improvement、predictive validity 或跨仓库泛化。
- Sphinx profile 不是通用 Python historical environment solver。

## Exact Next Runbook Recommendation

下一份 runbook 应是：`Sphinx paid-baseline-preregistration runbook`。

它应冻结 certification-expanded task manifest，锁定 Agents、baseline-discovery cells、seeds、`LLM_BASE_URL`/`LLM_API_KEY` endpoint proof、cost/timeout stop、score-join rules、success criteria 和 artifact hygiene；在任何 paid execution 前停止并等待显式批准。

## Verification

- `uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q` -> `44 passed`
- `git diff --check` -> passed
- hygiene scan -> `experiments/demo_common/workspace_inputs.py`，这是 tracked source helper filename，不是 solver/verifier workspace、raw artifact、prompt、completion、transcript、cache 或 secret。
