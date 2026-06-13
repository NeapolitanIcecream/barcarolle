# Agent Selection Top-2 Repeatability Plan 2026-06-13

Status: execution plan for the next Codex agent session.

Primary inputs:

- `experiments/agent_selection_demo/reports/post_demo_diagnostics_zh.md`
- `experiments/agent_selection_demo/reports/target_repo_coding_agent_selection_demo_report_zh.md`
- `experiments/agent_selection_demo/results/frozen_split.json`
- `experiments/agent_selection_demo/results/holdout_score_table.csv`
- `experiments/agent_selection_demo/results/holdout_check.json`

## Goal

Run a narrow repeatability check for the two Agents involved in the
selection/holdout contradiction:

- `Codex + GPT mainline`
- `Kilo + GPT mainline`

Use the same 10 `mahmoud/boltons` holdout tasks from the first demo. The goal is
to learn whether Kilo's holdout lead is stable enough to discuss, or whether the
observed reversal is likely dominated by stochastic single-run noise.

This is a repeatability check, not a new model benchmark and not a new
predictive-validity experiment.

## Why This Comes Next

The post-demo diagnostics found:

- selection quality was tied: Codex GPT mainline `15/20`, Kilo GPT mainline
  `15/20`;
- the original Codex recommendation depended on a fragile cost tie-breaker;
- Kilo GPT mainline led holdout `9/10` to Codex GPT mainline `5/10`;
- the holdout lead concentrated on later `canonical_history` tasks;
- current artifacts cannot distinguish stochasticity from a stable
  harness/repository behavior difference.

The cheapest useful next answer is therefore a top-2 repeat on the same holdout
tasks.

## Scope

Run exactly these scored candidates:

| Agent | Harness | Model |
| --- | --- | --- |
| Codex + GPT mainline | codex | `gpt-5.4` |
| Kilo + GPT mainline | kilo | `gpt-5.4` |

Primary task set:

- the same 10 holdout tasks recorded in
  `experiments/agent_selection_demo/results/frozen_split.json`.

Optional task set:

- the same 20 selection tasks, only if the holdout repeat is clean and the user
  or executing agent decides the added paid cost is justified.

Do not add:

- more Agents;
- more models;
- second repository;
- prompt/tool tuning;
- learned selector work;
- rolling-origin paid validation.

## Frozen Conditions

Keep unchanged from the original demo:

- task text;
- solver-visible context;
- visible test command;
- hidden verifier;
- verifier replay procedure;
- endpoint policy;
- timeout and external retry policy;
- workspace setup;
- writable path policy;
- cost labeling policy.

Do not tune either Agent between original run and repeat. The point is to
measure repeatability, not to improve either candidate.

## Gates Before Paid Runs

Before paid repeat runs:

1. Confirm `LLM_BASE_URL` and `LLM_API_KEY` are present after sourcing
   `~/.zshrc`.
2. Confirm `/models` still exposes `gpt-5.4`.
3. Run or reuse a minimal smoke/gate check for the existing Codex and Kilo
   workspace adapters.
4. Confirm solver-visible shells cannot read provider secrets.
5. Confirm raw prompts, completions, transcripts, solver workspaces, verifier
   workspaces, and cloned raw repositories remain under ignored paths.

Stop before paid runs if any gate fails.

## Execution Design

Minimum run:

- 2 Agents x 10 holdout tasks = 20 paid cells.

Recommended artifact names may vary, but outputs should include:

- repeat score table;
- repeat verifier results;
- repeat cost/usage ledger;
- task-level stability table comparing original holdout and repeat;
- Chinese repeatability report.

Recommended report path:

```text
experiments/agent_selection_demo/reports/top2_repeatability_check_zh.md
```

## Analysis Questions

Answer these directly:

1. Does Kilo GPT mainline still lead Codex GPT mainline on the same holdout
   tasks?
2. Which task outcomes changed between original holdout and repeat?
3. Are the same Codex failures repeated, especially on:
   - `boltons__hist__022`
   - `boltons__hist__023`
   - `boltons__hist__027`
   - `boltons__hist__028`
4. Does Kilo remain strong on later `canonical_history` tasks?
5. Are any repeated failures infrastructure, timeout, policy, or verifier
   replay issues rather than model/harness task failures?
6. Does the repeat change the presentation story?

## Interpretation Rules

If Kilo still clearly leads:

- Present the result as evidence that the holdout contradiction is less likely
  to be pure single-run noise.
- Still do not claim Kilo is generally better, or that predictive validity is
  proven.

If Codex catches up or rankings flip:

- Present the result as evidence that single-run Agent selection is noisy.
- The next planning focus should become repeated evaluation and uncertainty,
  not second-repo expansion.

If both Agents perform poorly or scoreability drops:

- Treat the repeat as an infrastructure or task stability blocker.
- Do not use it to make an Agent ranking claim.

## Cost Policy

This repeat is mainly about pass/fail stability. Cost repair is useful but not a
hard prerequisite.

However:

- do not use conservative Kilo cost estimates to choose a production-value
  winner;
- label Kilo costs as estimated unless normalized usage becomes available;
- if usage coverage remains asymmetric, report cost as inconclusive.

## Acceptance Criteria

The repeatability check is accepted if:

- all 20 planned holdout repeat cells complete;
- scoreable-cell rate is at least `95%`;
- every scored diff is replayed in a clean verifier workspace;
- the report includes task-level original-vs-repeat stability;
- the report states whether the original holdout contradiction looks stable,
  noisy, or inconclusive;
- no broad model-family, cross-repository, or predictive-validity claim is made.

## Stop Conditions

Stop and write a blocker report if:

- endpoint compliance cannot be proven;
- `gpt-5.4` is not available from the configured upstream;
- secret isolation fails;
- hidden verifier material is visible to the solver workspace;
- raw transcripts or workspaces would need to be committed;
- scoreable-cell rate in smoke/gate checks is below `90%`;
- repeated runs cannot be explained without reading raw transcripts.

## Closeout Requirements

Closeout should state:

1. exact Agent matrix;
2. exact task set;
3. number of repeat cells;
4. original holdout result versus repeat result;
5. task-level stability summary;
6. whether Kilo's holdout lead appears stable;
7. whether stochasticity remains a plausible explanation;
8. cost/usage coverage caveats;
9. recommended next step: second-repo gate, more repeats, cost repair, or
   rolling-origin design prep.

