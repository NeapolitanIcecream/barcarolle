# Boltons Task Generator Capacity Audit Runbook 2026-06-15

Status: mandatory no-paid audit runbook for deciding whether to continue the
Agent Tuning Demo on `mahmoud/boltons` or return to target-repository selection.

This runbook answers a concrete question:

> Does `mahmoud/boltons` have enough additional task-generator capacity to
> support a stronger rolling-origin Agent Tuning Demo, or should Barcarolle move
> back to repository selection and prepare a better target?

Do not run paid Agent cells in this runbook. The output should be a hard
recommendation backed by local task-supply, certification, time-distribution,
and cost evidence.

## Background

Phase 2b produced a disciplined but negative tuning result:

- terminal state: `phase2b_dev_negative`;
- only one usable time-ordered `boltons` window;
- LLM-driven proposer generated two train-only Kilo `AGENTS.md` appendices;
- both candidates matched baseline on dev: `4/6 -> 4/6`, paired net wins `0`;
- future validation was correctly skipped.

The current concern is that the experiment may be underpowered because current
`boltons` certified/scoreable task supply is too small or too unevenly
distributed over time. Existing repo inventory says `boltons` has substantial
history, but that does not automatically mean enough certified, scoreable,
time-distributed tasks for rolling-origin tuning.

## Required Reading

Read before running tools:

- `AGENTS.md`
- `PROCESS.md`
- `experiments/agent_tuning_demo/reports/phase2b_closeout_zh.md`
- `experiments/agent_tuning_demo/results/phase2b_closeout.json`
- `experiments/agent_tuning_demo/reports/phase2b_task_supply_headroom_audit_zh.md`
- `experiments/agent_tuning_demo/results/phase2b_task_supply_headroom_audit.json`
- `experiments/phase1_compiler/reports/phase1_task_supply_v2_repo_inventory.md`
- `experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md`
- `experiments/agent_selection_demo/reports/second_repo_gate_zh.md`
- `docs/research/project-state-after-proposal.md`
- `docs/research/current-project-story.md`

Inspect relevant task-supply tools before invoking or modifying them:

- `experiments/phase1_compiler/tools/phase1_task_supply_v2_generator_bakeoff.py`
- `experiments/phase1_compiler/tools/phase1_two_repo_certified_supply_expansion.py`
- `experiments/phase1_compiler/tools/phase1_third_repo_release_supply_screen.py`
- `experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py`
- `experiments/phase1_compiler/tools/phase1_task_supply_v2_fresh_certification.py`
- `experiments/phase1_compiler/tools/phase1_attrs_source_repair.py`

Preserve unrelated untracked runbook/prompt files.

## Non-Goals

- Do not run paid Agent or LLM cells.
- Do not run Agent tuning.
- Do not run another Agent selection matrix.
- Do not claim predictive validity.
- Do not choose a new repository based on vibes. Use supply evidence.
- Do not commit raw prompts, completions, transcripts, cloned repos, workspaces,
  caches, or large raw generator outputs.

## Output Directory

Use existing experiment locations where possible:

```text
experiments/agent_tuning_demo/reports/
experiments/agent_tuning_demo/results/
```

Use `boltons_capacity_` prefixes for this audit.

## Package 1: Current Supply And Outcome Inventory

Goal: establish the current baseline before further mining.

Tasks:

1. Inventory current `boltons` task supply across all committed sanitized
   sources:
   - certified task files;
   - selection demo task tables;
   - task pool audit;
   - selector bakeoff feature tables;
   - Phase 1 compiler supply results.
2. Deduplicate by stable task identity and statement hash where available.
3. Report:
   - total candidate tasks;
   - certified tasks;
   - release-eligible tasks;
   - tasks with current Kilo low-cost outcomes;
   - tasks with complete multi-Agent outcomes;
   - source reservoirs;
   - module/path/test coverage;
   - time distribution.
4. Explain the difference between:
   - raw candidates;
   - certified candidates;
   - scoreable paid outcomes;
   - windows usable for Phase 2b tuning.

