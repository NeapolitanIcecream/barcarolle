# Agent Selection Selector Evolution Runbook 2026-06-14

Status: mandatory long-running runbook for turning the Agent-selection demo
from "facility plus random-baseline traction" into a decision-ready demo.

This runbook supersedes the random-baseline demo-evidence runbook when the goal
is to support the specific user story:

> A user looks at Selection results, chooses an Agent, and later Holdout results
> validate that choice.

The previous runbook established important evidence:

- real complete Agents can be run and verified end to end;
- the current candidate selector has lower pass-rate MAE than same-budget
  random task sampling;
- Kilo + GPT mainline is a reliability-gated leader in the existing boltons
  top-2 evidence.

That is not enough for the Agent-selection story because the original
Selection set had Codex + GPT mainline and Kilo + GPT mainline tied at `15/20`.
The recommendation was not a clean quality recommendation, and the Holdout lead
therefore validates the facility's ability to catch instability more than it
validates the selector's ability to choose an Agent.

This runbook makes task selection a standalone algorithm problem and requires
the executing Agent to explore, implement, evaluate, and report selectors until
there is decision-ready evidence or a hard, well-evidenced negative result.

## Target Outcome

Build and validate a decision-aware task selector that can support this demo
claim:

> On a frozen Selection benchmark, the facility recommends an Agent using
> preregistered decision rules; on later/Holdout tasks, the recommended Agent is
> also the winner or has low regret. The selected benchmark is better than
> same-budget random and strong random baselines for Agent-selection decisions,
> not only for aggregate pass-rate MAE.

The result may be small-scale and demo-level. It must be logically clean.

## Non-goals

- Do not claim full predictive validity.
- Do not claim global model, harness, or Agent ranking.
- Do not tune on the final Holdout/later outcomes and then present the same
  outcomes as validation.
- Do not expand the model matrix by default.
- Do not make this a Kilo adapter repair project unless adapter failures block
  the selected evidence path.
- Do not turn this into a second-repo paid matrix unless the no-paid and
  boltons paths are exhausted and the paid boundary below permits it.

## Required Reading

Read these before changing code:

- `AGENTS.md`
- `PROCESS.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0614-0.md` if present
- `experiments/agent_selection_demo/reports/demo_predictive_facility_story_zh.md`
- `experiments/agent_selection_demo/reports/demo_agent_selection_evidence_zh.md`
- `experiments/agent_selection_demo/reports/random_baseline_predictive_signal_zh.md`
- `experiments/agent_selection_demo/reports/rolling_origin_eval_zh.md`
- `experiments/agent_selection_demo/results/closeout_summary.json`
- `experiments/agent_selection_demo/results/selection_score_table.csv`
- `experiments/agent_selection_demo/results/holdout_score_table.csv`
- `experiments/agent_selection_demo/results/doubled_timeout_top2_repeat_score_table.csv`
- `experiments/agent_selection_demo/results/rolling_origin_eval_slices.csv`
- `experiments/agent_selection_demo/tools/agent_selection_demo.py`

## Core Definitions

Selection algorithm input:

- target repository;
- origin time or frozen Selection context;
- candidate task pool visible before that origin;
- task metadata, including time, source, module/path, test type, change size,
  source cluster, oracle/certification quality, and risk/flakiness markers when
  available;
- candidate Agents;
- historical Agent-task pass/fail outcomes allowed by the origin mask;
- benchmark budget `k`.

Selection algorithm output:

- `k` benchmark tasks;
- optional task weights only if justified, but prefer unweighted pass rate for
  the demo;
- enough metadata to audit why each task was selected.

Decision output after running/replaying Selection:

- `recommend: <Agent>`;
- `abstain: indistinguishable-on-benchmark`;
- `need-more-evidence`.

Primary decision metrics:

- pass-rate MAE between Selection and later/Holdout;
- pairwise direction agreement on non-tie Agent pairs;
- top-1 agreement;
- recommendation regret;
- risk/coverage for recommendation versus abstention;
- random-baseline percentile for MAE and decision metrics.

## Hard Success Criteria

Do not mark the run complete until one of these terminal states is reached.

### Preferred Terminal State: Decision-ready Demo Evidence

All of the following must be true:

1. At least two selector families are implemented and evaluated:
   - RSQ: recency-stratified quota selector or a clearly equivalent strong
     metadata baseline;
   - HRD: hybrid representative + disagreement selector or a clearly equivalent
     decision-aware selector.
