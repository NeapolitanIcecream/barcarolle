# Agent Selection Demo Strict Completion Runbook 2026-06-13

Status: mandatory execution runbook for a long-running autonomous Codex agent.

This runbook supersedes the looser completion plan when the goal is to finish
all remaining demo work, not just produce a final written package.

Primary context:

- `AGENTS.md`
- `PROCESS.md`
- `docs/research/agent-selection-demo-execution-proposal-2026-06-12.md`
- `docs/research/agent-selection-demo-alignment-note-2026-06-13.md`
- `docs/research/agent-selection-demo-completion-plan-2026-06-13.md`
- `experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md`
- `experiments/agent_selection_demo/reports/demo_completion_closeout_zh.md`

## Mission

Complete the Agent selection demo end to end. "Autonomous" means solving
encountered engineering and analysis problems within the boundaries below. It
does not mean choosing the shortest branch and stopping after a document-only
deliverable.

The final state should let a reader or future engineer see:

- what the `mahmoud/boltons` demo proved;
- whether the Kilo repeat path is repaired, or exactly why it remains blocked;
- whether a second repository is ready for a future paid matrix;
- how sanitized evaluation results become Agent tuning feedback;
- which code paths and reports are the maintained demo entry points.

## Non-negotiable Completion Criteria

Do not mark the run complete until all mandatory work packages below are either
completed or have a specific blocker report with attempted fixes and evidence.

Mandatory work packages:

1. State audit and gap list.
2. Demo tooling and artifact hygiene audit.
3. Kilo adapter timeout and usage root-cause work.
4. Frozen top-2 repeat completion attempt after Kilo gates pass, or a narrow
   blocker proving the repeat is still not executable.
5. No-paid second-repo gate.
6. Runnable Agent tuning feedback summary generator.
7. Final package and closeout update.

Document-only completion is not acceptable unless every engineering or
experiment package is blocked by a documented external condition.

## Paid-call Boundary

Default first step is no paid calls. Fix and test locally wherever possible.

Approved paid calls inside this runbook:

- up to 4 Kilo adapter smoke/debug cells;
- one frozen top-2 repeat attempt after Kilo gates pass:
  - `Codex + GPT mainline`
  - `Kilo + GPT mainline`
  - the same 10 frozen `mahmoud/boltons` holdout tasks
  - at most 20 scored cells.

Do not run second-repo paid cells. Do not expand the Agent matrix. Do not tune
prompts, tools, model settings, task text, or hidden verifiers to improve a
candidate after seeing results.

All paid LLM or Agent calls must use `LLM_BASE_URL` and `LLM_API_KEY`, with the
endpoint and secret-isolation gates recorded before the call.

## Blocker Standard

An item can be marked blocked only after the agent has:

- identified the exact command, code path, artifact, or external dependency that
  prevents progress;
- made at least one concrete local fix attempt when the issue is in repo code;
- added or updated a focused test if the code path is testable without paid
  calls;
- recorded why further progress would require exceeding the paid-call boundary,
  violating artifact hygiene, changing the experiment contract, or waiting for
  an external tool/provider.

If a blocker affects only one work package, continue the remaining packages.

## Work Package 1: State Audit And Gap List

Read the primary context and inspect current demo code/results.

Produce or update:

```text
experiments/agent_selection_demo/reports/demo_remaining_gap_audit_zh.md
```

Required content:

- current branch and latest relevant commits;
- completed demo artifacts;
- remaining gaps mapped to the mandatory work packages;
- exact commands or files the agent will use for Kilo diagnosis, second-repo
  gate, and feedback generator.

Acceptance:

- gap list explicitly says that the final package already exists but is not the
  end of this runbook;
- no paid calls are made in this package.

Commit after this package.

## Work Package 2: Demo Tooling And Artifact Hygiene Audit

Audit the current demo tooling under:

```text
experiments/agent_selection_demo/
experiments/phase0_headroom/tools/
experiments/phase1_compiler/tools/
```

