# Agent Selection Demo Execution Proposal 2026-06-12

Status: execution proposal for the next Codex agent session.

Related context:

- `docs/research/ab-demo-proposal-2026-06-11.md`
- `docs/research/presentation-feedback-2026-06-11.md`
- `docs/research/project-state-after-proposal.md`
- `experiments/phase0_headroom/configs/acut_workspace_adapters.yaml`

## Executive Goal

Build a near-term demo showing that Barcarolle can compare real Coding Agents on
one target repository, verify their diffs in clean workspaces, and make a useful
Agent-selection recommendation.

This is no longer a two-cell AB demo and it must not predefine artificial
categories such as `Fast`, `Balanced`, and `Deep`. Those labels may be used only
after results exist. The experiment should start from real candidate Agent
configurations that an engineering team might plausibly choose in production.

The core demo question is:

> For this target repository, which complete Coding Agent setup gives the best
> quality/cost/latency tradeoff, and does that recommendation still look
> reasonable on fresh holdout tasks?

## What This Demo Should Demonstrate

The demo can demonstrate:

- the system can run complete Coding Agents, not just raw models;
- the same repo-specific task set can compare multiple real Agent setups;
- generated diffs can be replayed and checked in clean verifier workspaces;
- the system can report verified solve rate, cost, latency, and failure reasons;
- a recommendation made on selection tasks can be checked on holdout tasks.

The demo must not claim:

- predictive validity has been proven;
- the selected Agent is universally best;
- one model family is generally superior;
- the selector is already optimal;
- results generalize across repositories without more evidence.

Preferred phrasing if results are strong:

> On this repository and candidate set, the benchmark-selected Agent remained a
> reasonable recommendation on independent holdout tasks, while the report made
> the quality/cost/failure tradeoff visible.

## Current Upstream Model Availability

Before execution, rerun the model-list check against `LLM_BASE_URL` because
availability can change.

As of the latest local check on 2026-06-12, the configured upstream
`LLM_BASE_URL` exposed these relevant model IDs:

- `gpt-5.4-mini`
- `gpt-5.4`
- `gpt-5.5`
- `claude-sonnet-4-6`
- `claude-sonnet-4-6-thinking`
- `claude-opus-4-8`
- `claude-haiku-4-5-20251001`

Do not use `gpt-5.3-codex` in this demo plan. It appears on OpenAI's public
pricing page, but the current configured upstream did not expose that exact
model ID in the local `/models` response. Also do not substitute
`gpt-5.1-codex` or `gpt-5.2-codex`; the current presentation strategy removed
the Codex-specialized model branch to keep the candidate set simple.

The active model dimension for this demo is:

- GPT low-cost: `gpt-5.4-mini`
- GPT mainline: `gpt-5.4`
- Claude mainline: `claude-sonnet-4-6`
- optional high-end calibrator: `gpt-5.5` or `claude-opus-4-8`

Provider interface policy:

- use the upstream provider's OpenAI-compatible interface for all scored model
  calls, including Claude-family models;
- use `LLM_BASE_URL` and `LLM_API_KEY` as the canonical endpoint variables;
- do not mix OpenAI-compatible and Anthropic-compatible interfaces inside the
  first scored matrix unless the user explicitly approves that exception.

Pricing reference as of 2026-06-12:

- OpenAI standard pricing lists `gpt-5.4` at `$2.50 / $0.25 / $15.00` per 1M
  input / cached input / output tokens for short context, and `gpt-5.4-mini` at
  `$0.75 / $0.075 / $4.50`.
- OpenAI standard pricing lists `gpt-5.5` at `$5.00 / $0.50 / $30.00` for short
  context.
- Anthropic standard pricing lists Claude Sonnet 4.6 at `$3.00 / $15.00` per
  1M input/output tokens, with cache-write and cache-hit pricing listed
  separately. Batch pricing is discounted to `$1.50 / $7.50` per 1M
  input/output tokens if the Batch API is used. The docs also note a 1.1x
  multiplier for US-only inference geography on Sonnet 4.6 and later.

Record actual observed usage and gateway-billed cost if available. If billed
cost is unavailable, use observed-token estimates and label them clearly.