2. At least three baselines are implemented:
   - uniform random same-budget;
   - quality-filtered random;
   - stratified random using the same strata as RSQ.
3. A decision wrapper is implemented:
   - paired task-level uncertainty or an explicitly justified small-sample
     fallback;
   - `recommend`, `abstain`, and `need-more-evidence` states;
   - fixed thresholds before final evaluation.
4. A rolling-origin or frozen pseudo-future protocol is implemented with
   leakage masks:
   - train/development origins may be used for selector design;
   - final origins or final demo slice must be evaluated after selector config
     is frozen;
   - the report states exactly what information was visible at selection time.
5. At least one frozen final evaluation slice produces:
   - a Selection recommendation, not only abstention;
   - the same top Agent on later/Holdout, or recommendation regret no worse than
     `5` percentage points;
   - pairwise direction agreement for the recommended Agent against the nearest
     serious competitor;
   - Selection-to-later/Holdout MAE better than strong random baseline by at
     least `10%` relative or `0.02` absolute;
   - decision metrics better than same-budget random distribution, not just one
     cherry-picked random sample.
6. The final Chinese story is easy to explain:
   - "Selection chose Agent A; later/Holdout also favored Agent A";
   - or "when Selection did not have enough evidence, the system abstained;
     when it recommended, regret was low."

### Accepted Negative Terminal State

If preferred success is not achievable, the run may complete only after:

- all mandatory no-paid algorithm packages are implemented and evaluated;
- paid cells allowed by this runbook are either unnecessary, exhausted, or
  rejected by a hard gate;
- the closeout identifies the exact reason the story could not be made true:
  task supply, missing outcome grid, selector weakness, stochasticity,
  unreliable Agent path, or invalid oracle/task quality;
- the final report gives a concrete next engineering move instead of asking for
  manual intervention.

Do not stop after a partial diagnostic if additional packages can still run.

## Paid-call Boundary

Default: run no new paid cells. First exhaust existing sanitized score tables,
rolling-origin artifacts, and no-paid replay.

Approved paid cells only after:

1. the selector config, decision rule, task IDs, Agent set, invalid-cell policy,
   and success thresholds are frozen and written to a preregistration artifact;
2. the no-paid evidence shows that missing cells, not selector logic, are the
   bottleneck;
3. environment checks prove `LLM_BASE_URL` and `LLM_API_KEY` are set and used.

Approved hard cap: `80` new paid cells.

Priority order:

1. Fill the common grid for one frozen final Selection benchmark:
   `selected tasks x top-2 Agents`.
2. Fill the matching later/Holdout common grid for those top-2 Agents.
3. If the top-2 story succeeds and budget remains, fill the same tasks for the
   other existing demo Agents.
4. If still inconclusive and budget remains, run one same-budget strong-random
   control set for the same top-2 Agents.

Do not run paid cells for a second repository unless boltons cannot produce a
valid final slice, a no-paid second-repo gate passes, and the selected paid
cells still fit inside the `80` cell cap. Any second-repo paid use must be
preregistered in the run's own artifact before execution.

All paid calls must use `LLM_BASE_URL` plus `LLM_API_KEY`.

## Blocker Standard

"Blocked" is allowed only after the executing Agent has:

- found the exact code path, command, data artifact, or provider behavior;
- made a concrete local fix if the issue is in repo code;
- added or updated a focused test when feasible;
- tried smaller `k`, top-2-only evaluation, stricter quality filters, and
  no-paid rolling-origin fallback when task supply is sparse;
- continued independent packages that do not depend on the blocked path.

Do not ask for manual intervention during this run. If a user decision would
normally be helpful, choose the conservative option inside the boundaries above
and document it.

## Package 1: Problem And Evidence Audit

Produce:

```text
experiments/agent_selection_demo/reports/selector_evolution_problem_statement_zh.md
experiments/agent_selection_demo/results/selector_evolution_inventory.json
```

Required content:

- explain why the current random-baseline story is insufficient for Agent
  selection;
- list all available score tables and which Agents/tasks/stages they cover;
- identify missing cells and whether they are needed for the new story;
- define the exact decision metrics to optimize;
- choose initial budgets `k` to evaluate, including at least the current
  Selection size and one smaller sensitivity setting if task supply is sparse;
- choose the candidate Agent set, defaulting to the existing demo Agents and a
  top-2 subset for paid fallback.

Acceptance:

- no paid calls;
- explicitly separates pass-rate prediction from Agent-selection decision
  quality;