Focus on:

- where Kilo and Codex adapters are invoked;
- how timeouts are applied and recorded;
- whether child processes are killed cleanly;
- how stdout/stderr are drained;
- where usage/cost metadata is parsed and normalized;
- whether score tables preserve enough metadata to debug without raw
  transcripts;
- whether any committed file violates artifact hygiene.

Patch clear bugs and add focused tests. If no bug is found, produce an audit
section explaining why.

Acceptance:

- scoped tests pass;
- `git diff --check` passes;
- committed files do not include raw prompts, raw completions, raw transcripts,
  solver/verifier workspaces, secrets, `.pyc`, or cache files;
- cost fields clearly distinguish observed usage, estimated usage, missing
  usage, and billed cost if available.

Commit after this package.

## Work Package 3: Kilo Timeout And Usage Root-cause Work

This package is mandatory. Do not skip it because the first demo package is
already present.

Investigate the two 900-second Kilo timeouts in the frozen top-2 repeat path
and the missing Kilo usage coverage.

Use sanitized artifacts first:

- `experiments/agent_selection_demo/reports/top2_repeatability_check_zh.md`
- `experiments/agent_selection_demo/results/top2_repeatability_check.json`
- `experiments/agent_selection_demo/results/top2_repeat_cost_ledger.jsonl`
- `experiments/agent_selection_demo/results/top2_repeat_score_table.csv`
- `experiments/agent_selection_demo/results/top2_repeat_submissions.jsonl`
- Kilo adapter code and tests.

If sanitized artifacts are insufficient, the agent may inspect ignored local
raw logs/workspaces only for diagnosis. Do not commit raw content. Summarize
only sanitized findings.

Required output:

```text
experiments/agent_selection_demo/reports/kilo_timeout_usage_root_cause_zh.md
```

Required analysis:

- timeout path: model did not finish, CLI hung, process management bug, stream
  draining issue, workspace/test hang, or unknown;
- whether timeout status is recorded correctly and scoreable logic treats it as
  infrastructure rather than quality;
- why usage is absent for Kilo and whether normalized usage can be emitted;
- local patch or mitigation attempted;
- tests added or updated;
- whether Kilo is safe to smoke test.

Acceptance:

- a root-cause hypothesis is documented;
- if repo code was likely involved, a fix or mitigation is implemented;
- if usage still cannot be observed, reports label Kilo cost as
  `cost-inconclusive` and explain the missing source;
- a Kilo smoke/gate decision is recorded.

Commit after this package.

## Work Package 4: Kilo Smoke/Gate And Frozen Top-2 Repeat Attempt

Run this package unless Work Package 3 proves that a paid Kilo run would violate
endpoint policy, secret isolation, artifact hygiene, or the paid boundary.

Preflight gates:

- `LLM_BASE_URL` and `LLM_API_KEY` are present after sourcing `~/.zshrc`;
- `/models` includes `gpt-5.4`;
- Codex and Kilo adapter tests pass;
- solver-visible shell cannot access provider secrets;
- raw artifacts remain under ignored paths;
- the Kilo timeout/usage diagnosis says a smoke run is safe.

First run up to 4 Kilo smoke/debug cells if needed. If Kilo still times out or
cannot produce a scoreable cell, stop paid work and write a blocker update.

If Kilo gate passes, run one frozen top-2 holdout repeat:

- same 10 `mahmoud/boltons` holdout tasks from `frozen_split.json`;
- `Codex + GPT mainline` and `Kilo + GPT mainline`;
- same task text, visible context, hidden verifier, endpoint policy, timeout,
  workspace, writable path policy, and no evaluator repair loop;
- no candidate tuning.

Required output:

```text
experiments/agent_selection_demo/reports/top2_repeat_completion_zh.md
```

Acceptance if repeat runs:

