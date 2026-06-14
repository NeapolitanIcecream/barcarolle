# Agent Tuning Phase 1 feasibility closeout

生成日期：2026-06-14

## readiness state

`ready_for_phase2_with_restrictions`

Phase 1 已完成 Agent Tuning Demo Phase 2 前的准备判断：真实 Codex/Kilo-style workspace Agents 可以接收 repo-local tuning artifacts，Barcarolle 可以记录 artifact-driven request-context 行为差异；但 no-paid smoke 尚未证明 artifact 会改变真实 tool command trace、file edits、diff、public-test execution 或 hidden-verifier outcome。

因此 Phase 2 可以启动 real-Agent artifact-tuning 路线，但必须先通过一个最小 action-level preflight，再开始 GEPA/Phoenix optimization。

## proof-of-injection

通过：

- Codex repo `AGENTS.md`：fixed phrase 进入 `/v1/responses` request/output path；
- Codex repo skills：`.agents/skills/*/SKILL.md` metadata 进入 `/v1/responses` request/output path；
- Kilo repo `AGENTS.md`：fixed phrase 进入 `/v1/chat/completions` request/output path，fake endpoint 下 exit 0；
- Kilo `.kilo/rules/*.md` + `kilo.jsonc` instructions：rule fixed phrase 进入 request/output path，exit 0；
- Kilo `.kilo/skills/*/SKILL.md`：skill metadata 进入 request/output path，exit 0。

风险：

- Codex proof 在 fake endpoint 下有 adapter timeout status；证明了注入，不证明完整 run-loop 可靠性。
- skill smoke 证明 metadata 可见，不证明 full `SKILL.md` on-demand loading。
- Kilo rules 的通过路径包含 `kilo.jsonc` instructions；单独 rule 文件未作为通过结论。

## behavior-change smoke

通过但受限：

- 同一个 `codex_workspace` Agent、同一个 task statement、同一个 `repo_AGENTS_md` surface；
- Variant A 指示不要运行测试；
- Variant B 指示运行 `python -m pytest tests/test_public_smoke.py -q`；
- 两个 variant 都 loaded；
- public-test instruction 只在 Variant B 的 sanitized observation 中出现；
- `paid_calls_used = 0`。

未证明：

- command trace 差异；
- file read/edit 差异；
- final diff 差异；
- public-test execution 差异；
- hidden verifier outcome 差异。

## supported and risky surfaces

Supported for Phase 2 with restrictions:

- Kilo repo `AGENTS.md` appendix；
- Kilo `.kilo/rules/*.md` with `kilo.jsonc` instructions；
- Codex repo `AGENTS.md` appendix after Codex action-level preflight。

Risky / not first:

- Codex/Kilo implicit skills：metadata 可见，但 full skill loading 依赖模型选择；
- explicit skills：可作为后续候选，但 first MVP 不应依赖 on-demand skill tool call；
- harness prompt/context：可诊断，不是 deployable Agent artifact；
- runtime policy：hard control，需要单独 estimand；
- model/reasoning：Agent-selection knob，不作为 artifact tuning 主 surface。

## tuner compatibility recommendation

Primary proposer:

```text
GEPA standalone / optimize_anything
```

Primary artifact path:

```text
GEPA -> one Kilo repo AGENTS.md appendix -> Kilo workspace Agent -> Barcarolle before/after validation
```

Backup real-Agent proposer:

```text
Phoenix Prompt Learning -> Kilo AGENTS.md or .kilo/rules artifact
```

Tuner-native fallback:

```text
DSPy-native coding workflow optimized by dspy.GEPA or another DSPy optimizer,
with Barcarolle as external verifier/evaluator
```

Do not claim DSPy tunes Codex/Kilo unless a real bridge exposes a Codex/Kilo-consumed artifact and verifies injection/action behavior.

## Phase 2 primary path

Recommended first Agent surface:

```text
Kilo workspace Agent + repo AGENTS.md appendix
```

Why:

- Kilo `AGENTS.md` proof-of-injection passed and exited cleanly under no-paid fake endpoint；
- `AGENTS.md` is a deployable project artifact and does not require custom runtime policy；
- one-file artifact keeps attribution clearer than simultaneous rules + skills + policy changes。

Recommended task pool:

- use `mahmoud/boltons` because the Agent-selection demo already has certified workspace tasks and sanitized outcomes；
- build Phase 2 train/dev only from Selection-side or otherwise optimizer-visible tasks；
- keep Holdout/future tasks invisible until the selected artifact hash is frozen；
- if the selected Agent is too saturated, use a predeclared Kilo low-cost/headroom slice rather than changing Holdout after seeing results。

Fallback path:

1. Kilo `.kilo/rules/barcarolle.md` plus `kilo.jsonc` instructions if `AGENTS.md` action-level preflight is weak；
2. Codex repo `AGENTS.md` if a Codex action-level preflight removes the fake-endpoint timeout caveat；
3. DSPy-native fallback if real-Agent artifact injection can be seen but cannot drive action-level behavior.

## leakage controls before Phase 2

- freeze train/dev/Holdout split manifest before optimizer input export；
- exporter must exclude Holdout task IDs, raw logs, raw prompts, raw completions, hidden tests, and hidden verifier text；
- every candidate artifact must include `visible_to_optimizer` and `holdout_derived` fields；
- helper must reject `holdout_derived: true` artifacts by default；
- artifact hash must be frozen before any Holdout run；
- run only baseline and selected tuned artifact on Holdout；
- commit only sanitized summaries, injection records, schemas, tests, and reports。

## exact claim boundary

Supported now:

- Barcarolle can inject repo-local text artifacts into real Codex/Kilo-style workspace Agents.
- Barcarolle can produce sanitized injection records with deterministic hashes.
- Kilo `AGENTS.md` and Kilo project rules are currently the most reliable real-Agent surfaces.
- Barcarolle can observe artifact-driven request-context differences without paid calls.
- GEPA/Phoenix-style tuners are compatible as artifact proposers, not full opaque-Agent optimizers.

Unsupported now:

- tuned Agent improvement；
- action-level behavior change such as actual test command execution；
- full Codex/Kilo black-box Agent tuning；
- model fine-tuning；
- predictive validity；
- cross-repo generalization；
- statistical significance of any tuning effect；
- claim that skills were fully loaded beyond observed metadata unless future smoke proves skill tool use。

## validation and hygiene

Commands run:

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
uv run --project experiments/phase0_headroom pytest experiments/phase0_headroom/tools/test_cli_workspace_adapters.py experiments/phase0_headroom/tools/test_workspace_acut_run.py -q
```

Results:

- `7 passed`
- `30 passed`

Additional final checks:

- `git diff --check`: pass
- `git ls-files experiments/agent_tuning_demo | rg '(\.venv|\.pytest_cache|\.DS_Store|raw|transcript|workspace|secret|prompt|completion)'`: no hits
- `git diff --cached --name-only | rg '(\.venv|\.pytest_cache|\.DS_Store|raw|transcript|workspace|secret)'`: no hits before staging closeout files

## commits

- `02fb4cea` Audit agent tuning feasibility context
- `b912ce7d` Inventory agent tuning surfaces
- `26481fd0` Define agent tuning artifact schemas
- `d8e3bcd1` Verify agent artifact injection smoke paths
- `7cadaec9` Record artifact behavior change smoke
- `8f20a2ad` Study agent tuning optimizer compatibility
