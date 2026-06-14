# Agent Tuning Phase 1 proof-of-injection smoke tests

生成日期：2026-06-14

## 结论

Package 4 使用真实 Codex/Kilo CLI adapters 和本地 fake OpenAI-compatible endpoint 完成 no-paid proof-of-injection。没有调用 paid LLM endpoint，`paid_calls_used = 0`。

结果：至少一个真实 Agent 有通过的 artifact 注入路径。实际上，Codex 与 Kilo 的主要 repo-local instruction surfaces 都能让固定短语进入 real CLI 的 request/output path。

## 方法

smoke runner：

```text
experiments/agent_tuning_demo/tools/agent_injection_smoke.py
```

运行方式：

```text
uv run --project experiments/phase1_compiler python experiments/agent_tuning_demo/tools/agent_injection_smoke.py --suite injection --out experiments/agent_tuning_demo/results/injection_smoke_tests.json
```

测试方式：

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
```

验证逻辑：

1. 创建临时 Git workspace；
2. 用 Package 3 helper 注入 artifact；
3. 用真实 `codex_workspace_adapter.py` 或 `kilo_workspace_adapter.py` 启动 CLI；
4. 将 `LLM_BASE_URL` 指向本地 fake endpoint，`LLM_API_KEY` 设为本地 dummy；
5. endpoint 只在内存中检查 request body / CLI output 是否包含固定短语；
6. committed result 只保留 booleans、counts、paths、hashes、exit code、latency 和 sanitized injection records。

raw request body、stdout/stderr、solver workspace、verifier workspace、prompt/completion 没有写入仓库。

## 结果表

| agent | surface | artifact path | loaded observed | exit | request path | 说明 |
| --- | --- | --- | --- | ---: | --- | --- |
| Codex | repo `AGENTS.md` | `AGENTS.md` | yes | 124 | `/v1/responses` | `AGENTS.md` 固定短语进入 request/output path；fake endpoint 未完整模拟 Codex loop，adapter 返回 timeout status |
| Codex | explicit skill | `.agents/skills/barcarolle-smoke/SKILL.md` | yes | 124 | `/v1/responses` | skill metadata 固定短语进入 request/output path；未证明 full `SKILL.md` on-demand loading |
| Codex | implicit skill | `.agents/skills/barcarolle-implicit-smoke/SKILL.md` | yes | 124 | `/v1/responses` | implicit skill metadata 可见；不作为 Phase 2 主 surface |
| Kilo | repo `AGENTS.md` | `AGENTS.md` | yes | 0 | `/v1/chat/completions` | `AGENTS.md` 固定短语进入 request/output path，fake endpoint 下正常退出 |
| Kilo | `.kilo/rules` | `.kilo/rules/barcarolle-smoke.md`, `kilo.jsonc` | yes | 0 | `/v1/chat/completions` | project rule 固定短语进入 request/output path；依赖 project `kilo.jsonc` instructions |
| Kilo | explicit skill | `.kilo/skills/barcarolle-smoke/SKILL.md` | yes | 0 | `/v1/chat/completions` | skill metadata 固定短语可见；full `SKILL.md` 使用仍需 skill tool call 证据 |
| Kilo | implicit skill | `.kilo/skills/barcarolle-implicit-smoke/SKILL.md` | yes | 0 | `/v1/chat/completions` | implicit skill metadata 可见；不作为 Phase 2 主 surface |

## proof-of-injection 判定

通过：

- Codex repo `AGENTS.md` request-capture proof；
- Codex repo skill metadata request-capture proof；
- Kilo repo `AGENTS.md` request-capture proof；
- Kilo project rule request-capture proof；
- Kilo skill metadata request-capture proof。

风险/限制：

- Codex 在 fake endpoint 下返回 adapter timeout status，因此本 smoke 只证明 artifact 进入真实 CLI request/output path，不证明 Codex 在 no-paid mock 下完成完整 run loop。
- Skill smoke 证明 metadata 可见，不证明 full `SKILL.md` 被 on-demand 读取；Phase 2 若以 skill 为主，最好先用 explicit trigger 加一个最小 paid 或更完整 fake-tool smoke。
- Kilo rules 最可靠的形式是同时注入 `kilo.jsonc` 的 `instructions` 和 `.kilo/rules/*.md`，单独放 rule 文件是否自动加载没有作为通过结论。

## Phase 2 含义

真实 Agent artifact injection path 已存在。最稳的 Phase 2 第一路径是 Kilo `AGENTS.md` 或 Kilo `.kilo/rules`，因为 fake endpoint 下既观察到注入，又正常退出。Codex `AGENTS.md` 也能证明注入，但需要在 Phase 2 前用更完整的 mock 或最小 paid smoke 解除 fake-endpoint timeout caveat。