- all planned cells or all reachable cells are accounted for;
- scoreable rate is reported;
- every scored diff is replayed in a clean verifier workspace;
- task-level table compares original holdout, previous repeat, and new repeat;
- conclusion is one of:
  - stable holdout contradiction;
  - noisy/inconclusive;
  - infrastructure blocker still unresolved.

Do not claim a global Agent ranking.

Commit after this package.

## Work Package 5: No-paid Second-repo Gate

This package is mandatory and must not be skipped because Kilo work is hard.

Run a no-paid gate for a second target repository. Default candidate:

```text
python-attrs/attrs
```

The agent may choose a cleaner candidate only if it records the reason and does
not run paid Agent cells.

Gate requirements:

- repository checkout/setup can run locally;
- visible tests or a stable subset are identified;
- task generator/certification assets can produce or locate candidate tasks;
- at least 30 locally certified tasks are available, or the report explains why
  not;
- hidden verifier replay path is feasible;
- expected matrix cost is estimated from existing `boltons` costs and planned
  candidate count;
- go/no-go recommendation is clear.

Required output:

```text
experiments/agent_selection_demo/reports/second_repo_gate_zh.md
```

Acceptance:

- no paid second-repo cells are run;
- report states whether a future paid second-repo matrix is ready;
- if not ready, it lists the minimum repair work.

Commit after this package.

## Work Package 6: Runnable Agent Tuning Feedback Summary Generator

The existing tuning feedback report is useful but not enough. Implement or
improve a runnable generator that reads sanitized result files and produces a
feedback summary.

Expected behavior:

- input: committed sanitized score tables, metrics, repeatability summary, and
  cost ledgers under `experiments/agent_selection_demo/results/`;
- output: markdown feedback report with per-Agent failure taxonomy, unstable
  tasks, infra blockers, cost/usage coverage, and example tasks for follow-up;
- no raw prompts, completions, transcripts, or workspaces required;
- stable CLI or documented command.

Suggested output path:

```text
experiments/agent_selection_demo/reports/agent_tuning_feedback_summary_zh.md
```

Acceptance:

- generator command is documented in the report or closeout;
- focused tests cover at least one generated summary or core aggregation
  function;
- output does not claim tuning has already improved any Agent.

Commit after this package.

## Work Package 7: Final Package And Closeout Update

Update the final demo package and closeout to reflect every completed mandatory
package.

Required updates:

- final Chinese package cites Kilo root-cause report, top-2 repeat completion or
  blocker, second-repo gate, and runnable feedback generator;
- closeout distinguishes:
  - demo-level claims;
  - Kilo/repeat status;
  - second-repo readiness;
  - feedback-generator status;
  - remaining blockers;
  - paid cells used;
  - tests and hygiene checks.
- `PROCESS.md` links to the strict runbook outputs and records the next
  recommended work.

Acceptance:

- a future session can start from `PROCESS.md` and the final package without
  reading this whole chat;
- stale "recommended next work" from earlier closeouts is updated or clearly
  marked superseded.

Commit after this package.

## Required Validation

Run at minimum:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q
git diff --check
git ls-files experiments/agent_selection_demo | rg '(__pycache__|\\.pyc$|raw|transcript|workspace|\\.DS_Store|\\.pytest_cache|\\.venv)'
```

The artifact scan should have no hits. If broader scans find historical files
with `raw` or `workspace` in names, document that they are pre-existing
sanitized artifacts or tooling paths rather than raw paid-call transcripts or
workspaces.

Run broader tests if code changes touch phase0 adapters, phase1 compiler tools,
or shared workspace execution logic.

## Final Closeout Checklist

The final response from the executing agent must answer:

1. Which mandatory packages were completed?
2. Which packages, if any, remain blocked and what exact evidence supports the
   blocker?
3. How many paid cells were run?
4. Did Kilo timeout/usage improve, and is a top-2 repeat result now available?
5. Is a second repository ready for a paid matrix?
6. What command generates the Agent tuning feedback summary?
7. What files are the canonical demo entry points?
8. Which tests and hygiene checks passed?

Only mark the goal complete when this checklist is answered.