Sources checked:

- OpenAI Codex non-interactive mode: <https://developers.openai.com/codex/noninteractive>
- OpenAI pricing: <https://developers.openai.com/api/docs/pricing>
- Kilo OpenAI-compatible providers: <https://kilo.ai/docs/ai-providers/openai-compatible>
- Kilo custom models: <https://kilo.ai/docs/code-with-ai/agents/custom-models>
- Claude Code CLI reference: <https://code.claude.com/docs/en/cli-reference>
- Claude Code environment variables: <https://code.claude.com/docs/en/env-vars>
- Claude pricing: <https://platform.claude.com/docs/en/about-claude/pricing>
- SWE-Bench++ paper: <https://arxiv.org/abs/2512.17419>
- SWE-Bench++ public repository: <https://github.com/TuringEnterprises/SWE-Bench-plus-plus>
- SWE-Bench++ public dataset: <https://huggingface.co/datasets/TuringEnterprises/SWE-Bench-plus-plus>

## Target Repository And Task Source

Default target repository:

```text
mahmoud/boltons
```

Use `boltons` because it is a real public Python utility library, has stable
local test commands in the existing Barcarolle artifacts, has already been used
in paid workspace-agent runs, and has the best current mix of prior paid-run
context and near-ready task supply among the retained single-repo demo
candidates. Existing two-repo expansion records show that `boltons` has 60
existing task-supply rows and 55 later certification attempts, including 15
locally certified tasks and 24 near-certified tasks. That is not enough to claim
the full preferred demo immediately, but it is the best current starting point
for a single-target-repo execution path.

Fallback target repository:

```text
python-attrs/attrs
```

Use `attrs` only if `boltons` fails the repository gate. `attrs` has broad
history and many near-certified candidates, but prior experiments showed more
reference-pass/flakiness repair work before enough tasks become scoreable.

Do not use the public SWE-Bench++ dataset as the main target-repo source for
this demo. Its public Hugging Face split has 500 instances across many
repositories, and the largest single repository slice found in the current
public split is `kubernetes/kubernetes` with 10 tasks. That is useful for
external comparison, but it is too thin for this single-target-repo demo.

### Task Source Decision

The fixed task source for this demo is:

```text
Barcarolle repo-history task generator, configured in SWE-Bench++ style.
```

Concretely, the generator should mine the target repository's merged commits or
PRs, require implementation changes plus changed tests, construct a
solver-visible statement from non-leaky public context, derive a hidden verifier
from changed tests plus pass-to-pass guards, and certify the task by replaying
base, no-op, and reference-patch states in clean workspaces.

Use these existing assets as the starting point:

- `experiments/phase1_compiler/tools/phase1_task_supply_v2_fresh_certification.py`
- `experiments/phase1_compiler/tools/phase1_two_repo_certified_supply_expansion.py`
- `experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_existing_inventory.json`
- `experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_certification_attempts.json`
- `experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_candidate_funnel.json`

The executing agent may wrap or simplify these tools, but the source rule should
stay fixed: repo-history tasks with changed-test oracle extraction and local
certification. Do not mix in synthetic tasks, user-written one-off tasks, or
post-result handpicked tasks for the scored run.

### SWE-Bench++ Research Finding

SWE-Bench++ is a strong methodological reference, not a drop-in public task
generator for this demo.

The paper describes an automated pipeline with programmatic sourcing,
environment synthesis, test oracle extraction, and quality assurance. The public
GitHub repository currently exposes an evaluation harness, Docker/test-spec/log
parser code, and instructions for evaluating predictions against the public
dataset. It does not appear to expose the full sourcing and generation pipeline
needed to run SWE-Bench++ generation on an arbitrary target repository.

The public Hugging Face dataset is still useful as:

- an external schema and metadata reference;
- a possible future task-source adapter;
- a comparison point for environment/test-spec design;
- a reminder that generator outputs must still be selected for target-repo
  predictive usefulness.

Do not write that this demo uses the "SWE-Bench++ public task generator" unless
the executing agent finds a public generator entrypoint and records the command.

## Candidate Agent Matrix

