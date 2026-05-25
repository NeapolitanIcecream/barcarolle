# Phase 1 Attrs Generalization And Third-Repo Decision Runbook

Status: implementation runbook, 2026-05-23.

This runbook is for one dedicated Codex CLI session. Its job is to move Phase 1
back from infrastructure repair to the research question in the proposal:

```text
Does the Barcarolle repo-specific benchmark signal predict held-out future
target-repo work, or does the current evidence show a negative or underpowered
pilot?
```

The immediate task is not to rerun the confirmed `attrs__hist__027` policy
violation. That cell has already been classified as a genuine ACUT boundary
violation. The next useful work is to explain the `attrs` H_future collapse,
quantify uncertainty, and decide whether the correct next move is:

- report the two-repo result as negative or underpowered;
- build a better weighted/stratified compiler analysis before spending more;
- mine clean local supply for a third repo, without paid ACUT calls.

## Starting Point

Current committed Phase 1 state:

```text
two-repo validation:
  selected repos: boltons, attrs
  B_eval scoreable cells: 16
  H_future scoreable cells: 15
  policy violations: 1
  non-scoreable cells: 1
  pooled MAE: 0.479167
  predictive_validity_established: false
  production ranking: not_produced

policy violation repair:
  classification: confirmed_acut_policy_violation_no_rerun
  task: attrs__hist__027
  adapter: kilo_workspace
  paid rerun performed: false
  paid rerun permitted: false
  next recommendation:
    analyze_attrs_h_future_generalization_or_mine_third_repo_without_rerunning_confirmed_violation
```

Important observed asymmetry:

```text
boltons:
  B_eval pass rate: 7/8 = 0.875
  H_future pass rate: 7/8 = 0.875

attrs:
  B_eval pass rate: 7/8 = 0.875
  H_future pass rate: 1/7 scoreable = 0.142857
  policy violation: 1
```

The research proposal in `barcarolle-research-0519.md`
sets the main direction:

```text
Barcarolle is a target-repository benchmark compiler, not a task generator or
agent harness. Its success criterion is predictive validity on held-out future
repo work, or a clear report that evidence is insufficient.
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing <repo>/docs/experiments/phase-1-attrs-generalization-third-repo-decision-runbook.md.

Work in <repo>. Use uv for repo-local Python tooling.
Make a cohesive git commit after every completed step that changes files. Do
not batch unrelated steps into one commit. If a step has no file changes, record
that fact in the next process-report update and do not create an empty commit.
Do not push unless the user explicitly asks.

Main goal: explain the current two-repo result, especially the attrs H_future
collapse, and decide the next research branch. Prefer local analysis and
uncertainty quantification before any new supply work. Mine a third repo only
if the evidence says another repo is needed to answer the proposal's predictive
validity question.

Do not rerun attrs__hist__027. Do not rerun any existing scoreable cell. Do not
run paid ACUT cells or paid LLM calls in this runbook. If a later branch appears
to require paid calls, stop and write a precise next-runbook recommendation
instead.

Keep Barcarolle on the benchmark/compiler side of the ACUT boundary. Do not
implement Codex, Kilo, or any other ACUT internals. Barcarolle may inspect
sanitized score artifacts, task metadata, target-repo history, certification
records, and local mining outputs. It may not use hidden verifier details to
tune task selection or weaken scope policy.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
GitHub API responses, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, raw patch bodies, or large raw outputs. Commit only
small sanitized configs, manifests, tools, tests, score tables, summaries,
reports, decisions, and digests. Raw artifacts must remain under ignored paths.
```

## Claim Boundary

Allowed claims:

```text
attrs_h_future_generalization_analyzed
two_repo_uncertainty_quantified
two_repo_negative_or_underpowered_pilot_reported
third_repo_local_supply_needed
third_repo_local_screening_started
weighted_compiler_analysis_needed_before_more_paid_validation
insufficient_evidence_for_predictive_validation
```

Disallowed claims:

```text
predictive_validity_established
production_benchmark_ranking
pure_harness_effect
attrs_policy_violation_repaired
third_repo_paid_validation_completed
third_repo_as_new_predictive_evidence_without_paid_holdout
task_generator_yield_as_main_contribution
```