- states how leakage will be avoided in rolling-origin replay.

Commit after this package.

## Package 2: Selector Data Model And Frozen Protocol

Implement or extend code so the demo can build a reusable selector dataset.

Required artifacts:

```text
experiments/agent_selection_demo/results/selector_task_table.csv
experiments/agent_selection_demo/results/selector_outcome_matrix.csv
experiments/agent_selection_demo/results/selector_protocol.json
experiments/agent_selection_demo/reports/selector_protocol_zh.md
```

Data requirements:

- one row per task with stable `task_id`;
- visible time/origin field when available;
- source cluster;
- stage/source table;
- module/path or a deterministic fallback bucket;
- task/source type if available, otherwise `unknown`;
- change-size or difficulty proxy if available, otherwise documented fallback;
- quality/risk/flakiness fields when available, otherwise conservative default;
- one row per `(task_id, agent_id, stage/window)` outcome with pass/fail/NA,
  scoreability, timeout/infra labels, and source artifact path.

Protocol requirements:

- rolling-origin split plan with train/dev/final segments where data permits;
- final demo slice definition if rolling origins are sparse;
- invalid-cell policy:
  - solver timeout, invalid diff, and normal verifier failure count as fail;
  - verifier outage, invalid task, and oracle flake count as NA;
  - pairwise metrics use common valid cells;
- all random seeds and budgets fixed;
- final evaluation outcomes must be masked from selector training.

Acceptance:

- tests cover dataset construction and leakage mask behavior;
- if metadata is sparse, code creates deterministic fallback features and the
  report says so plainly.

Commit after this package.

## Package 3: Strong Baselines And RSQ

Implement no-paid selectors:

- `uniform_random_same_budget`;
- `quality_filtered_random`;
- `stratified_random`;
- `rsq_recency_stratified_quota`.

RSQ minimum design:

- hard filter on quality/risk/flakiness where data exists;
- strata over module/path bucket, source/stage type, change-size/difficulty
  bucket, and recency bucket;
- recency weighting or quota preference for future-like tasks;
- per-cluster or per-module cap to avoid duplicates;
- deterministic output for fixed seed/config.

Produce:

```text
experiments/agent_selection_demo/results/selector_baseline_eval.json
experiments/agent_selection_demo/reports/selector_baseline_eval_zh.md
```

Acceptance:

- 1000 random seeds minimum for random baselines, or a documented lower number
  if data size makes all samples duplicate;
- reports MAE, pairwise agreement, top-1 agreement, regret, and random
  percentiles;
- tests cover deterministic selection and quota behavior.

Commit after this package.

## Package 4: HRD Decision-aware Selector

Implement HRD or an equivalent hybrid selector.

Minimum first version:

- `70%` representative tasks from RSQ or facility-location-like coverage;
- `30%` discriminative tasks chosen for likely Agent disagreement;
- variants `60/40` and `50/50` if no-paid replay is cheap;
- graceful fallback when historical Agent disagreement is unavailable:
  use difficulty proxy and avoid all-easy/all-hard task sets.

Discriminative score may use:

- historical pairwise disagreement;
- predicted disagreement from a low-capacity model if enough data exists;
- task difficulty near the middle of observed pass-rate range;
- source/module diversity;
- quality/risk penalties.

Do not use final later/Holdout outcomes when computing task scores.

Produce:

```text
experiments/agent_selection_demo/results/selector_hrd_eval.json
experiments/agent_selection_demo/reports/selector_hrd_eval_zh.md
```

Acceptance:

- compares HRD variants against RSQ and all random baselines;
- reports whether HRD improves the Agent-selection story, not only MAE;
- includes ablations for representative-only and disagreement-only if feasible;
- tests cover representative/discriminative budget split and no future-outcome
  leakage.

Commit after this package.

## Package 5: Decision Wrapper

Implement a shared decision layer for all selectors.

Required outputs:

```text
experiments/agent_selection_demo/results/selector_decision_eval.json
experiments/agent_selection_demo/reports/selector_decision_eval_zh.md
```

Decision states:

- `recommend`;
- `abstain_indistinguishable`;
- `need_more_evidence`.

Recommended default thresholds, to be calibrated on train/dev only:

- meaningful action margin: `5` to `10` percentage points;
- minimum common valid selected tasks per top pair: `8`, or lower only with an
  explicit small-sample caveat;
- paired bootstrap confidence lower bound when enough tasks exist, otherwise
  exact/sign-test or conservative margin fallback;
