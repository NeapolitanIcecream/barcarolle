# ACUT Matrix Notes

Date: 2026-04-28
Operator: codex-cli-worker-acut-matrix
Branch: codex/core-exp-acut-matrix

## Scope

This matrix freezes seven agent configurations under `experiments/core_narrative/configs/acuts/`. The goal is not to predict absolute agent quality. The goal is to create controlled contrasts that can expose ranking reversals between a general benchmark score, a repository-specific benchmark score, and held-out repository work.

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

## Matrix Rationale

| ACUT | Primary contrast | Expected use |
| --- | --- | --- |
| `minimal-context-baseline` | Low context, low reasoning, narrow retrieval | Establish the floor for task statements and immediate local evidence only. |
| `general-benchmark-optimized` | Benchmark-style compact repair | Candidate for strong G_score but weaker repository adaptation. |
| `repo-context-heavy` | Repository map before editing | Candidate for stronger R_score and W_score when conventions matter. |
| `higher-budget-repo-depth` | Same repository bias with more time, commands, tests, and reasoning | Tests whether budget improves real repository work beyond model identity. |
| `lower-budget-fast-path` | Speed-optimized patching | Tests whether low latency causes repository-specific failures. |
| `retrieval-sparse-symbolic` | Symbol and error-text retrieval instead of broad preload | Tests whether precise retrieval can match broader context at lower cost. |
| `retrieval-history-augmented` | Adds bounded pre-cutoff git history | Tests whether development history improves convention matching without leaking private task answers. |

The matrix intentionally varies one or two major factors at a time, but it is not a perfect factorial design. The main planned comparisons are:

1. `general-benchmark-optimized` versus `repo-context-heavy`: expected to be the clearest ranking-reversal probe.
2. `minimal-context-baseline` versus `lower-budget-fast-path`: separates low context from low budget.
3. `repo-context-heavy` versus `higher-budget-repo-depth`: estimates whether extra budget adds value after repository context is already available.
4. `retrieval-sparse-symbolic` versus `repo-context-heavy`: compares targeted retrieval with broad repository mapping.
5. `retrieval-history-augmented` versus `retrieval-sparse-symbolic`: isolates whether bounded history improves repository-specific decisions.

## Expected Contrasts

The likely ranking-reversal pattern is:

- `general-benchmark-optimized` may place well on a short, self-contained general benchmark because it favors quick localization, compact patches, and direct verification.
- `repo-context-heavy` and `higher-budget-repo-depth` may place better on repository-specific tasks where local architecture, project conventions, test style, or cross-module behavior matters.
- `retrieval-history-augmented` may improve tasks that mirror historical maintenance patterns, but it carries a higher leakage risk if task splits and history cutoffs are not enforced.
- `retrieval-sparse-symbolic` may perform well on tasks with strong error messages or named symbols and worse on tasks requiring architectural judgment.
- `lower-budget-fast-path` should clarify how much quality loss comes from budget pressure rather than model capability.

## Reproducibility Risks

- Model aliases can drift. Before execution, the runner should resolve each `provider` and `model` to a provider snapshot or record the provider model version returned at run time.
- The runner and schema are still pending. The manifests name `codex-cli-acut-adapter-v0` and `core-narrative-runner-v0` as the intended harness basis, but the exact script interface may be finalized by the schema/tooling worker.
- The target repository is still pending. Retrieval budgets and test command limits may need runner-level normalization if the selected repository is much larger or slower than expected.
- Git history retrieval must respect the benchmark split. The `retrieval-history-augmented` and `higher-budget-repo-depth` manifests require the runner to hide post-cutoff history when those commits could reveal held-out answers.
- All network policies are denied for reproducibility. If the selected repository cannot test without package downloads, dependencies should be prepared outside the ACUT run and recorded as workspace provenance.
- Policy digests are operator-authored summaries, not public leaderboard claims. If exact prompts are later expanded, the runner should attach a cryptographic hash of the final prompt text without changing the frozen ACUT intent.
- Budget limits are part of the treatment. Runners should record overruns and timeouts instead of silently extending limits.
- Private verifier artifacts, reference patches, and other ACUT outputs must remain inaccessible to every ACUT workspace.

## Validation Notes

The Wave 0 schema worker's ACUT schema was inspected at `/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/schemas/acut.schema.json` while it was present. During final self-check that file had been deleted in the schema worker's separate worktree, and no schema validation CLI was available locally. The normalized manifests are aligned to the inspected contract by field name, scalar type, enum value, and `additionalProperties: false` top-level shape.

Schema-side validation is expected to be a runner/tooling concern once a validator is available again. The local self-check for this revision parses every ACUT YAML manifest, checks the canonical top-level keys and expected scalar/container types, verifies score placeholders are only under `metadata.score_fields`, verifies no public benchmark score is claimed, and runs `git diff --check`.

## Runner Expectations

Later runners should reject a manifest if any required field is missing: provider, model, prompt policy digest, tool permissions, retrieval/context strategy, runtime budget, network policy, execution mode, adapter or harness basis, frozen date-time, and operator.

For scoring, ACUT manifests should remain configuration inputs only. Scores belong in run result artifacts or summary reports, not in these frozen manifests.
