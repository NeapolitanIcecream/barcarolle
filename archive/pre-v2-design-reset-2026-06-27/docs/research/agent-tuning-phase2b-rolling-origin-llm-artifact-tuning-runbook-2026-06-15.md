# Agent Tuning Phase 2b Rolling-Origin LLM Artifact Tuning Runbook 2026-06-15

Status: mandatory Phase 2b runbook for moving beyond the Phase 2a engineering
pilot.

Phase 2a proved action-level artifact injection and completed a frozen
before/after validation loop, but it did not demonstrate tuned improvement:
Selection-dev was `1/4 -> 1/4`, Holdout was `5/6 -> 5/6`, and paired net wins
were `0` on both splits. It also used a custom local proposer with no reflection
LM, so it was not a real LLM-driven tuning run.

Phase 2b must not repeat that weak setup. It must use a rolling-origin style
evaluation design, choose tasks with real headroom, and use an LLM-driven
artifact proposer or a clearly documented reason why the proposer could not be
used.

## Objective

Build a stronger Agent Tuning Demo that can support this limited claim if it
succeeds:

> Across one or more frozen rolling-origin windows, Barcarolle used past
> target-repo Agent failures to produce a deployable repo-local Agent artifact,
> and later target-repo tasks showed non-regression plus at least some positive
> paired improvement under fixed Agent and verifier conditions.

This is still a demo-level claim. It is not full predictive validity, model
fine-tuning, full opaque-Agent tuning, cross-repo generalization, or statistical
significance unless the data actually supports those stronger claims.

## Key Differences From Phase 2a

Phase 2b must improve on Phase 2a in four ways:

1. **Rolling-origin framing:** use multiple time-ordered windows when task
   supply allows, not one static Holdout.
2. **Headroom gate:** select Agent/task slices where baseline pass rate is not
   saturated and not hopeless.
3. **LLM-driven proposer:** use GEPA/Phoenix/LLM reflective proposer to generate
   artifacts from failure evidence. Do not present a deterministic local
   template as a real tuner.
4. **Improvement gate:** Selection-dev must show positive paired net wins before
   spending Holdout cells. Non-regression alone is not enough for a Phase 2b
   tuning-success claim.

## Required Reading

Read before changing code:

- `AGENTS.md`
- `PROCESS.md`
- `experiments/agent_tuning_demo/reports/phase1_feasibility_closeout_zh.md`
- `experiments/agent_tuning_demo/reports/phase2_closeout_zh.md`
- `experiments/agent_tuning_demo/reports/phase2_agent_tuning_demo_report_zh.md`
- `experiments/agent_tuning_demo/results/phase2_closeout.json`
- `experiments/agent_tuning_demo/reports/phase2_action_preflight_zh.md`
- `experiments/agent_tuning_demo/results/phase2_action_preflight.json`
- `experiments/agent_tuning_demo/results/phase2_selection_dev_results.csv`
- `experiments/agent_tuning_demo/results/phase2_holdout_results.csv`
- `docs/research/agent-tuning-tuner-compatibility-2026-06-14.md`
- `experiments/agent_tuning_demo/tools/`
- `experiments/agent_selection_demo/results/selection_score_table.csv`
- `experiments/agent_selection_demo/results/holdout_score_table.csv`
- `experiments/agent_selection_demo/results/doubled_timeout_top2_repeat_score_table.csv`
- any existing Phase 1 compiler task supply, rolling-origin, and future-holdout
  artifacts relevant to `mahmoud/boltons`, `python-attrs/attrs`, or other
  available target repositories.

Preserve unrelated untracked files, especially runbook/prompt drafts that were
intentionally left untracked.

## Directory Layout

Continue under:

```text
experiments/agent_tuning_demo/
  config/
  reports/
  results/
  schemas/
  tests/
  tools/
```

Use `phase2b_` prefixes for new artifacts.

## Paid-Call Boundary

Default to no-paid audit first. Do not run paid tuning until Packages 1-3 pass.

All paid LLM or Agent calls must use:

```text
LLM_BASE_URL
LLM_API_KEY
```

No fallback auth is allowed.

Recommended caps:

```text
llm_proposer_calls_max: 8
agent_paid_cells_max: 72
total_estimated_cost_soft_cap_usd: 8.00
```

If windows or headroom are weak, run fewer cells or stop with a no-paid negative
readiness report.

## Package 1: Reframe Phase 2a And Freeze Phase 2b Claim

Goal: prevent overclaiming and freeze the stronger Phase 2b target.

Tasks:

1. Record Phase 2a as:
   - action-level preflight success;
   - end-to-end artifact validation pilot;
   - no tuned improvement;
   - no real reflection-LM tuner.
2. Freeze Phase 2b success criteria:
   - rolling-origin or time-ordered future validation;
   - LLM-driven artifact proposer;
   - positive Selection-dev paired net wins before Holdout;
   - later/future non-regression at minimum, positive paired net wins preferred;
   - cost/latency and invalid-run checks.
3. Define exact supported and unsupported claims before seeing Phase 2b results.

Deliverables:

- `experiments/agent_tuning_demo/reports/phase2b_claim_and_phase2a_reframe_zh.md`
- `experiments/agent_tuning_demo/results/phase2b_claim_and_phase2a_reframe.json`

Acceptance:

- Report explicitly says Phase 2a did not prove tuning improvement.
- Report explicitly says a deterministic local proposer is not a real
  LLM-driven tuner.
- Phase 2b success gates are frozen.

Commit after this package.

## Package 2: Rolling-Origin Task-Supply And Headroom Audit

Goal: decide whether a paid Phase 2b tuning run is justified and where.

Tasks:

1. Inventory available tasks and sanitized outcomes for:
   - `mahmoud/boltons`;
   - any already prepared second repository such as `python-attrs/attrs`;
   - other repositories only if they already have enough Barcarolle-compatible
     task supply and verifier support.
2. Build candidate rolling-origin windows. Each window should have:
   - `train`: past tasks visible to proposer;
   - `dev`: near-future tasks used to select artifact;
   - `future`: later tasks used only after artifact freeze.
3. For each candidate window, estimate:
   - available train/dev/future task counts;
   - existing baseline outcome coverage;
   - expected paid cells needed for fresh baseline/tuned runs;
   - baseline pass-rate headroom;
   - recurring failure labels;
   - infrastructure risk;
   - hidden-oracle/leakage risk.
4. Prefer windows where baseline pass rate is roughly:

```text
dev/future baseline pass rate target: 0.20 to 0.70
avoid: >0.80 saturated
avoid: <0.15 hopeless unless failure labels are very coherent
```

5. Select 2-3 candidate rolling-origin windows if possible. If task supply is
   too sparse, select one stronger window and explain the limitation.

Deliverables:

- `experiments/agent_tuning_demo/reports/phase2b_task_supply_headroom_audit_zh.md`
- `experiments/agent_tuning_demo/results/phase2b_task_supply_headroom_audit.json`
- `experiments/agent_tuning_demo/results/phase2b_candidate_windows.json`

Acceptance:

- No paid cells are run in this package.
- The report states whether rolling-origin is feasible with current task supply.
- The report identifies the recommended Agent/repo/window set or stops with a
  negative readiness decision.

Commit after this package.

## Package 3: Phase 2b Protocol Preregistration

Goal: freeze the paid/no-paid protocol before any proposer or fresh validation
run.

Tasks:

1. Freeze selected windows.
2. Freeze target Agent:
   - default candidate: Kilo low-cost if it has headroom;
   - choose another real Agent only if the audit shows better headroom and
     reliable injection.
3. Freeze artifact surface:
   - default: Kilo repo `AGENTS.md` appendix;
   - use Kilo `.kilo/rules` only if the audit shows a strong reason.
4. Freeze proposer:
   - primary: real LLM-driven GEPA or GEPA-shaped reflective proposer;
   - fallback: Phoenix-style LLM prompt/rule proposer;
   - if neither can use an LLM reflection/proposal step, stop or label the run
     as non-LLM pilot.
5. Freeze candidate count and iteration caps:

```text
max_windows: 3
min_windows_for_rolling_origin_claim: 2
max_candidates_per_window: 2
max_reflection_iterations_per_window: 2
dev_tasks_per_window_target: 4 to 8
future_tasks_per_window_target: 4 to 8
```