- if margin is small but uncertainty is narrow, use
  `abstain_indistinguishable`;
- if margin exists but uncertainty/common-valid count is weak, use
  `need_more_evidence`.

Required metrics:

- recommendation coverage;
- false-recommendation rate when later top is known;
- mean and worst recommendation regret;
- missed-opportunity rate for abstentions when later top gap is large;
- correct-abstain rate when later top gap is small;
- top-pair direction agreement.

Acceptance:

- the system never hard-recommends on a tie or cost-only tie-break;
- tests cover recommendation, abstain, and need-more-evidence paths;
- report includes at least one compact table that a non-specialist can read.

Commit after this package.

## Package 6: Frozen Final Evaluation And Optional Paid Completion

Freeze one final selector configuration before final evaluation.

Required preregistration artifact:

```text
experiments/agent_selection_demo/results/selector_final_preregistration.json
experiments/agent_selection_demo/reports/selector_final_preregistration_zh.md
```

It must include:

- selector name and full config;
- budget `k`;
- Agent set;
- final origin/demo slice;
- selected task IDs before outcome join where possible;
- later/Holdout task IDs;
- random seed list;
- invalid-cell policy;
- decision thresholds;
- success criteria;
- paid-cell cap actually used by this run.

Then run final no-paid evaluation from existing sanitized outcomes.

If the final no-paid evaluation already meets the preferred terminal state,
do not run paid cells.

If the final no-paid evaluation is inconclusive only because selected or
later/Holdout cells are missing, run the minimum paid cells needed under the
paid-call boundary. Before any paid cell:

- source `~/.zshrc` if needed and confirm `LLM_BASE_URL` and `LLM_API_KEY`;
- run the relevant adapter smoke/gate for the Agent path;
- record the frozen task IDs and Agent IDs;
- keep raw transcripts/workspaces in ignored paths only.

Produce:

```text
experiments/agent_selection_demo/results/selector_final_eval.json
experiments/agent_selection_demo/reports/selector_final_eval_zh.md
```

Acceptance:

- final evaluation is not silently retuned after seeing results;
- if paid cells are run, cost/usage observation kind is reported;
- if the final result recommends an Agent, later/Holdout validates the choice
  or regret is within the threshold;
- if final result abstains, the report says whether this is a safety success or
  a missed opportunity.

Commit after this package.

## Package 7: Final Demo Story And Closeout

Produce:

```text
experiments/agent_selection_demo/reports/selector_agent_selection_demo_story_zh.md
experiments/agent_selection_demo/reports/selector_evolution_closeout_zh.md
experiments/agent_selection_demo/results/selector_evolution_closeout.json
```

The final story must be written for an internal reviewer, not for the author of
the code. It should avoid unnecessary jargon and answer:

- what problem the old demo still had;
- what changed in the selector;
- what the frozen Selection recommended;
- what Holdout/later showed;
- how this compares to strong random baselines;
- whether the system recommended, abstained, or requested more evidence;
- how much was spent in this run;
- what cannot be claimed.

Closeout checklist:

1. Which selectors were implemented?
2. Which selector is the final locked config?
3. What are the final Selection pass rates?
4. What are the final later/Holdout pass rates?
5. Did top-1 or top-pair ranking transfer from Selection to later/Holdout?
6. What is final MAE versus strong random baselines?
7. What is recommendation regret?
8. Did the system recommend, abstain, or need more evidence?
9. How many new paid cells were run?
10. Which tests and hygiene checks passed?
11. What exact claim is now supported?
12. What remains unproved?

Update `PROCESS.md` with a short handoff entry and links to the final artifacts.

Commit after this package.

## Required Validation

Run at minimum:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q
```

```text
PYTHONPATH=experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_retrospective_predictive_signal.py -q
```

If adapter or workspace code changes:

```text
PYTHONPATH=experiments/phase0_headroom/tools uv run --project experiments/phase1_compiler pytest experiments/phase0_headroom/tools/test_cli_workspace_adapters.py experiments/phase0_headroom/tools/test_workspace_acut_run.py experiments/phase0_headroom/tools/test_workspace_usage_import.py -q
```

Always run:

```text
git diff --check
git ls-files experiments/agent_selection_demo | rg '(__pycache__|\.pyc$|raw|transcript|workspace|\.DS_Store|\.pytest_cache|\.venv)'
```

The final artifact scan should have no prohibited tracked path hits. If `rg`
returns exit code `1` because there are no matches, record that as pass.