Deliverables:

- `experiments/agent_tuning_demo/reports/boltons_capacity_current_inventory_zh.md`
- `experiments/agent_tuning_demo/results/boltons_capacity_current_inventory.json`

Acceptance:

- The report identifies exactly why Phase 2b had only one usable window.
- The report quantifies the gap between raw/certified/scoreable supply.

Commit after this package.

## Package 2: No-Paid Generator Capacity Audit

Goal: estimate how much more `boltons` supply the existing internal task
generators can produce.

Tasks:

1. Run or reuse no-paid generator/bakeoff tools for `boltons`.
2. Do not use paid statement generation.
3. Do not certify broad raw outputs by hand unless the certification path is
   deterministic and bounded.
4. Produce a candidate expansion inventory with:
   - source type;
   - commit/PR/issue anchor;
   - base/target commit availability;
   - changed code files;
   - changed/usable test files;
   - oracle/source-context availability;
   - estimated certification difficulty;
   - time bucket.
5. Separate:
   - already used tasks;
   - previously certified but unused tasks;
   - raw candidates likely certifiable;
   - raw candidates blocked by missing oracle/context/environment.

Deliverables:

- `experiments/agent_tuning_demo/reports/boltons_capacity_generator_audit_zh.md`
- `experiments/agent_tuning_demo/results/boltons_capacity_generator_audit.json`

Acceptance:

- The report estimates the incremental certified-task potential for `boltons`.
- It distinguishes "can mine raw candidates" from "can support paid
  rolling-origin tuning soon".

Commit after this package.

## Package 3: Bounded Certification Dry Run

Goal: test whether promising new `boltons` candidates can actually be certified
without paid calls.

Tasks:

1. Select a bounded sample of promising new `boltons` candidates from Package 2.
   Suggested size: `10-20`.
2. Prefer candidates that improve time distribution, especially middle/recent
   future buckets.
3. Run the existing no-paid certification or replay checks where available:
   - base commit checkout;
   - test file availability;
   - verifier command feasibility;
   - changed-test oracle extraction;
   - environment/reference subgates.
4. Classify each sampled candidate:
   - certified;
   - likely certifiable with small repair;
   - blocked by source context;
   - blocked by oracle;
   - blocked by environment;
   - duplicate or low value.

Deliverables:

- `experiments/agent_tuning_demo/reports/boltons_capacity_certification_dry_run_zh.md`
- `experiments/agent_tuning_demo/results/boltons_capacity_certification_dry_run.json`

Acceptance:

- The dry run gives a realistic conversion-rate estimate from raw candidates to
  certified tasks.
- It identifies the dominant bottleneck if conversion is poor.

Commit after this package.

## Package 4: Rolling-Origin Window Capacity Simulation

Goal: answer whether `boltons` can support more than one credible rolling-origin
or time-ordered tuning window.

Tasks:

1. Combine existing certified tasks with likely-new certified tasks from the dry
   run.
2. Simulate possible train/dev/future splits.
3. Require each candidate window to meet, unless explicitly waived:

```text
train_tasks_min: 10
dev_tasks_min: 6
future_tasks_min: 8
time_ordered: true
future_not_reused_across_primary_windows: preferred
baseline_headroom_target: 0.20 to 0.70 when current outcomes exist
source_diversity: at least two source reservoirs when feasible
module_diversity: avoid one-module-only windows unless justified
```

4. Estimate paid cost for a Phase 2b-style run:
   - baseline/tuned dev;
   - up to two candidate artifacts;
   - baseline/tuned future only for dev-positive windows.
5. Report if windows are:
   - credible rolling-origin windows;
   - time-ordered single-window only;
   - underpowered;
   - saturated;
   - too expensive for current value.

Deliverables:

- `experiments/agent_tuning_demo/reports/boltons_capacity_window_simulation_zh.md`
- `experiments/agent_tuning_demo/results/boltons_capacity_window_simulation.json`

Acceptance:

- The report states whether `boltons` can plausibly support at least two
  windows after further mining/certification.
