# Agent Tuning Phase 1 上下文审计

生成日期：2026-06-14

## 结论

现有 Agent-selection / phase0 workspace tooling 可以复用为 Phase 2 的执行和验证外壳，但不能直接完成调优 artifact 注入。当前缺口是：在 solver workspace 初始化之后、真实 Codex/Kilo Agent 启动之前，没有一个可审计的 pre-run 注入点来写入 `AGENTS.md`、`SKILL.md`、Kilo rule 或 policy snippet。

因此 Phase 1 需要新增一个很窄的 helper：验证 artifact schema、写入声明的 workspace 相对路径、计算确定性 hash、生成 sanitized injection record。它不应重写 ACUT harness，也不应实现 Agent 内部搜索/编辑/retry 逻辑。

## 可复用代码路径

| 路径 | 可复用点 | Phase 1 影响 |
| --- | --- | --- |
| `experiments/phase0_headroom/tools/workspace_acut_run.py` | clean solver workspace、statement file、adapter invocation、diff capture、fresh verifier replay、hidden oracle injection、policy checks | Phase 2 主执行边界可沿用；需要注入 hook 或外层 wrapper |
| `experiments/agent_selection_demo/tools/agent_selection_demo.py` | task pool、candidate adapter config、stage result persistence、usage/cost parsing、score rows | 可沿用 agent config 和 score/report 口径 |
| `experiments/phase0_headroom/tools/codex_workspace_adapter.py` | `codex exec`、isolated `CODEX_HOME`、LLM endpoint provider、workspace `--cd` | Codex repo-local `AGENTS.md` / skills 是可测 surface |
| `experiments/phase0_headroom/tools/kilo_workspace_adapter.py` | `kilo run`、isolated config<external-user-home>、workspace `--dir`、generated provider config | Kilo repo-local `AGENTS.md` / `.kilo/rules` / `.kilo/skills` 是可测 surface |
| `experiments/phase0_headroom/tools/llm_endpoint_proxy.py` | child env secret isolation、`LLM_BASE_URL`/`LLM_API_KEY` forwarding | paid boundary 和 no-secret child process 逻辑可沿用 |

## Agent 表示方式

Codex-style Agent 当前由 adapter script、model、CLI flags、custom provider config 和 solver workspace 共同定义。`codex_workspace_adapter.py` 使用 `--ignore-user-config --ephemeral --json --cd <workspace> --sandbox workspace-write --model <model>`，并把 task statement 路径写进 prompt。

Kilo-style Agent 当前由 adapter script、model、CLI flags、generated `kilo.jsonc`、isolated `HOME`/`XDG_*` 和 solver workspace 共同定义。`kilo_workspace_adapter.py` 使用 `kilo run ... --pure --auto --format json --dir <workspace> --file <statement_file> --model <provider/model>`。

两者都是真实 workspace Agent，不是 one-shot diff generator。Barcarolle 不应该实现它们内部的 file search、editing loop、retry、tool-use 或 reasoning loop。

## 控制点

| 控制点 | 当前位置 |
| --- | --- |
| task text | `workspace_acut_run.render_statement()` 写入 solver `.barcarolle/statement.md`；demo runner 由 `statement_for()` 生成 |
| workspace path | `run_workspace_cell()` 的 `solver_workspace` / `verifier_workspace` |
| env vars | demo runner 和 adapters 要求 `LLM_BASE_URL`、`LLM_API_KEY`；child env 经 proxy sanitized |
| timeout | adapter config `timeout_seconds`、candidate `timeout_seconds`、verifier package timeout |
| model id | demo candidate config 和 adapter `--model` |
| cost/usage | `agent_selection_demo.usage_from_submission()`、cost ledger rows、`usage_observed`、token count fields |
| diff | `workspace_acut_run.capture_diff()` 写入 ignored raw path，committed submission only stores `patch_sha256` 和 changed paths |

## 注入能力审计

当前 runner 可以创建 solver workspace，但没有在 Agent invocation 前写入 artifact 的通用接口。可行实现方式有两类：

1. 外层 wrapper：先 archive/init workspace，再调用 helper 注入 artifact，再复用 adapter command 和后续 diff/replay 逻辑。
2. 给 `run_workspace_cell()` 增加可选 pre-run callback/config。

Phase 1 采用更保守的窄 helper，不直接改 scoreable runner 主流程。这样可以先证明注入和行为变化，避免把 feasibility runbook 变成大框架改造。

## 可观察行为字段

无需提交 raw transcript 的可观察字段包括：

- `submission.status`、`verifier.status`、`terminal_status` / score row；
- `changed_paths`；
- `patch_sha256`；
- `latency_seconds`；
- `adapter_timed_out` / timeout status；
- `usage_observed`、token counts、`estimated_cost_usd`；
- verifier exit code 和 duration；
- sanitized smoke summaries，例如 fixed phrase 是否出现在 real CLI 发往本地 fake endpoint 的 request 摘要里；
- public-test command 是否在 sanitized request/context 或 CLI event summary 中出现。

现有 committed fields 不稳定地记录 file reads / command trace；这些通常只存在 raw stdout/stderr 或 Agent JSON event 中。Phase 1 可以提交 derived booleans 和计数，但不能提交 raw request body、raw transcript、solver/verifier workspace。

## paid-call 与 hygiene 边界

本 runbook 默认 no-paid。真实 CLI smoke test 使用本地 fake OpenAI-compatible endpoint 捕获 request 摘要，不调用外部 paid endpoint。若后续必须 paid，必须只用 `LLM_BASE_URL` 和 `LLM_API_KEY`，并记录 paid cells、estimated cost、latency，同时 raw stdout/stderr、request captures、workspace、prompts、completions 均留在 ignored/local-only 路径。

本次 Phase 1 不运行完整 tuning demo，不启动 GEPA/DSPy/Phoenix optimization，不比较多 tuned variants on Holdout，不声称任何 tuned Agent improvement。