6. Freeze success gates:

```text
selection_dev_gate:
  paired_net_wins > 0
  invalid_or_unscoreable_tuned <= baseline
  cost_per_task <= baseline * 1.50 unless explicitly justified

future_gate_green:
  aggregate_future_paired_net_wins > 0
  no window has material regression

future_gate_yellow:
  aggregate_future_paired_net_wins == 0
  no window has material regression
  behavior/failure labels improve

future_gate_red:
  aggregate_future_paired_net_wins < 0
  or tuned invalid/timeout materially worse
```

7. Freeze leakage controls:
   - proposer sees train only;
   - dev scores select artifact;
   - future tasks/logs/outcomes are hidden until artifact hash freeze;
   - no candidate artifact may contain future-derived content.

Deliverables:

- `experiments/agent_tuning_demo/reports/phase2b_protocol_zh.md`
- `experiments/agent_tuning_demo/results/phase2b_protocol.json`

Acceptance:

- Protocol is specific enough to execute without reinterpretation.
- It includes a no-go condition if task supply/headroom is inadequate.
- It records exact paid-cell and cost caps.

Commit after this package.

## Package 4: LLM-Driven Proposer Integration

Goal: implement or wire a real LLM-driven proposer for repo-local artifacts.

Primary path:

```text
GEPA standalone / optimize_anything, or a GEPA-shaped reflective proposer using
an LLM proposal/reflection call
```

Backup:

```text
Phoenix-style LLM prompt/rule proposer
```

Requirements:

1. The proposer receives only train failure labels and sanitized train
   summaries.
2. The proposer must generate at least one candidate artifact from the evidence,
   not from a hardcoded local template.
3. Each candidate must include:
   - targeted failure labels;
   - evidence task IDs from train only;
   - expected behavior change;
   - rollback plan;
   - deterministic artifact hash;
   - `holdout_derived: false`.
4. Store only sanitized proposer input/output summaries. Raw prompt/completion
   content must remain in ignored paths.
5. If no LLM proposer can be made to run safely, stop before paid Agent
   validation or continue only as a clearly labeled non-LLM negative/control run.

Deliverables:

- `experiments/agent_tuning_demo/reports/phase2b_proposer_integration_zh.md`
- `experiments/agent_tuning_demo/results/phase2b_proposer_integration.json`
- `experiments/agent_tuning_demo/results/phase2b_candidate_artifacts.json`
- sanitized candidate artifacts under
  `experiments/agent_tuning_demo/results/phase2b_candidate_artifacts/`

Acceptance:

- At least one candidate artifact was generated by an LLM-driven proposer; or
- report records why Phase 2b cannot proceed as LLM-driven tuning.

Commit after this package.

## Package 5: Rolling-Origin Dev Evaluation

Goal: evaluate candidate artifacts on each window's dev split and select only
positive candidates for future validation.

For each selected window:

1. Run fresh baseline on dev if stale or missing.
2. Run each candidate artifact on the same dev tasks.
3. Compute:
   - pass rates;
   - paired net wins;
   - improved/regressed task IDs;
   - invalid/unscoreable counts;
   - cost/latency;
   - behavior markers if available.
4. Select at most one artifact per window by preregistered rule.
5. Do not run future validation for a window if dev paired net wins are not
   positive, unless the runbook records a deliberate yellow-path exception.

Deliverables:

- `experiments/agent_tuning_demo/reports/phase2b_dev_eval_zh.md`
- `experiments/agent_tuning_demo/results/phase2b_dev_eval.csv`
- `experiments/agent_tuning_demo/results/phase2b_dev_eval_summary.json`

Acceptance:

- Dev results are paired baseline/tuned by task.
- Future gate decision is explicit per window.
- Candidate artifacts are frozen before any future run.

Commit after this package.

## Package 6: Frozen Rolling-Origin Future Validation

Goal: validate chosen artifacts on future tasks after artifact freeze.

For each window that passed dev gate:

1. Confirm chosen artifact hash is frozen.
2. Run fresh baseline on future tasks unless a same-condition fresh baseline
   already exists and is explicitly marked comparable.
