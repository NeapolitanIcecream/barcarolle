# Phase 0 To Phase 1 Overnight Research Runbook

Status: overnight handoff runbook, 2026-05-20.

This runbook is written for one unattended Codex CLI session. Its job is to use
the measured endpoint path to push Phase 0 as far as the evidence supports, then
spend remaining time on the smallest Phase 1 compiler work that follows from
`/Users/chenmohan/Downloads/barcarolle-research-0519.md`.

The goal is not to consume the budget. The goal is to convert the overnight
window into the most defensible evidence or blocker report.

## Starting Point

The current measured Phase 0 closeout says:

- primary ACUT model: `gpt-5.4-mini`;
- endpoint path: `LLM_BASE_URL` + `LLM_API_KEY`;
- measured endpoint calls: `6`;
- measured usage observed rate: `1.0`;
- estimated endpoint spend: `USD 0.11133000`;
- measured calibration cells: `4`;
- scoreable same-repo calibration cells: `2`;
- generic comparator status: `blocked_metadata_only`;
- same-protocol `G_mini` tasks: `0`;
- final Phase 0 decision: `proceed_regression_benchmark`;
- next smallest useful experiment: `repair_generic_comparator_first`.

This runbook assumes the existing branch already contains the measured endpoint
commits. If the worker starts from a different branch or stale checkout, stop
before running paid calls and report the mismatch.

## Research Alignment

The restart proposal defines Barcarolle as a target-repository benchmark
compiler, not a task generator. The overnight work should preserve that framing.

Relevant research goals:

- Phase 0: show whether repo-specific benchmark signal is worth constructing.
- Phase 0.2: compare `G -> W_real` against `G + B_real -> W_real`.
- Phase 0.3: show a credible task-supply funnel with certification gates.
- Phase 1: produce the first MVP compiler pieces: task schema, release schema,
  target profile, stratified selection, weighting, splits, uncertainty, and
  scorecards.

Do not revive old Agent License, admission, G0-G5 authorization, or core
narrative semantics. Licensing may be mentioned only as future productization,
not as an active research objective.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-0-to-phase-1-overnight-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.

All LLM and ACUT calls must use LLM_BASE_URL + LLM_API_KEY. If either variable is
missing, source ~/.zshrc and check again. Do not use local Codex/ChatGPT
subscription auth. Do not use OPENAI_API_KEY, OPENROUTER_API_KEY, or other
provider-specific variables unless the user's shell explicitly maps them into
LLM_API_KEY.

Do not print or commit secrets, full prompts, raw completions, raw transcripts,
cloned repositories, .venv, caches, or workspaces. Store raw model responses only
under ignored raw paths and commit sanitized summaries.

Start by checking the current measured Phase 0 artifacts. Then follow the
decision tree in this runbook:

1. Repair the generic comparator protocol if feasible.
2. If at least three G_mini tasks become same-protocol scoreable, run a measured
   expanded matrix under the endpoint model.
3. If G_mini cannot be repaired within the bounded attempt, write a precise
   blocker report and switch to task-supply expansion plus Phase 1 compiler
   skeleton work.
4. Commit cohesive checkpoints after each completed work package.

Run tests and git hygiene before every commit:

  git diff --check
  uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools

End by writing an overnight report that says what was completed, what branch was
taken, measured spend, remaining blockers, and the next smallest useful runbook.
```

## Budget And Runtime Rules

The measured endpoint cost is low enough to justify controlled scale-up, but the
overnight run is unattended, so keep strict caps.

Budget caps:

- overnight soft cap: `USD 25` estimated or observed endpoint spend;
- overnight hard cap: `USD 60`;
- original Phase 0 absolute hard cap: `USD 200`;
- stop before any batch whose projected cumulative overnight spend exceeds
  `USD 40`;
- stop and leave a report before any batch that would exceed `USD 60`.

Batch rules:

- Record a projected-cost ledger row before every paid ACUT batch.
- Record observed token usage and estimated cost after every paid call.
- Do not run parallel paid ACUT batches.
- Do not use LLM calls for deterministic CSV, JSON, metric, or report formatting.
- Prefer small sequential batches that can change the research decision.
- If endpoint usage is no longer reported, stop paid scale-up after one smoke
  batch and report `usage_observed_regressed`.

Scale guidance:

- The prior measured calibration used `4` task-solving cells and cost roughly
  `USD 0.111` including smoke calls.
- The overnight window may run roughly `4x` to `6x` that cell count when the
  protocol is valid.
- A reasonable target is `16` to `24` paid task-solving cells total, not hundreds
  of cells. Time and certification quality are the limiting resources.

## Output Layout

Reuse the current Phase 0 layout for Phase 0 artifacts:

```text
experiments/phase0_headroom/
  configs/
  candidate_sources/
  certified_tasks/
  releases/
  results/
  reports/
  target_profiles/
  tools/
```

Create these overnight-specific summaries:

```text
experiments/phase0_headroom/
  reports/
    overnight_research_process.md
    overnight_research_report.md
  results/
    overnight_research_decision.json
```

If Phase 1 compiler work starts, create a separate minimal workspace:

```text
experiments/phase1_compiler/
  pyproject.toml
  README.md
  schemas/
  tools/
  tests/
  reports/
  results/
```

Use `uv` for the Phase 1 workspace as well. Keep schemas and tools small.

## Step 0: Preflight And Evidence Sync

Actions:

1. Record branch, HEAD, current date, Python version, `uv --version`, and status.
2. Confirm the current measured endpoint artifacts exist:
   - `configs/endpoint.yaml`
   - `configs/model_selection.yaml`
   - `results/measured_cost_ledger.jsonl`
   - `results/measured_cost_summary.json`
   - `results/cost_realignment.json`
   - `reports/phase0_decision_memo.md`
3. Confirm no raw artifacts are tracked:

```bash
git ls-files experiments/phase0_headroom/results/raw \
  experiments/phase0_headroom/.venv \
  experiments/phase0_headroom/workspaces \
  experiments/phase0_headroom/external_repos \
  experiments/phase0_headroom/tools/__pycache__