The first demo should mainly vary `harness/runtime` and `model`. Freeze budget,
tool policy, test policy, network policy, workspace setup, and retry policy
unless a smoke test proves that a candidate cannot run under the same knobs.

### Minimal Candidate Set

Use this if time and integration budget are tight:

| ID | Reviewer-facing name | Harness/runtime | Model | Why include it |
| --- | --- | --- | --- | --- |
| A | Codex + GPT mainline | Codex CLI workspace adapter | `gpt-5.4` | Existing Codex path; shows OpenAI's coding agent runtime with the main GPT candidate. |
| B | Kilo + GPT mainline | Kilo Code CLI workspace adapter | `gpt-5.4` | Existing Kilo path; holds model fixed against A to expose harness/runtime effects. |
| C | Kilo + GPT low-cost | Kilo Code CLI workspace adapter | `gpt-5.4-mini` | Existing Kilo path; tests whether a cheaper model is good enough for this repo. |
| D | Kilo + Claude Sonnet | Kilo Code CLI workspace adapter | `claude-sonnet-4-6` | Keeps the endpoint and harness path controllable while adding a non-GPT model family. |

If `Kilo + Claude Sonnet` cannot pass the smoke tests, replace D with:

| ID | Reviewer-facing name | Harness/runtime | Model | Why include it |
| --- | --- | --- | --- | --- |
| D-alt | Codex + GPT low-cost | Codex CLI workspace adapter | `gpt-5.4-mini` | Completes a small `Codex/Kilo x gpt-5.4/gpt-5.4-mini` matrix with existing adapters. |

`Claude Code + Sonnet` is not part of the minimal scored plan. This is not
because Claude models are unavailable: the upstream provider exposes Claude
models and supports compatible access. The reason is interface consistency. The
first scored matrix should use the OpenAI-compatible `LLM_BASE_URL` /
`LLM_API_KEY` path for every model family, so the preferred Claude candidate is
`Kilo + Claude Sonnet`. Keep Claude Code as an optional integration spike only;
it can enter the scored set only if the user approves mixing interfaces or the
executing agent proves Claude Code can be routed through the same endpoint
policy without weakening artifact capture.

### Stronger Candidate Set

Use this only after the minimal set passes smoke tests:

| ID | Reviewer-facing name | Harness/runtime | Model |
| --- | --- | --- | --- |
| A | Codex + GPT mainline | Codex CLI | `gpt-5.4` |
| B | Kilo + GPT mainline | Kilo Code CLI | `gpt-5.4` |
| C | Codex + GPT low-cost | Codex CLI | `gpt-5.4-mini` |
| D | Kilo + GPT low-cost | Kilo Code CLI | `gpt-5.4-mini` |
| E | Kilo + Claude Sonnet | Kilo Code CLI | `claude-sonnet-4-6` |
| F | High-end calibrator | Codex or Kilo, choose the lower-risk adapter | `gpt-5.5` |
| G | Optional external harness | Claude Code CLI, only with explicit interface-policy approval | `claude-sonnet-4-6` |

Do not add more candidates until this set is interpretable. Additional budget is
usually better spent on more tasks, repeatability checks, or failure analysis
than on more Agent names.

## Required Smoke Tests

Before any paid matrix run, run a small smoke suite and write a short smoke
report.

Required checks:

1. `LLM_BASE_URL` and `LLM_API_KEY` are present after sourcing `~/.zshrc`.
2. `/models` includes every planned model ID.
3. Codex adapter can run `gpt-5.4` and, if selected, `gpt-5.4-mini`.
4. Kilo adapter can run `gpt-5.4`, `gpt-5.4-mini`, and
   `claude-sonnet-4-6` through the configured OpenAI-compatible provider.
5. Claude Code adapter is optional and should not block the main demo. It can
   run `claude-sonnet-4-6` as a scored candidate only with explicit approval to
   use a secondary Anthropic-compatible interface, or if the implementation can
   route it through the same endpoint policy while preserving tool restrictions,
   secret isolation, and artifact capture.
6. Each candidate can modify a disposable workspace, produce a Git diff, and
   terminate with a machine-readable or reliably parseable status.
7. No Agent shell can print or access `LLM_API_KEY` or other provider secrets.
8. Raw prompts, completions, transcripts, and workspaces stay under ignored
   paths.

