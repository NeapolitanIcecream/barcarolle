# Agent Selection Demo Random-baseline Evidence Runbook 2026-06-14

Status: mandatory long-running runbook for finishing the demo story around a
practical predictive-validity facility and Agent selection evidence.

This runbook supersedes the previous predictive-validity completion pass when
the goal is a demo, not a full research proof. The previous pass correctly built
rolling-origin infrastructure, but it framed the main result against the best
simple baseline and made the story feel heavier than needed. This runbook
re-centers the demo claim:

> Barcarolle is already a demo-level target-repo predictive Agent evaluation
> facility: it can run complete Agents, compare selection and future/holdout
> outcomes, and show that its benchmark selection predicts future pass rate
> substantially better than same-budget random sampling.

The required evidence is not "predictive validity is proven." The required
evidence is:

- the facility runs real Agents end to end;
- rolling-origin/pseudo-future metrics are reproducible;
- the candidate selection has a clear MAE advantage over random same-budget
  baseline;
- the Agent-selection recommendation is reported with caveats, reliability
  gates, and uncertainty instead of a fragile one-shot ranking.

## Reader-facing Claim

Target reader: an internal reviewer who wants to know whether this is a viable
development project or product demo.

Main demo claim:

> We have built a target-repo Agent evaluation facility with predictive-validity
> direction: it can select benchmark tasks, run real Agent configurations, verify
> diffs, and produce Agent-selection evidence whose legitimacy comes from lower
> future-pass-rate prediction error than same-budget random task sampling.

Scope:

- demo-level;
- target-repo;
- complete Agent configurations, not raw models;
- predictive-validity direction, not proof.

Non-scope:

- universal model/harness ranking;
- full predictive-validity proof;
- production-ready cross-repo benchmark marketplace;
- tuned-Agent improvement claim.

## Hard Success Criteria

Do not mark the run complete until all mandatory packages are done or have a
specific blocker report.

Required demo success gates:

1. Timeout policy is doubled and verified:
   - Agent/adapter solving timeout: `900s -> 1800s`.
   - Adapter cleanup grace: `30s -> 60s`.
   - Outer workspace timeout should be `1860s`.
   - Verifier timeout should be reviewed and either doubled from `180s -> 360s`
     or explicitly left unchanged with a reason.
   - LLM endpoint proxy/upstream timeout must be greater than the Agent timeout;
     use `3600s` where configurable.
2. Rolling-origin/random-baseline evidence is reproducible from committed
   sanitized artifacts.
3. Main evidence compares Barcarolle candidate against same-budget random
   baseline:
   - report absolute MAE improvement;
   - report relative MAE improvement;
   - report random baseline seed distribution or percentile if available;
   - success threshold for demo: at least `0.02` absolute MAE improvement or at
     least `10%` relative MAE improvement over random same-budget baseline.
4. Agent-selection evidence is usable:
   - selection/holdout pass-rate matrix is reported;
   - MAE from selection to holdout is reported;
   - non-scoreable/timeout cells are not hidden;
   - if Kilo still times out under doubled timeout, it is treated as a
     reliability-gate failure, not as a model-quality result.
5. Final story is simple:
   - random baseline is the main comparison;
   - best-simple-baseline and catastrophic miss are appendix/limitations;
   - the reader can understand why this supports an investable demo without
     following all previous runbooks.

Document-only completion is not acceptable unless experiment execution is
blocked by a documented external condition after attempted fixes.

## Paid-call Boundary

Default: reuse existing paid/sanitized outcomes and run no paid cells until the
timeout policy and no-paid gates are updated.

Approved paid cells inside this runbook:

- up to 2 doubled-timeout Kilo smoke/debug cells;
- if Kilo smoke/gate passes, up to 20 top-2 repeat cells under doubled timeout:
  - `Codex + GPT mainline`;
  - `Kilo + GPT mainline`;
  - same 10 frozen `mahmoud/boltons` holdout tasks;
- if Kilo remains blocked and the Agent-selection story still needs fresh
  evidence, up to 20 stable-path cells chosen from already scoreable candidate
  paths, with the choice preregistered before execution.

Hard cap: `42` new paid cells.

Do not run second-repo paid cells under this runbook. Do not expand the model
matrix beyond candidates already present in the demo unless the user explicitly
approves.

All paid calls must use `LLM_BASE_URL` plus `LLM_API_KEY`; no fallback endpoint
or subscription auth is allowed.

## Blocker Standard

A package may be blocked only after the agent has:

- identified the exact code path, command, artifact, or external dependency;
- made a concrete local fix attempt if the blocker is in repo code;
- added or updated a focused test if feasible;
- recorded why continuing would exceed the paid boundary, violate artifact
  hygiene, change the experiment contract, or require external provider/tool
  behavior.

If one package is blocked, continue other packages where possible.

## Package 1: Story Reset And Evidence Inventory

Read:

- `AGENTS.md`;
- `PROCESS.md`;
- `experiments/agent_selection_demo/reports/predictive_validity_demo_story_zh.md`;
- `experiments/agent_selection_demo/reports/rolling_origin_eval_zh.md`;
- `experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md`;
- `experiments/agent_selection_demo/reports/demo_completion_closeout_zh.md`;
- `experiments/agent_selection_demo/results/rolling_origin_eval.json`;
- `experiments/agent_selection_demo/results/rolling_origin_eval_slices.csv`;
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md`;
- `experiments/phase1_compiler/results/phase1_proposal_evidence_package_random_baseline_distribution.json`.

Produce:

```text
experiments/agent_selection_demo/reports/demo_random_baseline_story_reset_zh.md
experiments/agent_selection_demo/results/demo_random_baseline_evidence_inventory.json
```

Required content:

- current demo claim in plain Chinese;
- current random baseline MAE, candidate MAE, absolute improvement, relative
  improvement;
- whether random seed distribution/percentile is available;
- which existing artifacts can support the random-baseline story;
- which evidence gaps remain before final story.

Acceptance:

- explicitly says best-simple-baseline is a robustness check, not the main demo
  gate;
- no paid calls are made.

Commit after this package.

## Package 2: Double-timeout Policy Patch

Implement the doubled timeout policy in code/config where the demo actually
reads it.

Required changes:

- update `experiments/agent_selection_demo/config/demo_config.json` candidate
  `timeout_seconds` from `900` to `1800`;
- add or update `run_policy.adapter_cleanup_grace_seconds` to `60`;
- ensure `agent_selection_demo.adapter_config_for()` produces outer timeout
  `1860s`;
- check `codex_workspace_adapter.py` and `kilo_workspace_adapter.py` defaults:
  either update CLI defaults to `1800` or ensure demo command always passes
  explicit `--timeout 1800`;
- verify endpoint proxy upstream timeout is greater than Agent timeout, and add
  a config/code path for `3600s` if currently fixed at `1800s`;
- review verifier timeout. If it is currently `180s`, either double to `360s`
  for this demo or document why verifier timeout is intentionally unchanged.

Required output:

```text
experiments/agent_selection_demo/reports/doubled_timeout_policy_zh.md
```

Acceptance:

- tests cover adapter command timeout and outer cleanup grace;
- no result table is silently rewritten as if old runs used the new timeout;
- reports clearly distinguish old `900s` runs from new `1800s` runs.

Commit after this package.

## Package 3: Random-baseline Evidence Refresh

Regenerate or summarize rolling-origin metrics with random baseline as the main
comparison.

Required output:

```text
experiments/agent_selection_demo/reports/random_baseline_predictive_signal_zh.md
experiments/agent_selection_demo/results/random_baseline_predictive_signal.json
```

Required metrics:

- candidate design name;
- candidate MAE;
- random same-budget baseline MAE;
- absolute MAE improvement;
- relative MAE improvement;
- random seed count or slice count;
- random percentile if available;
- best-simple-baseline result as a secondary robustness note;
- caveat if random baseline is aggregated rather than full seed distribution.

Acceptance:

- main result is framed as "candidate beats random baseline" rather than
  "candidate barely beats best simple baseline";
- success gate is evaluated:
  - pass if candidate improves MAE over random by at least `0.02` absolute or
    `10%` relative;
  - if it fails, write a negative demo result and do not inflate the claim.

Commit after this package.

## Package 4: Doubled-timeout Agent Reliability Gate

Use the doubled-timeout policy to decide whether Kilo can be treated as a
scoreable candidate in repeat evidence.

Preflight:

- source `~/.zshrc` if needed and confirm `LLM_BASE_URL` / `LLM_API_KEY`;
- confirm `/models` includes `gpt-5.4`;
- run adapter tests;
- confirm secret isolation;
- confirm raw paths remain ignored;
- confirm timeout config in generated adapter commands is `1800`.

Execution:

- run no-paid checks first;
- if preflight passes, run up to 2 Kilo smoke/debug paid cells with `1800s`
  timeout;
- if Kilo still exits `124`, produces empty patch/stdout, or has repeated
  provider errors, stop Kilo paid work and label it reliability-gate failed.

Required output:

```text
experiments/agent_selection_demo/reports/doubled_timeout_agent_reliability_gate_zh.md
```

Acceptance:

- records paid cells used;
- records whether Kilo is scoreable under doubled timeout;
- distinguishes provider/adapter timeout from hidden-verifier failure;
- if Kilo fails, the final story treats Kilo as "not currently selectable under
  reliability gate" rather than leaving the demo blocked.

Commit after this package.

## Package 5: Agent-selection Evidence Under The Demo Policy

Produce the clean Agent-selection evidence packet.

If Kilo passes Package 4:

- run or complete top-2 repeat under doubled timeout, up to 20 cells;
- report original selection, original holdout, old repeat, and doubled-timeout
  repeat side by side.

If Kilo fails Package 4:

- do not keep spending paid cells on Kilo;
- report Kilo as a reliability-gate failure;
- if the Agent-selection story still needs fresh evidence, run up to 20
  preregistered stable-path cells using already scoreable candidates and the
  same frozen holdout tasks.

Required output:

```text
experiments/agent_selection_demo/reports/demo_agent_selection_evidence_zh.md
experiments/agent_selection_demo/results/demo_agent_selection_evidence.json
```

Required content:

- selection/holdout pass-rate matrix;
- selection-to-holdout MAE;
- reliability-gated candidate status;
- recommendation rule after cost-inconclusive handling;
- what Agent-selection basis can be given today;
- what remains unresolved.

Acceptance:

- evidence is enough to say the facility can experimentally support Agent
  selection decisions;
- does not claim Kilo or Codex is globally better;
- does not hide randomness or non-scoreable cells.

Commit after this package.

## Package 6: Final Demo Story Rewrite

Rewrite the final story around the simplified demo claim.

Required output:

```text
experiments/agent_selection_demo/reports/demo_predictive_facility_story_zh.md
```

Required structure:

1. What we built: target-repo predictive Agent evaluation facility.
2. Why it matters: Agent selection should predict future repo work.
3. Evidence 1: complete Agent execution and clean verifier replay work.
4. Evidence 2: candidate benchmark selection has substantial MAE advantage over
   random same-budget baseline.
5. Evidence 3: selection/holdout matrix gives experimental Agent-selection
   evidence, with reliability gates.
6. Caveats: best-simple-baseline, Kilo timeout, small data, no full proof.
7. Next step: strengthen signal and run preregistered future validation.

Style requirements:

- Chinese;
- low terminology burden;
- avoid process terms like `phase`, `M1-M6`, `ACUT`, `release`;
- do not center best-simple-baseline or Kilo timeout in the main narrative;
- explain MAE in one sentence.

Acceptance:

- reader can understand the demo claim in under two minutes;
- main evidence includes random baseline improvement and Agent-selection matrix;
- limitations are clear but not allowed to swallow the demo claim.

Commit after this package.

## Package 7: Closeout And Process Update

Update:

- `PROCESS.md`;
- `experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md`;
- `experiments/agent_selection_demo/reports/demo_completion_closeout_zh.md`;
- `experiments/agent_selection_demo/results/closeout_summary.json`.

Closeout must answer:

1. What timeout settings are now active?
2. How many new paid cells were run?
3. Did Kilo pass the doubled-timeout reliability gate?
4. What is the random-baseline MAE comparison?
5. Does the comparison pass the demo success gate?
6. What Agent-selection evidence can be used today?
7. What cannot be claimed?
8. What is the next experiment?
9. Which tests and hygiene checks passed?

Commit after this package.

## Required Validation

Run at minimum:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q
PYTHONPATH=experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_retrospective_predictive_signal.py -q
git diff --check
git ls-files experiments/agent_selection_demo | rg '(__pycache__|\\.pyc$|raw|transcript|workspace|\\.DS_Store|\\.pytest_cache|\\.venv)'
```

If timeout or workspace-adapter code changes touch phase0 shared tools, run the
relevant phase0 adapter/workspace tests too.

Artifact hygiene rule: do not commit raw prompts, completions, transcripts,
solver workspaces, verifier workspaces, provider logs, cloned repos, caches,
`.pyc`, or secrets.

## Final Response Checklist

The executing agent's final response must state:

- packages completed and blocked;
- active timeout settings;
- paid cells used;
- random-baseline MAE matrix and improvement;
- whether the demo success gate passed;
- Agent-selection pass-rate matrix and MAE;
- Kilo reliability-gate result;
- final demo claim;
- tests and hygiene checks.

Only mark the goal complete when this checklist is answered.
