# Agent Tuning artifact schema 与注入记录

生成日期：2026-06-14

## 结论

Package 3 定义了两个 JSON schema，并新增一个小型 helper：

- `experiments/agent_tuning_demo/schemas/tuning_artifact.schema.json`
- `experiments/agent_tuning_demo/schemas/artifact_injection_record.schema.json`
- `experiments/agent_tuning_demo/tools/tuning_artifacts.py`

helper 的职责只限于 Phase 1/Phase 2 所需的 artifact materialization：

1. 验证 artifact 必含字段；
2. 支持 `agents_md_appendix`、`skill_md`、`kilo_rule`、`policy_snippet`；
3. 拒绝 absolute path、`..`、反斜杠等非安全 workspace path；
4. 用 canonical JSON 计算确定性 `sha256:` hash；
5. 默认拒绝 `holdout_derived: true` 的 artifact；
6. 写入声明的 workspace-relative path；
7. 生成只含路径、hash、run_id、surface、时间和 cleanup policy 的 sanitized injection record。

它不记录 raw prompt、raw completion、raw transcript、solver workspace、verifier workspace 或 endpoint secret。

## artifact record

artifact schema 要求每条记录包含：

- `artifact_id`
- `artifact_type`
- `target_agent`
- `changed_files`
- `files`
- `hash`
- `intended_effect`
- `rollback_plan`
- `optimizer_source`
- `visible_to_optimizer`
- `holdout_derived`

`hash` 由 helper 对去掉 `hash` 字段后的 artifact payload 做 canonical JSON hash 生成，格式为 `sha256:<64 hex>`。`changed_files` 必须与 `files[*].workspace_relative_path` 完全一致，避免 optimizer 声明和实际写入不一致。

## injection record

injection record schema 要求每条记录包含：

- `run_id`
- `artifact_id`
- `artifact_hash`
- `target_agent`
- `surface`
- `workspace_relative_paths`
- `injected_at`
- `cleanup_policy`

record 不包含 artifact content。它可以安全提交，用于证明某个 run 的哪个 surface 收到了哪个 hash 的 artifact。

## example

一个 Codex `AGENTS.md` appendix artifact 的核心结构如下：

```json
{
  "schema_version": "barcarolle.agent_tuning_demo.tuning_artifact.v1",
  "artifact_id": "codex-agents-smoke-v1",
  "artifact_type": "agents_md_appendix",
  "target_agent": "codex_workspace",
  "changed_files": ["AGENTS.md"],
  "files": [
    {
      "workspace_relative_path": "AGENTS.md",
      "content": "BARCAROLLE_INJECTION_ACTIVE\n",
      "write_mode": "append"
    }
  ],
  "hash": "sha256:<computed>",
  "intended_effect": "prove Codex can receive repo instructions",
  "rollback_plan": "discard the solver workspace after the run",
  "optimizer_source": "phase1_static_smoke",
  "visible_to_optimizer": true,
  "holdout_derived": false
}
```

## validation

新增测试覆盖：

- hash 计算确定性；
- append 写入和 sanitized injection record；
- unsafe path 拒绝；
- holdout-derived artifact 默认拒绝；
- schema 文件是合法 JSON object。

本 package 的 focused test command：

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
```
