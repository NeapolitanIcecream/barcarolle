# Agent Tuning Tuner Compatibility 2026-06-14

Status: Phase 1 compatibility study for Agent Tuning Demo Phase 2. This is not
an optimizer run.

## Decision

Use real Codex/Kilo-style Agents first, but frame the tuner as an artifact
proposer, not as a full opaque-Agent optimizer.

Recommended Phase 2 primary proposer:

```text
GEPA standalone / optimize_anything -> Kilo AGENTS.md or .kilo/rules artifact
```

Recommended backup proposer:

```text
Phoenix Prompt Learning -> Kilo AGENTS.md or .kilo/rules artifact
```

Recommended tuner-native fallback if real-Agent artifact action cannot be
proven:

```text
DSPy-native coding workflow optimized with dspy.GEPA or another DSPy optimizer,
with Barcarolle as external verifier/evaluator.
```

Do not claim that GEPA, Phoenix, DSPy, Opik, TextGrad, ProTeGi, SKVM, or
SkillOpt tunes the full Codex/Kilo Agent unless Barcarolle exposes the relevant
Agent internals as tunable variables. The honest claim is narrower:

> Barcarolle can optimize deployable Agent context artifacts, such as
> `AGENTS.md`, `SKILL.md`, Kilo rules, or bounded policy snippets, using
> target-repo feedback.

## Compatibility Matrix

| tuner | tunable unit | native framework required | opaque CLI Agent? | Barcarolle scalar feedback | traces/diffs/failure labels | output artifact | inject into Codex/Kilo | Phase 2 role | risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GEPA standalone / `optimize_anything` | arbitrary text artifact | no | yes, if the CLI consumes the artifact | yes | yes, especially as actionable side information | text artifact: `AGENTS.md`, `SKILL.md`, Kilo rule, policy snippet | yes | primary proposer | medium: rollout cost, noisy search, overfit risk |
| Phoenix Prompt Learning | prompt/rule text | SDK/data workflow, not native Agent | as proposer only | yes | yes if converted to examples/feedback columns | prompt/ruleset | yes | backup proposer | medium: prompt-oriented, needs good feedback text |
| DSPy | DSPy module prompts/demos/program params | yes | no direct optimization of opaque CLI internals | yes | partially, through metric/trace adapters | compiled DSPy program or exported prompt | indirect/manual export | tuner-native fallback | medium-high: toy-agent risk and patch tooling work |
| Opik Agent Optimizer | prompts, tools, parameters, workflows | Opik SDK/logging objects | maybe via wrapper, not magical CLI internals | yes | yes if logged to Opik | prompt/tool/workflow config | yes for text artifacts; tool schemas only if Agent consumes them | future proposer candidate | medium: platform/data integration |
| TextGrad | text variables in a computation graph | yes | only if artifact is a TextGrad variable | weak-to-yes via textual loss | yes if summarized into feedback | optimized text variable | yes for skill/rule/prompt text | optional future proposer | medium: less turnkey for long Agent rollouts |
| ProTeGi / APO | prompt text | training examples and LLM API, not Agent-native | as prompt/rule proposer only | yes for selection/ranking | partially via summarized failures | rewritten prompt/rule | yes for prompt/rule artifacts | reference or lightweight proposer | medium: prompt-only and older method |
| SKVM / SkillRT-style systems | skills as compiled/runtime artifacts | yes | not primarily an optimizer for opaque CLIs | not primary | runtime evidence may help | compiled skill/runtime artifact | maybe later | future skill-runtime direction | high: runtime integration and maturity |
| SkillOpt-style systems | one natural-language skill document | rollout/eval framework needed | yes if frozen Agent consumes skills | yes | yes, trajectory-driven | `best_skill.md` / skill doc | yes | strong future skill optimizer; maybe Phase 2B | medium-high: new system and implementation maturity |

## Why GEPA First

GEPA's current docs describe optimizing text artifacts against arbitrary
evaluation metrics, including prompts, code, configs, policies, and agent
architectures. That maps directly to Barcarolle's Phase 2 need: evaluate a
candidate `AGENTS.md` or Kilo rule on target-repo tasks, return a score plus
failure labels/diff summaries, and let the proposer mutate the text artifact.

GEPA is a good fit only if Phase 2 keeps the artifact narrow. The first run
should optimize one file, not a bundle of model, policy, prompt, rules, and
skills at once.

## Why Phoenix Backup

Phoenix Prompt Learning is relevant because it is explicitly prompt/ruleset
oriented and has coding-agent prompt-learning examples. It is less general than
GEPA for arbitrary text artifacts, but simpler to explain as:

```text
Barcarolle failure labels + eval outcomes -> improved coding-agent ruleset
```

Use Phoenix if GEPA integration or cost control is too heavy for the Phase 2
MVP.

## Why DSPy Is Fallback, Not Primary

DSPy optimizers tune DSPy programs. They are excellent if the Agent workflow is
implemented as DSPy modules with tools and a metric, but Codex/Kilo CLI internals
are not DSPy predictors. A DSPy fallback would demonstrate:

> Barcarolle can serve as a target-repo verifier/reward source for a
> tuner-native coding workflow.

It would not demonstrate:

> DSPy tuned Codex/Kilo.

## Compatibility With Phase 1 Smoke Evidence

Package 4 showed no-paid request-capture proof for Codex `AGENTS.md`, Codex
skill metadata, Kilo `AGENTS.md`, Kilo rules, and Kilo skill metadata. Kilo
`AGENTS.md` and Kilo rules also exited cleanly under the fake endpoint.

Package 5 showed artifact-driven request-context behavior change for Codex
`AGENTS.md`, but did not prove action-level command trace or public-test
execution. Therefore the first real-Agent Phase 2 path should be restricted to:

1. one artifact surface;
2. no Holdout-derived optimizer input;
3. action-level preflight before optimizer rollout;
4. before/after validation only after the chosen artifact hash is frozen.

## Sources Checked

- GEPA: https://github.com/gepa-ai/gepa
- GEPA `optimize_anything`: https://gepa-ai.github.io/gepa/blog/2026/02/18/introducing-optimize-anything/
- DSPy GEPA: https://dspy.ai/api/optimizers/GEPA/overview/
- Phoenix coding-agent Prompt Learning: https://arize.com/docs/phoenix/cookbook/prompt-engineering/optimizing-coding-agent-prompts-prompt-learning
- Opik Agent Optimizer: https://www.comet.com/docs/opik/development/optimization-runs/overview
- TextGrad: https://github.com/zou-group/textgrad and https://arxiv.org/abs/2406.07496
- ProTeGi / APO: https://aclanthology.org/2023.emnlp-main.494/
- SKVM: https://github.com/SJTU-IPADS/SkVM and https://arxiv.org/html/2604.03088v2
- SkillOpt: https://github.com/microsoft/SkillOpt and https://microsoft.github.io/SkillOpt/