Interpretation rules:

- A confirmed policy violation remains a benchmark boundary failure. Do not
  relabel it as a scoreable fail.
- A third repo mined locally is supply or preregistration evidence only. It is
  not predictive-validation evidence until paid or otherwise scoreable ACUT
  holdout cells are run under a future runbook.
- More tasks are useful only if they reduce uncertainty about predictive
  validity or compiler design. Do not expand supply merely to make the artifact
  look larger.
- The proposal allows a negative or underpowered result if it is clearly
  reported. Do not force a positive predictive-validity claim.

## Commit Discipline

Every step that changes files must be committed before moving on. Use one or
more commits per step when the step naturally contains separate units.

Suggested commit messages:

```text
Record attrs generalization preflight
Build two repo task outcome matrix
Analyze attrs H_future failure taxonomy
Quantify two repo uncertainty and baseline error
Decide Phase 1 next research branch
Report two repo negative or underpowered pilot
Screen third repo local supply candidates
Record attrs generalization closeout
```

Before every commit:

```bash
git diff --check
git status --short
```

Use non-interactive git commands:

```bash
git add <paths>
git commit -m "<message>"
```

Do not commit ignored raw paths, workspaces, external repos, caches, or secrets.

## Budget And Runtime Rules

This runbook is local-only.

```text
paid ACUT calls: disabled
paid LLM calls: disabled
allowed external metadata lookup: only non-paid GitHub metadata if already
  authenticated and if sanitized before commit
expected provider cost change: USD 0
```

Stop before any paid work and write a blocker if:

- analysis suggests rerunning `attrs__hist__027`;
- analysis suggests rerunning existing scoreable cells;
- a third-repo branch would need paid ACUT cells;
- endpoint or usage accounting would need to be changed;
- the next step requires changing the ACUT harness rather than benchmark-side
  compiler logic.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_attrs_generalization_third_repo_decision.yaml
  results/
    phase1_attrs_generalization_preflight.json
    phase1_two_repo_task_outcome_matrix.json
    phase1_attrs_h_future_failure_taxonomy.json
    phase1_two_repo_uncertainty_and_baselines.json
    phase1_next_research_decision.json
    phase1_mvp_closeout.json
  reports/
    phase1_attrs_generalization_process.md
    phase1_two_repo_task_outcome_matrix.md
    phase1_attrs_h_future_failure_taxonomy.md
    phase1_two_repo_uncertainty_and_baselines.md
    phase1_next_research_decision.md
    phase1_mvp_closeout.md
```

Optional if the decision branch is third-repo local supply:

```text
experiments/phase1_compiler/
  results/
    phase1_third_repo_candidate_reassessment.json
    phase1_third_repo_local_supply_decision.json
  reports/
    phase1_third_repo_candidate_reassessment.md
    phase1_third_repo_local_supply_decision.md
```

Implementation files may be added or updated if durable analysis tooling is
needed:

```text
experiments/phase1_compiler/tools/phase1_attrs_generalization.py
experiments/phase1_compiler/tests/test_phase1_attrs_generalization.py
experiments/phase1_compiler/tools/phase1_compiler.py
experiments/phase1_compiler/tests/test_phase1_compiler.py
```

## Step 0: Preflight And Proposal Alignment

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, and current git
   status.
2. Record existing untracked or unrelated paths. At runbook creation time, the
   known untracked paths were:

```text
docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md
docs/experiments/phase-1-policy-violation-triage-bounded-rerun-runbook.md
```

3. Confirm current decisions:

```bash
jq '{primary_decision_label, selected_repos, selected_repo_id, b_eval_scoreable_cells, h_future_scoreable_cells, policy_violation_count, non_scoreable_count, pooled_mae, predictive_validity_established, production_ranking_status, blockers, recommended_next_runbook}' \
  experiments/phase1_compiler/results/phase1_two_repo_future_holdout_decision.json

jq '{terminal_state, classification_label, paid_rerun_performed, paid_rerun_permitted, policy_violation_count, h_future_scoreable_cells, predictive_validity_established, recommended_next_runbook}' \
  experiments/phase1_compiler/results/phase1_policy_violation_repair_decision.json