- It includes estimated task counts and paid-cell/cost ranges.

Commit after this package.

## Package 5: Repository Selection Fallback Audit

Goal: if `boltons` is weak, identify whether returning to target-repository
selection is the better next move.

Tasks:

1. Compare `boltons` against existing candidate repositories from committed
   inventory:
   - `python-attrs/attrs`;
   - `toolz`;
   - `humanize`;
   - `click` if current artifacts support it.
2. For each candidate, report:
   - current raw/certified supply;
   - historical size;
   - test/environment maturity;
   - rolling-origin potential;
   - expected adapter/packaging repairs;
   - paid readiness;
   - relevance to Agent tuning demo.
3. Do not start a paid matrix for any candidate.
4. If recommending a new target, name the minimal no-paid readiness work before
   paid runs.

Deliverables:

- `experiments/agent_tuning_demo/reports/boltons_capacity_repo_selection_fallback_zh.md`
- `experiments/agent_tuning_demo/results/boltons_capacity_repo_selection_fallback.json`

Acceptance:

- The fallback recommendation is concrete, not generic.
- It explains whether `attrs`, `toolz`, `humanize`, or another repo is a better
  next target and why.

Commit after this package.

## Package 6: Final Recommendation

Goal: produce the final decision.

Use one terminal state:

- `continue_boltons_capacity_expansion`: boltons can plausibly support the next
  rolling-origin tuning run after bounded certification expansion.
- `continue_boltons_with_single_window_only`: boltons can support only a narrow
  single-window story; use only if the user accepts that weaker claim.
- `return_to_target_repo_selection`: boltons is unlikely to support a persuasive
  multi-window tuning demo soon; choose/prep another repo.
- `blocked_insufficient_local_evidence`: local artifacts/tools cannot answer the
  question without additional external setup.

Decision gates:

Recommend continuing with `boltons` only if most are true:

```text
projected_certified_tasks_after_bounded_expansion >= 60
at_least_two_windows_meet_min_counts == true
dev_or_future_headroom_not_saturated == true
dominant_failure_labels_are_actionable == true
estimated_paid_cost_for_next_pilot_is_reasonable == true
```

Recommend returning to repository selection if most are true:

```text
projected_certified_tasks_after_bounded_expansion < 50
or fewer_than_two_windows_meet_min_counts == true
or recent/future task supply remains sparse
or certification bottleneck requires broad manual/LLM repair
or another candidate repo has clearer supply/readiness
```

Deliverables:

- `experiments/agent_tuning_demo/reports/boltons_capacity_final_recommendation_zh.md`
- `experiments/agent_tuning_demo/results/boltons_capacity_final_recommendation.json`
- concise `PROCESS.md` update only if the active next direction changes

Acceptance:

- The final recommendation directly answers the user's question.
- It says what to do next and what not to do next.
- It includes confidence and key uncertainty.

Commit after this package.

## Validation And Hygiene

Run relevant no-paid scoped tests:

```text
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_task_supply_v2_generator_bakeoff.py -q
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
git diff --check
```

If modified or invoked tooling has other dedicated tests, run those as well.

Hygiene checks:

```text
git ls-files experiments/agent_tuning_demo experiments/phase1_compiler | rg '(\.venv|\.pytest_cache|__pycache__|\.pyc|\.DS_Store|raw|transcript|workspace|secret|prompt|completion)' || true
git diff --cached --name-only | rg '(\.venv|\.pytest_cache|__pycache__|\.pyc|\.DS_Store|raw|transcript|workspace|secret)' || true
```

Investigate hits. Some existing committed files may contain "raw" in a
historical inventory filename; do not add new raw artifacts.

## Final Closeout Requirements

Final response and closeout must include:

- terminal state;
- current boltons raw/certified/scoreable supply counts;
- projected incremental certified capacity;
- certification dry-run conversion estimate;
- rolling-origin window simulation result;
- cost estimate for next paid pilot if continuing;
- repository fallback comparison;
- final recommendation;
- tests and hygiene checks;
- commits made.