3. Run tuned artifact on the same future tasks.
4. Compute paired metrics:
   - pass rate;
   - paired net wins;
   - improved/regressed task IDs;
   - invalid/unscoreable counts;
   - cost/latency;
   - behavior/failure label shifts if available.

Do not compare fresh tuned cells against stale baseline without labeling the
comparison retrospective-only.

Deliverables:

- `experiments/agent_tuning_demo/reports/phase2b_future_validation_zh.md`
- `experiments/agent_tuning_demo/results/phase2b_future_validation.csv`
- `experiments/agent_tuning_demo/results/phase2b_future_validation_summary.json`

Acceptance:

- Future validation uses frozen artifacts only.
- Aggregate and per-window paired net wins are reported.
- Negative, neutral, and positive results are all acceptable if reported
  honestly.

Commit after this package.

## Package 7: Final Phase 2b Report

Goal: produce a final reader-facing report and process handoff.

Deliverables:

- `experiments/agent_tuning_demo/reports/phase2b_agent_tuning_demo_report_zh.md`
- `experiments/agent_tuning_demo/reports/phase2b_closeout_zh.md`
- `experiments/agent_tuning_demo/results/phase2b_closeout.json`
- concise `PROCESS.md` update with canonical links and current claim boundary

Report outline:

1. Why Phase 2a was not enough.
2. Rolling-origin design and task supply.
3. Target Agent and artifact surface.
4. LLM-driven proposer and candidate artifacts.
5. Dev results and gate decisions.
6. Future validation results.
7. Cost/latency and invalid-run impact.
8. Case studies:
   - one improved task if any;
   - one unchanged task;
   - one regression or remaining failure if any.
9. Supported claims.
10. Unsupported claims.
11. Recommended next work.

Commit after this package.

## Validation And Hygiene

Run at minimum:

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
uv run --project experiments/phase0_headroom pytest experiments/phase0_headroom/tools/test_cli_workspace_adapters.py experiments/phase0_headroom/tools/test_workspace_acut_run.py -q
git diff --check
```

If new tooling touches Phase 1 compiler data, run the relevant scoped tests for
that tooling as well.

Hygiene checks:

```text
git ls-files experiments/agent_tuning_demo | rg '(\.venv|\.pytest_cache|__pycache__|\.pyc|\.DS_Store|raw|transcript|workspace|secret|prompt|completion)' || true
git diff --cached --name-only | rg '(\.venv|\.pytest_cache|__pycache__|\.pyc|\.DS_Store|raw|transcript|workspace|secret)' || true
```

Investigate any hits. Do not commit raw prompts, completions, transcripts,
solver workspaces, verifier workspaces, secrets, cloned repos, caches, or large
raw outputs.

## Terminal States

Use one final state:

- `phase2b_success_future_improved`: rolling-origin/future validation has
  aggregate positive paired net wins and no material regression.
- `phase2b_yellow_non_regression`: LLM-driven tuning ran, future validation did
  not regress but did not improve.
- `phase2b_dev_negative`: LLM-driven artifacts did not pass dev improvement
  gate; future validation was not run.
- `phase2b_task_supply_blocked`: rolling-origin/headroom audit found inadequate
  task supply or headroom.
- `phase2b_llm_proposer_blocked`: no safe LLM-driven proposer could be run.
- `phase2b_infrastructure_blocked`: execution was blocked by adapter,
  verifier, workspace, or endpoint instability after repair attempts.

Do not call the run successful if it only repeats Phase 2a non-regression with a
non-LLM local proposer.

## Final Closeout Requirements

Final response and closeout must include:

- terminal state;
- whether Phase 2a was relabeled correctly;
- rolling-origin windows and task counts;
- target Agent and artifact surface;
- LLM proposer used and number of proposer calls;
- paid Agent cells and estimated/observed cost;
- dev baseline/tuned matrix by window;
- future baseline/tuned matrix by window if run;
- paired net wins by window and aggregate;
- cost/latency/invalid-run comparison;
- behavior/failure-label changes;
- tests and hygiene checks;
- exact supported and unsupported claims;
- commits made.