If `Kilo + Claude Sonnet` cannot satisfy these checks quickly, drop it from the
minimal run and use `D-alt`. Do not block the minimal run on Claude Code.

## Frozen Experimental Conditions

Freeze these before looking at score results:

- target repository and commit SHA;
- task text and solver-visible context;
- selected task IDs and split assignment;
- visible test command given to Agents;
- hidden verifier checks;
- workspace OS image, dependency setup, and cache policy;
- wall-clock timeout;
- external retry policy: zero evaluator-level retries;
- solver-shell external network access: off unless the target repo setup
  requires an explicitly recorded exception;
- model-endpoint network access: allowed only for the Agent harness or adapter
  process, with secrets scrubbed from the Agent-visible shell environment;
- MCP/browser/external docs: disabled for the first demo;
- writable path policy;
- final diff extraction and verifier replay procedure;
- cost accounting method;
- recommendation rule.

Recommended first-run policy:

- one invocation per Agent per task;
- no evaluator repair loop after a failed hidden verifier;
- Agent may self-repair only inside its own run if its harness naturally does so;
- same outer timeout for all Agents;
- same visible tests for all Agents;
- no post-result task editing.

## Task Design

Use the target repository and task source fixed above. The first execution step
must run a repository gate for `mahmoud/boltons`; use `python-attrs/attrs` only
if the gate fails and the failure is recorded.

Repository gate:

- verify checkout, dependency installation, and visible test command stability;
- confirm the existing `boltons` artifacts can be loaded and replayed;
- produce at least 30 locally certified tasks before running the main 20+10
  scored demo;
- if fewer than 30 tasks can be certified, run only a smoke/infrastructure demo
  and do not make an Agent-selection recommendation;
- if at least 45 tasks can be certified, prefer the 30+15 split;
- if at least 60 tasks can be certified, prefer the 40+20 split.

Minimum viable task count:

- 20 selection tasks + 10 holdout tasks.

Preferred task count:

- 30 selection tasks + 15 holdout tasks.

Stronger task count:

- 40 selection tasks + 20 holdout tasks.

The previous 30+15 minimum remains a good target, but the current `boltons`
supply may require certification repair before it is reachable. A 20+10 run is
acceptable for the first demo if the report presents it as an execution and
decision demo, not as evidence of durable predictive validity.

Task requirements:

- each task has a clean base commit;
- solver-visible statement does not leak the answer patch;
- hidden verifier material is unavailable to the solver workspace;
- diff replay works in a fresh verifier workspace;
- task has a clear terminal status;
- certification status is recorded.

## Selection And Holdout Protocol

Use plain names in user-facing reports:

- `selection tasks`: the tasks used to choose the recommended Agent;
- `holdout tasks`: fresh tasks used once after the recommendation is locked.

Do not call them `training` and `test` unless a learned selector or tuning loop
is actually trained.

Protocol:

1. Build or choose the certified task pool.
2. Freeze selection/holdout split before running candidate Agents.
3. Run all candidate Agents on selection tasks.
4. Apply the recommendation rule.
5. Lock the recommended Agent and the reported decision.
6. Run all candidate Agents, or at minimum the recommended Agent and nearest
   competitor, on holdout tasks.
7. Report whether holdout agrees, partially agrees, or contradicts the
   selection-task recommendation.

Do not tune the candidates between selection and holdout.

## Recommendation Rule

Use a predeclared multi-view rule rather than a single hidden score.

Primary quality view:

- rank by verified solve rate on selection tasks;
- break ties by fewer policy/verifier replay failures;
- then lower cost per solved task;
- then lower median latency.

Production value view:

- recommend the cheapest Agent whose verified solve rate is within 5 percentage
  points of the top Agent, if such an Agent exists;
- otherwise recommend the top verified solve-rate Agent.

Report both views. If they disagree, present the disagreement as useful
decision evidence, not as a failure.

Do not hide cost or latency to make the quality winner look better.

## Metrics

Required metrics:

- scheduled cells;
- completed cells;
- scoreable-cell rate;
- verified solve rate;
- cost per task;
- cost per solved task;
- median and p90 latency;
- verifier replay success rate;
- hidden-test leakage or policy violations;
- failure category counts.

