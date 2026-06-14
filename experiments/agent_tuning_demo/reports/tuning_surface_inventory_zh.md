# Agent Tuning Phase 1 调优 surface inventory

生成日期：2026-06-14

## 结论

Phase 2 最适合先测试真实 Agent 的软指令 artifact，而不是模型选择或大范围 runtime policy。当前最推荐的两个 surface 是：

1. Codex repo `AGENTS.md` appendix：最通用，Codex 文档说明 project-scope `AGENTS.md` 在 Agent 开始工作前进入 instruction chain。
2. Codex repo skill `.agents/skills/<skill>/SKILL.md` 的显式触发：Codex 文档说明 repository skills 会从 `.agents/skills` 扫描，metadata 先入 context，full `SKILL.md` 在 Agent 选择使用时再加载。

Kilo 的 `AGENTS.md`、`.kilo/rules/*.md`、`.kilo/skills/*/SKILL.md` 都是可注入候选；但在本仓库当前 `kilo_workspace_adapter.py` 的 `--pure` + isolated config 运行方式下，rules/skills 是否在 `kilo run` noninteractive 模式稳定加载必须由 Package 4 smoke test 证明后再作为 Phase 2 主路径。

## hard policy 与 soft instruction 的区别

软指令 surface：

- `AGENTS.md`；
- `SKILL.md`；
- Kilo rules；
- harness prompt/context appendix。

这些 surface 能影响模型行为，但不能强制执行。它们适合作为 GEPA/Phoenix/SkillOpt-style proposer 的输出 artifact。

硬 policy / selection knobs：

- timeout；
- public-test policy；
- retry/self-check wrapper；
- approval/sandbox/tool permissions；
- model selection / reasoning effort。

这些更像 Agent policy 或 Agent selection 变量，能直接改变运行预算和可用动作。Phase 2 若要调它们，必须单独声明 estimand，不能和 `SKILL.md`/rules tuning 混为一类。

## surface matrix

| agent_id | surface | artifact_type | can_inject | can_observe_loaded | can_affect_behavior | requires_adapter_change | recommended_for_phase2 | risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_workspace | repo `AGENTS.md` appendix | `agents_md_appendix` | yes | yes, via request-capture smoke | yes | no | yes | soft instruction, not enforcement |
| codex_workspace | explicit repo skill | `skill_md` | yes | yes, via request-capture smoke | yes | no | yes | explicit trigger couples task text to skill |
| codex_workspace | implicit repo skill | `skill_md` | yes | yes, if metadata appears | likely | no | risky | implicit match may be omitted or ignored |
| codex_workspace | harness prompt/context | `policy_snippet` | yes | yes | yes | yes | no, except diagnostic | less deployable; changes Barcarolle harness layer |
| codex_workspace | runtime policy | `policy_snippet` | partial | yes | yes | yes | restricted | hard policy/control knob, not pure artifact tuning |
| codex_workspace | model/reasoning | `policy_snippet` | yes | yes | yes | yes | no | Agent-selection knob unless Phase 2 explicitly optimizes policy |
| kilo_workspace | repo `AGENTS.md` | `agents_md_appendix` | yes | yes, via request-capture smoke | yes | no | maybe | must prove loading under `kilo run --pure` |
| kilo_workspace | `.kilo/rules/*.md` | `kilo_rule` | yes | yes, via request-capture smoke | yes | no or config-dependent | maybe | project rule discovery may depend on config/instructions |
| kilo_workspace | explicit Kilo skill | `skill_md` | yes | yes, via request-capture smoke | yes | no | maybe | noninteractive skill loading must be proven |
| kilo_workspace | implicit Kilo skill | `skill_md` | yes | yes, if metadata appears | likely | no | risky | Kilo docs say the LLM decides from description; fragile for automated tuning |
| kilo_workspace | harness prompt/context | `policy_snippet` | yes | yes | yes | yes | no, except diagnostic | less deployable; adapter prompt becomes the tuned artifact |
| kilo_workspace | runtime policy | `policy_snippet` | partial | yes | yes | yes | restricted | hard policy/control knob; must be separated from text artifact tuning |
| kilo_workspace | model/reasoning | `policy_snippet` | yes | yes | yes | yes | no | Agent-selection knob, not first tuning target |

## 推荐 Phase 2 surface

Primary: Codex repo `AGENTS.md` appendix or explicit repo skill. Use one surface at a time in Phase 2 so attribution is clear. If Package 4 proves Kilo rules/skills load reliably and Package 5 shows behavior change, Kilo can remain a candidate, but it should not be the first path until those smoke tests pass.

Fallback within real-Agent path: Kilo `.kilo/rules/barcarolle.md` or repo `AGENTS.md`, because Kilo docs document both customization modes and they map naturally to external proposer output.

Not primary: model selection/reasoning effort. Those variables are valuable, but they belong to Agent selection or runtime-policy optimization rather than artifact tuning.

## sources checked

- Codex `AGENTS.md`: https://developers.openai.com/codex/guides/agents-md
- Codex skills: https://developers.openai.com/codex/skills
- Kilo `AGENTS.md`: https://kilo.ai/docs/customize/agents-md
- Kilo custom rules: https://kilo.ai/docs/customize/custom-rules
- Kilo custom instructions: https://kilo.ai/docs/customize/custom-instructions
- Kilo skills: https://kilo.ai/docs/customize/skills
- Kilo CLI: https://kilo.ai/docs/code-with-ai/platforms/cli