```

4. Run:

```bash
git status --short --ignored experiments/phase0_headroom docs/experiments .gitignore
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
```

5. Create or update `reports/overnight_research_process.md`.

Acceptance:

- scoped tests pass;
- the worker can identify the current measured cost summary;
- raw artifacts are ignored and unstaged;
- endpoint fallback remains disabled.

Stop if:

- `LLM_BASE_URL` or `LLM_API_KEY` is missing after sourcing `~/.zshrc`;
- the branch does not contain the measured endpoint run;
- unexplained uncommitted changes touch certification, release, or result files.

## Step 1: Remove Immediate Ambiguity

Before research work, fix small inconsistencies that could mislead later stages.

Actions:

1. Check whether `configs/headroom_matrix.yaml` still describes the old Codex
   CLI matrix. If yes, either mark it as historical/default-disabled or write a
   separate measured-endpoint matrix config. Do not let a future worker mistake
   the old Codex CLI path for the active measured endpoint path.
2. Verify `reports/phase0_decision_memo.md` points to the measured endpoint
   ledger and says `G_mini` is blocked.
3. Verify `results/headroom_matrix.json` and `results/headroom_score_table.csv`
   reflect the measured endpoint calibration, not the old Codex CLI run.

Acceptance:

- active measured endpoint artifacts are unambiguous;
- old Codex CLI artifacts may remain for historical continuity, but are clearly
  non-canonical for future paid runs.

Commit after this step if files changed:

```text
Clarify active measured endpoint Phase 0 artifacts
```

## Step 2: Bounded Generic Comparator Repair

This is the highest-priority Phase 0 blocker.

Objective:

Materialize at least `3` `G_mini` comparator tasks as Phase 0-compatible,
same-protocol task packages. Archived Click records may be used as source
material, but the active task packages must stand on their own.

Required active package fields:

```text
task_id
repo_id
source_type
base_commit
task_time
solver_facing_statement
base_checkout_or_workspace_recipe
oracle_command
reference_patch_or_reference_behavior
known_bad_patch_or_failure_mode
leakage_review
ambiguity_review
scope_review
cost_bound
feature_taxonomy
scoreability_status
```

Actions:

1. Inventory all archived Click `G_mini` metadata currently referenced by:
   - `target_profiles/click_archive_generic_profile.json`
   - `results/generic_comparator_protocol.json`
   - prior archived docs or workflow notes, only as metadata.
2. For each candidate, try to recover or reconstruct:
   - base commit;
   - reference change;
   - issue or PR context sufficient for a solver-facing statement;
   - hidden verifier command;
   - no-op fail, reference pass, known-bad fail, and flakiness evidence.
3. If deterministic recovery is possible, create active manifests under
   `experiments/phase0_headroom/generic_comparator/`.
4. Run the same dry-run protocol as the `toolz` tasks:
   - checkout/build;
   - no-op/reference/known-bad;
   - flakiness;
   - leakage;
   - ambiguity;
   - scope clarity;
   - cost boundedness;
   - feature taxonomy.
5. Update:
   - `results/generic_comparator_protocol.json`
   - `reports/generic_comparator_protocol.md`
   - `results/overnight_research_decision.json`

Use LLM calls only for statement drafting or ambiguity review when deterministic
source context exists. Do not spend model calls trying to guess missing commits,
patches, or oracle commands.

Acceptance:

- `>= 3` comparator tasks are `scoreable_same_protocol`; or
- the report explains precisely why materialization failed for each candidate.

Stop this step and switch branches if:

- no candidate has recoverable base commit and oracle material;
- repair would require reviving Agent License or old G0-G5 semantics;
- more than `2` hours of deterministic recovery produces `0` scoreable tasks;
- the projected LLM spend for this step exceeds `USD 5` without a scoreable
  candidate.

Commit after this step:

```text
Repair generic comparator protocol
```

or:

```text
Document generic comparator materialization blocker
```

## Step 3A: If Generic Comparator Repair Succeeds

Take this branch only if Step 2 produced at least `3`
`scoreable_same_protocol` `G_mini` tasks.

Objective:

Run a measured, same-protocol Phase 0 matrix large enough to evaluate whether
repo-specific signal is worth the next phase, while staying under the overnight
budget.

Matrix A: primary endpoint ACUT

- model/config: current primary `gpt-5.4-mini`;
- tasks:
  - all `6` certified `toolz` tasks, unless the existing measured calibration
    can be reused without mixing incompatible prompts;
  - `3` or `4` same-protocol `G_mini` tasks;
- expected cells: `9` to `10`.

If the previous four measured `toolz` cells used the same prompt, runner, output
contract, and verifier protocol, reuse them and run only missing cells. If the
runner or output contract changed, mark prior cells as calibration-only and run a
fresh consistent matrix.

Output-contract repair:

- If invalid patch output remains above `25%`, add a small output-contract
  repair prompt/config before adding a second model.
- Compare `generic_prompt` vs `output_contract_repair` on a `4` to `6` cell
  subset before scaling.

Optional Matrix B: paired configuration

Run only if Matrix A completes, generic comparator cells are scoreable, and
projected cumulative overnight spend remains below `USD 25`.

Prefer a paired configuration over a simple strong-vs-weak model contrast:

- same model + stricter patch output contract;
- same model + repo task-statement context packaging;
- same model + local test command reminder.

Run `6` to `10` additional cells. This is a small Phase 2 preview, not a final
residual predictive-validity experiment.

Actions:

1. Write or update a measured endpoint matrix config.
2. Append projected-cost rows before each paid batch.
3. Run ACUT calls through the measured endpoint runner.
4. Verify every submission.
5. Separate:
   - `verified_pass`
   - `verified_fail`
   - `invalid_output`
   - `harness_error`
   - `timeout`
6. Compute:
   - split pass rates;
   - invalid-output rate;
   - scoreable cell count;
   - cost per submitted cell;
   - cost per scoreable cell;
   - median latency;
   - `G_mini -> W_real` availability;
   - `G_mini + B_real -> W_real` availability.
7. Mark predictive metrics as `not_applicable_underpowered` unless the sample
   size and predictor setup justify them.

Acceptance:

- every scheduled cell has a terminal status;
- `G_mini` cells are reported only when same-protocol scoreable;
- the final report states whether Phase 0 can now move from
  `proceed_regression_benchmark` toward `proceed_predictive` or remains
  diagnostic.

Stop if:

- harness errors dominate the first `4` comparator cells;
- invalid output remains above `50%` after one output-contract repair attempt;
- cost usage is not observed;
- projected overnight spend exceeds `USD 40`.

Commit after each cohesive batch:

```text
Run measured endpoint comparator matrix
```

```text
Evaluate output contract repair configuration
```

## Step 3B: If Generic Comparator Repair Remains Blocked

Take this branch if Step 2 cannot produce at least `3`
`scoreable_same_protocol` comparator tasks.

Objective:

Do not spend the night repeatedly attacking the same blocked comparator. Convert
the time into Phase 0.3 task-supply evidence and Phase 1 compiler foundations.

Actions:

1. Write a precise comparator blocker:
   - what metadata exists;
   - what base checkout/oracle/statement material is missing;
   - what would be needed to make it same-protocol;
   - whether the blocker is Click-specific or generic.
2. Expand certified same-repo supply for `toolz` if feasible:
   - target: `12` certified tasks total;
   - minimum useful increment: `+3` certified tasks;
   - include all certification gates from the research proposal:
     - checkout/build;
     - oracle extract;
     - no-op fail;
     - reference pass;
     - known-bad fail;
     - flakiness;
     - ambiguity;
     - solution leakage;
     - scope clarity;
     - cost boundedness;
     - feature taxonomy.
3. If `toolz` is exhausted or the next `toolz` tasks are low quality, start one
   backup repo supply funnel. Prefer a repo already present in local artifacts
   such as `humanize`; do not add more than one new repo overnight.
4. Create a task-supply report that makes rejection reasons first-class data.
5. Run at most a small measured ACUT harness smoke on newly certified tasks:
   - `2` to `4` cells;
   - only if it tests harness robustness or output-contract repair;
   - do not claim predictive validity from it.

Acceptance:

- either `+3` or more new certified tasks exist, or the report explains why the
  source is exhausted;
- rejection reasons include the full certification gate vocabulary;
- no paid scale-up is run merely because measured cost is cheap.

Commit after this branch:

```text
Expand Phase 0 task supply funnel
```

or:

```text
Document Phase 0 task supply blocker
```

## Step 4: Phase 1 Compiler Skeleton

Start this step after one of the following:

- Step 3A completed Matrix A; or
- Step 3B produced a precise comparator blocker and at least one task-supply
  improvement or exhaustion report.

Objective:

Create the smallest useful Phase 1 skeleton without pretending Phase 1
validation is complete.

Actions:

1. Initialize `experiments/phase1_compiler/` with `uv`.
2. Add typed schemas or dataclasses for:
   - task manifest;
   - release manifest;
   - target profile;
   - certification report;
   - agent run manifest;
   - scorecard;
   - weighted score summary.
3. Add a converter that imports the current `toolz` Phase 0 mini release into a
   draft Phase 1 release format.
4. Add a simple stratified weighting module:
   - use current target profile strata when available;
   - mark strata with insufficient evidence explicitly;
   - produce a weighted score only when task outcomes are compatible.
5. Add tests for schema validation and weighted score computation.
6. Write:
   - `experiments/phase1_compiler/README.md`
   - `experiments/phase1_compiler/reports/compiler_skeleton_report.md`

Acceptance:

- `uv run --project experiments/phase1_compiler pytest -q` passes;
- the skeleton can import the current Phase 0 release into a draft release
  manifest;
- missing evidence is represented as `insufficient_evidence`, not silently
  filled;
- the report clearly distinguishes implemented skeleton from future Phase 1
  predictive validation.

Commit after this step:

```text
Initialize Phase 1 compiler skeleton
```

## Step 5: Optional Phase 1 Preview

Do this only if Steps 2-4 are clean and there is still time.

Objective:

Produce one small analysis that connects the overnight work to the restart
proposal's next-stage claims.

Allowed previews:

- compare unweighted vs target-profile weighted score aggregation on the current
  same-repo outcomes;
- generate dev/eval/canary split candidates for `toolz`;
- compute bootstrap or beta-binomial uncertainty for the current scoreable
  cells;
- draft a residual-predictive-validity experiment design for multiple ACUT
  configurations without running paid cells.

Do not run broad multi-ACUT residual validation overnight unless:

- same-protocol `G_mini` exists;
- Matrix A completed cleanly;
- the planned cells are at most `10`;
- projected cumulative spend remains below `USD 25`;
- the result answers a concrete comparison, not a leaderboard question.

Commit if a preview artifact is produced:

```text
Add Phase 1 predictive-validation preview
```

## Step 6: Final Overnight Closeout

Actions:

1. Update:
   - `reports/overnight_research_report.md`
   - `results/overnight_research_decision.json`
   - `reports/phase0_decision_memo.md`
   - `reports/measured_cost_report.md`, if paid calls were run
   - `reports/headroom_analysis.md`, if matrix outcomes changed
2. The overnight report must include:
   - branch and HEAD commits;
   - chosen branch: `generic_comparator_repaired`,
     `generic_comparator_blocked_supply_expanded`,
     `generic_comparator_blocked_phase1_skeleton`, or `stopped`;
   - artifacts changed;
   - measured and estimated cost;
   - task/cell counts;
   - scoreable vs invalid/harness-error counts;
   - certification yield and rejection reasons;
   - whether Phase 0 decision changed;
   - whether Phase 1 skeleton exists;
   - next smallest useful runbook.
3. Run:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
test ! -d experiments/phase1_compiler || uv run --project experiments/phase1_compiler pytest -q
git status --short --ignored experiments/phase0_headroom experiments/phase1_compiler docs/experiments .gitignore
```