jq '{next_runbook_recommendation, predictive_validity_established, production_ranking_status}' \
  experiments/phase1_compiler/results/phase1_mvp_closeout.json
```

4. Record proposal alignment from
   `barcarolle-research-0519.md` in one paragraph:

```text
The next work must support benchmark compiler predictive validity, uncertainty,
or clean evidence boundaries. It must not optimize for task-count yield,
leaderboard ranking, or ACUT harness behavior.
```

5. Run baseline checks:

```bash
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
git diff --check
```

Acceptance:

- current state is recorded without changing conclusions;
- the process report states that this runbook is local-only;
- predictive validity remains `false`;
- no paid calls are made.

Commit:

```text
Record attrs generalization preflight
```

## Step 1: Build The Two-Repo Task Outcome Matrix

Actions:

1. Build a sanitized cell-level matrix from the four score tables:

```text
phase1_future_holdout_b_eval
phase1_future_holdout_h_future
phase1_two_repo_future_holdout_attrs_b_eval
phase1_two_repo_future_holdout_attrs_h_future
```

2. Include these fields for each cell:

```text
repo_id
split
task_id
adapter_id
terminal_status
scoreable_cell
verified_pass
verified_fail
policy_violation
harness_error
source_score_table
```

3. Join safe task metadata where available:

```text
task_time
source_context_ref
source_context_status
changed_files
test_files
candidate module/package label
selected split from frozen design
```

4. Write:

```text
experiments/phase1_compiler/results/phase1_two_repo_task_outcome_matrix.json
experiments/phase1_compiler/reports/phase1_two_repo_task_outcome_matrix.md
```

Acceptance:

- matrix has exactly `32` planned cells;
- scoreable cells count is `31`;
- policy violation count is `1`;
- the single policy violation is still
  `attrs__hist__027` / `kilo_workspace`;
- frozen design task ids still match the preregistration;
- no raw verifier logs, raw patches, prompts, completions, or transcripts are
  committed.

Commit:

```text
Build two repo task outcome matrix
```

## Step 2: Analyze Attrs H_future Failure Taxonomy

Actions:

1. Compare these groups:

```text
attrs B_eval tasks
attrs H_future tasks
boltons B_eval tasks
boltons H_future tasks
```

2. Identify whether `attrs` H_future failures are concentrated by:

```text
module/package
task type
source context kind
changed-file count
test-file count
adapter
time window
scope clarity
policy boundary
```

3. For raw verifier outcomes, use only sanitized facts:

```text
verified_pass
verified_fail
policy_violation
same task failed on both adapters
same task passed on one adapter and failed on the other
```

Do not commit hidden test names, hidden test bodies, raw stdout/stderr excerpts,
raw patches, or ACUT transcript text.

4. Write:

```text
experiments/phase1_compiler/results/phase1_attrs_h_future_failure_taxonomy.json
experiments/phase1_compiler/reports/phase1_attrs_h_future_failure_taxonomy.md
```

The report should answer these questions in plain terms:

- Is the `attrs` H_future collapse broad or tied to one task?
- Is it mostly Codex, mostly Kilo, or both?
- Is it plausibly a benchmark scope problem?
- Is it plausibly a task-family shift from B_eval to H_future?
- Does it justify more paid validation, or only more local analysis/supply?

Acceptance:

- policy violation is not converted into a scoreable fail;
- the report separates observed outcomes from interpretation;
- the report does not claim a root cause that the metadata cannot support;
- no paid calls are made.

Commit:

```text
Analyze attrs H_future failure taxonomy
```

## Step 3: Quantify Uncertainty And Baseline Error

Actions:

1. Compute Wilson 95% intervals, or another explicitly documented binomial
   interval, for:

```text
pooled B_eval pass rate
pooled H_future pass rate
boltons B_eval pass rate
boltons H_future pass rate
attrs B_eval pass rate
attrs H_future pass rate
adapter-level B_eval and H_future pass rates
```

2. Compute simple baseline prediction errors:

```text
pooled B_eval -> pooled H_future
repo-specific B_eval -> same-repo H_future
adapter-specific B_eval -> same-adapter H_future
unweighted all-B_eval predictor -> each H_future repo/adapter cell
```

3. Preserve the existing preregistered two-repo result:

```text
pooled_mae: 0.479167
policy_violation_count: 1
predictive_validity_established: false
```

4. Write:

```text
experiments/phase1_compiler/results/phase1_two_repo_uncertainty_and_baselines.json
experiments/phase1_compiler/reports/phase1_two_repo_uncertainty_and_baselines.md
```

Acceptance:

- intervals clearly show the sample-size limitation;
- baseline errors are computed from scoreable cells only;
- policy violations remain non-scoreable;
- the report states whether the pilot is negative, underpowered, or both;
- no paid calls are made.

Commit:

```text
Quantify two repo uncertainty and baseline error
```

## Step 4: Decide The Next Research Branch

Actions:

1. Use the evidence from Steps 1-3 to write:

```text
experiments/phase1_compiler/results/phase1_next_research_decision.json
experiments/phase1_compiler/reports/phase1_next_research_decision.md
```

2. Choose exactly one primary decision label:

```text
report_two_repo_negative_or_underpowered_pilot
build_weighted_compiler_analysis_before_more_paid_validation
mine_third_repo_clean_supply_without_paid_acut
blocked_pending_user_protocol_or_budget_decision
```

3. Decision rules:

Use `report_two_repo_negative_or_underpowered_pilot` if:

- the policy violation is genuine;
- the `attrs` H_future collapse remains real after taxonomy analysis;
- additional local supply is unlikely to change the immediate conclusion;
- the best next artifact is a clear research report.

Use `build_weighted_compiler_analysis_before_more_paid_validation` if:

- unweighted pass-rate comparison is too crude;
- task strata or repo profile differences plausibly explain the failure;
- a target-profile / weighting analysis can be built locally before spending
  more.

Use `mine_third_repo_clean_supply_without_paid_acut` if:

- uncertainty is dominated by having only two repos;
- another clean repo is needed to decide whether `attrs` is an outlier;
- there is a credible local-only path to clean outcome-unseen supply.

Use `blocked_pending_user_protocol_or_budget_decision` if:

- the next useful step requires paid ACUT calls;
- the next useful step requires changing the protocol;
- the worker cannot choose among branches without user input.

4. The decision report must include:

```text
main conclusion in simple language
evidence for the conclusion
strongest alternative explanation
why the chosen next branch is better than the alternatives
what must not be claimed yet
```

Acceptance:

- exactly one primary decision label is set;
- the decision is consistent with the proposal's main claim;
- the decision does not recommend rerunning the confirmed policy violation;
- the decision does not recommend paid work inside this runbook.

Commit:

```text
Decide Phase 1 next research branch
```

## Step 5A: If Reporting The Pilot, Write The Negative Or Underpowered Result

Run this step only if Step 4 selected:

```text
report_two_repo_negative_or_underpowered_pilot
```

Actions:

1. Write a concise research-facing report:

```text
experiments/phase1_compiler/reports/phase1_two_repo_negative_or_underpowered_pilot.md
experiments/phase1_compiler/results/phase1_two_repo_negative_or_underpowered_pilot.json
```

2. The report should use this structure:

```text
Question
Design
Observed result
Why predictive validity was not established
What the attrs H_future result means
What the policy violation means
Uncertainty and limits
Next recommended experiment
```

3. Keep the claim narrow:

```text
This Phase 1 pilot did not establish predictive validity. It did demonstrate
that Barcarolle can build and execute a clean two-repo validation and can report
when evidence is insufficient.
```

Acceptance:

- predictive validity remains `false`;
- production ranking remains `not_produced`;
- the report does not imply Barcarolle failed as a project, only that this pilot
  did not establish the stronger claim;
- no paid calls are made.

Commit:

```text
Report two repo negative or underpowered pilot
```

Then skip to Step 6.

## Step 5B: If Weighted Analysis Is Needed, Prepare The Compiler Analysis Plan

Run this step only if Step 4 selected:

```text
build_weighted_compiler_analysis_before_more_paid_validation
```

Actions:

1. Draft a local-only weighting/strata analysis plan:

```text
experiments/phase1_compiler/results/phase1_weighted_compiler_analysis_plan.json
experiments/phase1_compiler/reports/phase1_weighted_compiler_analysis_plan.md
```

2. Include candidate strata:

```text
repo
module/package
task type
source context kind
change size
test count
adapter sensitivity
time window
```

3. Specify at least these baselines:

```text
unweighted repo pool
repo-stratified predictor
adapter-stratified predictor
Barcarolle weighted predictor placeholder
```

4. Do not tune on H_future task outcomes to choose future H_future tasks. The
   plan may use current outcomes to diagnose why the current pilot is
   underpowered, but not to silently improve the frozen validation after the
   fact.

Acceptance:

- the plan is clearly local-only;
- it defines what data is needed before paid validation resumes;
- it does not change the existing two-repo decision;
- no paid calls are made.

Commit:

```text
Plan weighted compiler analysis before more paid validation
```

Then skip to Step 6.

## Step 5C: If Third-Repo Supply Is Needed, Screen Locally Only

Run this step only if Step 4 selected:

```text
mine_third_repo_clean_supply_without_paid_acut
```

Actions:

1. Reassess third-repo candidates from:

```text
experiments/phase0_headroom/configs/repositories.yaml
```

2. Exclude repos already used in the two-repo validation:

```text
boltons
attrs
```

3. Treat prior third-repo history carefully:

- `itsdangerous` had source-quality and hardening blockers; do not revive it
  unless the decision report explains why those blockers no longer matter.
- `toolz` has prior Phase 0 score evidence; do not reuse outcome-seen paid
  cells as clean future-holdout validation.
- `humanize` has prior diagnostic-only concerns around source provenance; use
  it only if non-leaky problem context can be established.
- `rich` and `requests` have higher environment/oracle risk; screen them only
  if simpler candidates cannot provide clean supply.

4. Write:

```text
experiments/phase1_compiler/results/phase1_third_repo_candidate_reassessment.json
experiments/phase1_compiler/reports/phase1_third_repo_candidate_reassessment.md
```

5. If one candidate is clearly best, create or update a local-only mining plan
   and, if feasible within the runbook, start deterministic mining/certification
   without paid calls. Use repo-specific artifact names and keep raw clones
   under ignored paths.

6. If local mining is started, write:

```text
experiments/phase1_compiler/results/phase1_third_repo_local_supply_decision.json
experiments/phase1_compiler/reports/phase1_third_repo_local_supply_decision.md
```

Acceptance:

- no paid ACUT or paid LLM calls are made;
- no repo already used in the two-repo validation is selected as the third repo;
- outcome-seen prior score rows are not reused as clean future-holdout evidence;
- if no candidate is strong enough, the decision says so directly;
- predictive validity remains `false`.

Commit:

```text
Screen third repo local supply candidates
```

## Step 6: Closeout And MVP Update

Actions:

1. Update:

```text
experiments/phase1_compiler/reports/phase1_attrs_generalization_process.md
```

with a simple final summary:

```text
what was analyzed
what was learned
which decision branch was selected
whether any paid calls were made
what the next runbook should do
```

2. If needed, update `phase1_compiler.py` so `phase1_mvp_closeout.json` imports
   the new next-research decision as sidecar evidence and uses it for
   `next_runbook_recommendation`.

3. Rebuild and validate the closeout:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  build-mvp \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

4. Run final checks:

```bash
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
git diff --check
git status --short
```

Acceptance:

- final decision is one of the Step 4 labels;
- no paid calls were made;
- predictive validity remains `false` unless a future runbook establishes all
  preregistered thresholds;
- production ranking remains `not_produced`;
- the closeout recommendation supersedes stale advice to rerun the confirmed
  policy violation;
- all committed artifacts are sanitized.

Commit:

```text
Record attrs generalization closeout
```

## Final Response Requirements

The executing agent's final response to the user must be in simple Chinese.
It should state:

- whether `attrs` H_future failure looks broad or narrow;
- whether uncertainty was the main blocker;
- which decision branch was selected;
- whether any third-repo local screening happened;
- whether any paid calls happened;
- final predictive-validity status;
- the next concrete runbook recommendation.
