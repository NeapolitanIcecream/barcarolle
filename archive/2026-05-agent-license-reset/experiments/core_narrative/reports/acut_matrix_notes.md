# ACUT Matrix Notes

Date: 2026-04-28
Operator: codex-cli-worker-acut-matrix
Branch: codex/core-exp-acut-matrix

## Scope

This matrix now freezes a reviewed 2x2 active core plus three deferred exploratory configurations under `experiments/core_narrative/configs/acuts/`. The goal is not to predict absolute agent quality. The goal is to create controlled contrasts that can expose ranking reversals between a general benchmark score, a repository-specific benchmark score, and held-out repository work.

The 2026-04-29 redesign replaces the earlier four active ACUTs because they mixed model tier, reasoning effort, context volume, retrieval strategy, and task budget too heavily to cleanly test the Barcarolle ranking-reversal claim.

All manifests use the canonical ACUT top-level contract. They leave `g_score`, `r_score`, `w_score`, and `public_benchmark_score` as `null` under `metadata.score_fields`. Each manifest references `general_benchmark.yaml#pending` only as the future general benchmark basis.

## Manifest Contract

The schema-facing top level is intentionally small and stable:

- `schema_version: core-narrative.acut.v1`
- `acut_id` and `display_name`
- scalar `provider` and scalar `model`
- `model_parameters` for model-specific knobs such as `reasoning_effort`
- scalar `prompt_policy_digest` plus optional `prompt_policy_reference`
- compact `tool_permissions` with `filesystem`, `network`, and `allowed_tools`
- compact `retrieval_context_strategy` with `strategy_id`, `description`, and `allowed_sources`
- compact `runtime_budget` with `max_wall_seconds`, `max_turns`, `max_tokens`, and `max_cost_usd`
- `network_policy`, `execution_mode`, and scalar `adapter_or_harness_basis`
- date-time `frozen_at`
- string `operator`
- `notes`
- `metadata` for audit-only detail

The richer treatment details from the first revision are preserved in `metadata`: operator branch/worktree, prompt-policy summary, detailed filesystem/git/tool permissions, disallowed sources, initial and maximum context budgets, repository-map mode, search policy, shell/test/verification budgets, execution workspace rules, adapter inputs and outputs, and null score placeholders. Scores remain configuration-adjacent audit fields only; they are not top-level manifest claims.

## 2x2 Core Rationale

| ACUT | Primary contrast | Expected use |
| --- | --- | --- |
| `frontier-generic-swe` | Frontier tier, generic SWE policy | General frontier control cell. |
| `frontier-click-specialist` | Same frontier tier, Click-specialist policy | Tests whether task-agnostic Click specialization improves R/W outcomes without changing model, harness, budget, turn cap, test cap, or retry policy. |
| `cheap-generic-swe` | Cheap tier, generic SWE policy | Cheap model-tier control cell with the same task budget as the other active cells. |
| `cheap-click-specialist` | Same cheap tier, Click-specialist policy | Tests whether Click specialization has leverage even when the model tier is cheaper. |

The active matrix is a 2x2:

- model tier: frontier vs cheap;
- policy: generic SWE vs Click specialist.

All four active cells share the same harness, workspace contract, task budget, turn cap, test cap, retry policy, network policy, and one-primary-attempt policy. Within a model tier, only the generic-vs-Click-specialist policy changes.

The mapping from the previous active matrix is:

- `general-benchmark-optimized` -> `frontier-generic-swe`;
- `repo-context-heavy` + `retrieval-sparse-symbolic` -> `frontier-click-specialist`, with higher reasoning and higher budget removed;
- `lower-budget-fast-path` -> `cheap-generic-swe`, with the fast-path/short-budget confound removed;
- `cheap-click-specialist` is newly added.

`higher-budget-repo-depth`, `retrieval-history-augmented`, and `minimal-context-baseline` remain deferred exploratory ACUTs.

## Expected Contrasts

The likely ranking-reversal pattern is:

- generic SWE cells may remain competitive on short, self-contained general tasks;
- Click-specialist cells may place better on repository-specific tasks where Click conventions, command-line behavior, and testing idioms matter;
- the frontier-vs-cheap contrast estimates how much of the effect is model tier rather than specialization;
- the cheap Click-specialist cell is the most important leverage test for Barcarolle-style context and retrieval.

## Reproducibility Risks

- Model aliases can drift. Before execution, the runner should resolve each `provider` and `model` to a provider snapshot or record the provider model version returned at run time.
- The runner and schema are still pending. The manifests name `codex-cli-acut-adapter-v0` and `core-narrative-runner-v0` as the intended harness basis, but the exact script interface may be finalized by the schema/tooling worker.
- The target repository is still pending. Retrieval budgets and test command limits may need runner-level normalization if the selected repository is much larger or slower than expected.
- Click-specialist context artifacts must be task-agnostic, reproducible, and generated before ACUT execution. They may include a Click repo map, docs map, symbol index, convention playbook, and deterministic retrieval policy, but must not include RBench/RWork gold patches, hidden human hints, post-hoc tuning from ACUT outputs, or undeclared history mining.
- Git history retrieval must respect the benchmark split. The active 2x2 core does not allow undeclared history mining. The deferred `retrieval-history-augmented` and `higher-budget-repo-depth` manifests still require the runner to hide post-cutoff history when those commits could reveal held-out answers.
- All network policies are denied for reproducibility. If the selected repository cannot test without package downloads, dependencies should be prepared outside the ACUT run and recorded as workspace provenance.
- Policy digests are operator-authored summaries, not public leaderboard claims. If exact prompts are later expanded, the runner should attach a cryptographic hash of the final prompt text without changing the frozen ACUT intent.
- Budget limits are no longer part of the active treatment. Runners should enforce the same task budget, turn cap, test cap, and retry policy across all four active ACUTs and record overruns/timeouts instead of silently extending limits.
- Private verifier artifacts, reference patches, and other ACUT outputs must remain inaccessible to every ACUT workspace.

## Validation Notes

The Wave 0 schema worker's ACUT schema was inspected at `/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/schemas/acut.schema.json` while it was present. During final self-check that file had been deleted in the schema worker's separate worktree, and no schema validation CLI was available locally. The normalized manifests are aligned to the inspected contract by field name, scalar type, enum value, and `additionalProperties: false` top-level shape.

Schema-side validation is expected to be a runner/tooling concern once a validator is available again. The local self-check for this revision parses every ACUT YAML manifest, checks the canonical top-level keys and expected scalar/container types, verifies score placeholders are only under `metadata.score_fields`, verifies no public benchmark score is claimed, and runs `git diff --check`.

## Runner Expectations

Later runners should reject a manifest if any required field is missing: provider, model, prompt policy digest, tool permissions, retrieval/context strategy, runtime budget, network policy, execution mode, adapter or harness basis, frozen date-time, and operator.

For scoring, ACUT manifests should remain configuration inputs only. Scores belong in run result artifacts or summary reports, not in these frozen manifests.
