# Agent Tuning Demo final report

## 结论

本轮完成了 Agent Tuning Demo。Terminal state: `agent_tuning_demo_complete`；result label: `agent_tuning_demo_complete_regressed`。

Barcarolle 在 `mypy` 上使用已认证任务供给，冻结了 corrected rolling-origin window：先从 origin 前历史池选择 benchmark，再在 artifact hash freeze 后才揭示未来 holdout 任务。调优 artifact 是一个可部署的 repo-local Kilo `AGENTS.md` appendix。

## 协议

- Primary repo: `mypy`。
- Origin: `origin_40`。
- Selected benchmark: `20` tasks；train feedback `12`，dev eval `8`。
- Future holdout: `20` tasks。
- Future holdout IDs/outcomes were not tuner inputs.

## Feedback 与 artifact

- Candidate artifacts: `experiments/agent_tuning_demo/results/agent_tuning_demo_candidate_artifacts.json`。
- Chosen artifact: `agent-tuning-demo-mypy-family-triage-loop` / `sha256:4cc09bb467d9cf638a619017caa59fe01b84c26c1a12f5b4a9a9be08f1149621`。
- Tuner path: train-only local rule proposer; no paid LLM proposer calls were needed.

## Dev 与 future 结果

- Dev gate decision: `choose_least_bad_candidate_for_required_holdout_story`。
- Future paired tasks: `20`。
- Future paired net wins: `-1`。
- Improved tasks: `4`；regressed tasks: `5`。

## Cost

- Total estimated/observed cost: `$29.39064915`。
- Cost ledger: `experiments/agent_tuning_demo/results/agent_tuning_demo_cost_ledger.jsonl`。
- Actual billed provider cost was not available from endpoint export, so observed-token and conservative estimates are reported separately in the cost summary.

## 支持与不支持的 claim

支持：Barcarolle 可以供应 repo-specific certified tasks，冻结无未来泄漏的 rolling-origin window，导出 train-only feedback，产出 deployable repo-local Agent artifact，并在未来 holdout 上完成 before/after 验证和成本记录。

不支持：这不是 predictive validity 证明，不是统计显著结论，不证明跨 repo 泛化，不是模型 fine-tuning，也不证明任意 opaque Agent 都能被这个方法稳定改进。