4. Confirm no raw paths, prompts, responses, workspaces, cloned repos, `.venv`,
   or caches are staged.
5. Commit final report if it was not already included.

Final commit message:

```text
Summarize overnight Phase 0 and Phase 1 research
```

Do not push unless the user explicitly asked the worker to push.

## Decision Outcomes

Use these exact decision names in `results/overnight_research_decision.json`:

```text
generic_comparator_repaired
generic_comparator_blocked_supply_expanded
generic_comparator_blocked_phase1_skeleton
same_repo_supply_expanded
phase1_skeleton_initialized
stopped_missing_endpoint
stopped_dirty_worktree
stopped_budget_risk
stopped_harness_regression
stopped_no_scoreable_work_remaining
```

## Dawn Success Criteria

The overnight run is successful if it produces one of these defensible outcomes:

1. Best case:
   - at least `3` same-protocol `G_mini` tasks;
   - measured endpoint matrix across `B_real`, `W_real`, and `G_mini`;
   - updated Phase 0 decision memo;
   - cost and scorecard artifacts.

2. Good fallback:
   - precise generic-comparator blocker;
   - expanded certified task supply or a second repo funnel;
   - full rejection reasons for failed candidates;
   - Phase 1 compiler skeleton initialized.

3. Acceptable stop:
   - no unsafe spend;
   - no secret or raw artifact committed;
   - tests pass;
   - the report explains the blocker and the next smallest useful runbook.

Do not end with only raw logs. The final state must be a committed, reviewable
research artifact.