Failure categories:

- verified pass;
- hidden verifier failure;
- visible test failure;
- build/typecheck failure;
- patch did not apply;
- no meaningful change;
- exceeded budget or timeout;
- edited prohibited paths;
- edited tests when prohibited;
- unsafe or overbroad change;
- flaky or infrastructure failure.

Recommended charts for final report:

1. quality vs cost scatter: x = cost per solved task, y = verified solve rate;
2. quality vs latency scatter: x = median latency, y = verified solve rate;
3. failure-category stacked bars per Agent;
4. selection vs holdout rank table.

## Deliverables

The implementation should deliver:

- a clean demo directory chosen by the executing agent;
- config files for target repo, task split, Agent candidates, and run policy;
- smoke-test report;
- selection-run manifest;
- holdout-run manifest;
- sanitized score tables;
- cost/usage summary;
- failure taxonomy table;
- final Chinese demo report with concise English appendix if useful;
- a short closeout note with blockers, caveats, and recommended next run.

Suggested demo report title:

```text
目标仓库 Coding Agent 选型 Demo 报告
```

Suggested user-facing section order:

1. We compared real Coding Agents on one target repo.
2. Each Agent solved the same selection tasks under the same rules.
3. We replayed every diff in a clean verifier workspace.
4. The report compares quality, cost, latency, and failure reasons.
5. We checked the recommendation on fresh holdout tasks.
6. What the result means and what it does not prove.

## Implementation Guidance For Codex Agent

Use existing Barcarolle assets when they reduce risk:

- `experiments/phase0_headroom/tools/codex_workspace_adapter.py`
- `experiments/phase0_headroom/tools/kilo_workspace_adapter.py`
- workspace creation and diff capture logic;
- verifier replay and hidden-oracle injection patterns;
- score table and usage accounting logic;
- existing sanitized task/result schemas.

But do not force old research terminology into the new demo. Avoid demo-facing
terms such as:

- `phase`;
- `ACUT`;
- `release`;
- `candidate policy`;
- `weighted target profile`;
- `proposal evidence package`;
- runbook names.

Prefer demo-facing names:

- `target_repo`;
- `task_pool`;
- `selection_tasks`;
- `holdout_tasks`;
- `agent`;
- `agent_run`;
- `verifier`;
- `feedback_report`.

The executing Codex agent may choose whether to create a new clean demo layer or
wrap existing experiment code. The strict requirement is not a specific
directory shape; it is a runnable, readable, low-abstraction demo.

## Stop Conditions

Stop and write a blocker report if:

- endpoint compliance cannot be proven for a planned paid Agent run;
- a candidate harness cannot prevent secret exposure to Agent shell commands;
- hidden verifier material is visible to the solver workspace;
- scoreable-cell rate in smoke tests is below 90%;
- `Kilo + Claude Sonnet` cannot pass smoke tests and no clean replacement
  candidate is available;
- task certification is too weak to support a selection claim;
- raw transcripts or workspaces would need to be committed to explain the result.

## Acceptance Criteria

The demo is acceptable if:

- at least four candidate Agents are smoke-tested, using `D-alt` if needed;
- at least the minimal candidate set is run on selection tasks;
- holdout is run after the recommendation rule is locked;
- scoreable-cell rate is at least 95% in the main scored run;
- every scored diff is replayed in a clean verifier workspace;
- the final report can be read without understanding Barcarolle's old phase
  terminology;
- the report states what was learned, what was not proven, and what the next
  stronger run should test.

If only three candidates can be smoke-tested, or if the main scored run misses
the scoreable-cell gate because of infrastructure failures, close the run as a
partial/blocker report rather than marking the demo accepted.

## Concise Presentation Story

Use this wording as the story spine:

> We are not benchmarking raw models. We are comparing complete Coding Agents on
> a target repository. Each Agent gets the same tasks and the same rules. We
> replay its code changes in a clean verifier workspace, run private checks, and
> report quality, cost, latency, and failure reasons. The selection tasks produce
> a recommendation; holdout tasks check whether that recommendation remains
> reasonable on fresh work.
