# Phase 1 Click LLM-Assisted Source-Context Repair Runbook

Status: implementation runbook, 2026-05-29.

This runbook is for one dedicated Codex CLI session. Its job is narrow:

```text
Repair or augment the solver-visible source context and task statements for the
current click third-repo supply, using public context first and tightly
controlled LLM assistance only where needed.
```

Plain-language summary:

```text
The current three-repo Phase 1 pilot uses attrs, boltons, and click. Click
solved the third-repo supply gate, but all current click tasks carry a
title-only / minor-risk source-context caveat.

That caveat is acceptable for exploratory evidence if it is visible. It is not
ideal for a cleaner three-repo research claim. This runbook tests whether the
click supply can be upgraded with public context and reviewed LLM-assisted
statements without changing completed paid outcomes or turning Barcarolle into
a general task generator.
```

## Execution Boundary

This runbook may make paid LLM statement-generation or statement-review calls
only if endpoint compliance is proven and the cost cap below is respected.

Paid ACUT solver cells are disabled.

Allowed work:

- read committed candidate, source-context, statement, split, score-table,
  fairness, and diagnostic artifacts;
- inspect public click repository metadata, issues, pull requests, commits,
  changelogs, and release notes;
- build sanitized candidate packets for all current click release-eligible
  tasks or for a predeclared outcome-blind sample if the LLM budget is too low;
- use LLMs for statement drafting, source-context augmentation, ambiguity
  review, and leakage/sufficiency review when the prompt inputs are sanitized;
- write small sanitized configs, tools, tests, JSON/CSV outputs, reports,
  statement packets, review records, overlays, manifests, and a decision;
- use completed paid outcomes only after the source-quality decision is frozen,
  and only to explain exploratory traction or remaining limitations.

Disallowed work:

- running any new paid ACUT solver cell;
- rerunning failed, invalid, disagreeing, or high-gap cells;
- changing any completed paid terminal outcome, score table, selected task ID,
  split assignment, source eligibility, task statement, completed decision, or
  threshold;
- using paid outcomes, adapter outcomes, B_eval/H_future labels, or failure
  labels to decide which click tasks get repaired, promoted, rejected, or
  sampled;
- exposing hidden oracle material, raw target patches, raw test patches, exact
  hidden assertions, or target commit hashes in solver-visible statements;
- counting a generated or repaired statement as release-quality before it has
  provenance, leakage, ambiguity, and sufficiency review evidence;
- adopting SWE-Bench++, SWE-smith, R2E-Gym, or another external system as a
  default generator in this runbook;
- claiming formal preregistration, predictive validity, or clean three-repo
  validation from this repair run;
- committing raw prompts, raw completions, raw LLM transcripts, raw Codex/Kilo
  logs, ACUT transcripts, solver workspaces, verifier workspaces, raw diffs,
  raw test patches, target repository clones, raw public API responses, secrets,
  `.venv`, caches, or large raw outputs;
- drafting or creating the next runbook.

If exact evidence requires ignored raw artifacts, record the limitation. Do not
recover or commit raw sensitive artifacts unless an existing repo policy already
allows a sanitized digest.

## Endpoint And Budget Rules

All paid LLM calls in this runbook must use:

```text
LLM_BASE_URL
LLM_API_KEY
```

If either variable is missing in the worker shell, source `~/.zshrc` and check
again before making any model call. Do not fall back to local Codex/ChatGPT
subscription auth, `OPENAI_API_KEY`, OpenRouter variables, or provider-specific
variables unless the user explicitly updates this rule.

Default caps:

```text
paid ACUT solver cells: 0
paid task-solving calls: 0
paid LLM statement generation/review soft cap: USD 15 token-estimated
paid LLM statement generation/review hard cap: USD 25 token-estimated
full click task target: 30 tasks
minimum smoke before full LLM batch: 3 tasks
```

If cost accounting is unavailable, run at most the 3-task smoke and stop before
the full LLM branch with a blocker report. If the full 30-task branch would
exceed the hard cap, build a deterministic outcome-blind sample that preserves
task-family coverage and record the unprocessed tasks as remaining work.

## Starting Point

The current Phase 1 state is:

```text
research phase goal:
  traction evidence, narrative validation, and project/proposal support

predictive validity:
  not established

mainline paid-reporting baseline:
  repo_stratified / simple stratified until stronger local evidence exists

algorithm exploration:
  open, but candidate designs must be labeled and compared with baselines

adapter comparison:
  Kilo/Codex differences are ACUT configuration results if benchmark-side
  endpoint, task, workspace, verifier, policy, and accounting checks are clean
```

Relevant completed evidence:

```text
three-repo paid package:
  attrs release eligible:   31
  boltons release eligible: 35
  click release eligible:   30
  click source caveat: title-only / minor-risk

blocked split supplement:
  selected cells: 120 / 120
  scoreable cells: 119
  policy violations: 0
  raw oracle exposure: false
  endpoint compliance: pass
  predictive validity established: false

latest fairness diagnostic:
  adapter fairness: fair_enough_to_interpret_as_acut_difference
  endpoint/model/config evidence: clean
  more paid cells recommended now: false
```

This runbook should answer:

```text
Can click remain the third repo with a cleaner source-quality story after
public-context and LLM-assisted statement repair, or should future work replace
click before making a clean three-repo claim?
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-click-llm-assisted-source-context-repair-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md and PROCESS.md first.
Use uv for repo-local Python tooling. Follow AGENTS.md step-level acceptance and
commit requirements: after each step, or after a small group of tightly related
steps, commit the changed files with an appropriately scoped commit.

Main goal: repair or augment source context and solver-visible statements for
the current click release-eligible supply. Use public context first. Use paid
LLM statement generation/review only through LLM_BASE_URL and LLM_API_KEY, only
after endpoint and cost preflight pass, and only for sanitized packets.

Do not run paid ACUT solver cells. Do not rerun completed cells. Do not change
paid outcomes, score tables, selected task IDs, split labels, source
eligibility, or completed decisions. Do not use paid outcomes or adapter
outcomes to decide which click tasks are promoted or sampled.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. Whether click is cleaner, still usable only with a caveat, or should be
   replaced before a clean three-repo claim.

Do not commit secrets, raw prompts, raw completions, raw LLM transcripts, raw
Codex/Kilo logs, ACUT transcripts, solver workspaces, verifier workspaces,
target repo clones, raw public API responses, raw target diffs, raw test
patches, .venv, caches, or large raw outputs. Commit only small sanitized
configs, tools, tests, packets, review records, tables, reports, manifests,
digests, and decision files.

Do not draft or create the next runbook. Record recommended next action
categories only.
```

## Required Inputs

Use these committed inputs when present:

```text
AGENTS.md
PROCESS.md
docs/architecture/system-design.md
docs/experiments/phase-1-task-supply-v2-generator-bakeoff-runbook.md
docs/experiments/phase-1-source-context-statement-hardening-runbook.md
docs/experiments/phase-1-attrs-source-repair-runbook.md
docs/experiments/phase-1-diff-assisted-statement-regeneration-runbook.md
docs/experiments/phase-1-blocked-split-redesign-runbook.md
docs/experiments/phase-1-blocked-split-supplement-fairness-and-gap-diagnostics-runbook.md

experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_source_context_inventory.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_supply_snapshot.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_task_table.json
experiments/phase1_compiler/results/phase1_three_repo_paid_readiness_packaging_source_quality_audit.json
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_inventory.json
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_overlay.json
experiments/phase1_compiler/results/phase1_source_context_statement_hardening_split_feature_table.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_candidate_universe.json
experiments/phase1_compiler/results/phase1_blocked_split_redesign_selected_split.json
experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_selected_split_plan.json
experiments/phase1_compiler/results/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.json

experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md
experiments/phase1_compiler/reports/phase1_source_context_statement_hardening_decision.md
experiments/phase1_compiler/reports/phase1_blocked_split_redesign_decision.md
experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md
experiments/phase1_compiler/reports/phase1_diff_assisted_codex_loop_recovery_decision.md
```

Useful implementation references:

```text
experiments/phase1_compiler/tools/phase1_task_supply_v2_generator_bakeoff.py
experiments/phase1_compiler/tools/phase1_source_context_statement_hardening.py
experiments/phase1_compiler/tools/phase1_attrs_source_repair.py
experiments/phase1_compiler/tools/phase1_diff_assisted_codex_loop_statement_regeneration.py
experiments/phase1_compiler/tools/statement_quality.py
experiments/phase1_compiler/tests/test_phase1_source_context_statement_hardening.py
experiments/phase1_compiler/tests/test_phase1_attrs_source_repair.py
```

If an input is missing or has moved, record that in the preflight report and
continue with available committed artifacts.

## Output Layout

Create a new run under this prefix:

```text
phase1_click_llm_source_context_repair
```

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_click_llm_source_context_repair.yaml
  tools/
    phase1_click_llm_source_context_repair.py
  tests/
    test_phase1_click_llm_source_context_repair.py
  results/
    phase1_click_llm_source_context_repair_preflight.json
    phase1_click_llm_source_context_repair_click_inventory.json
    phase1_click_llm_source_context_repair_public_context_review.json
    phase1_click_llm_source_context_repair_llm_packet_plan.json
    phase1_click_llm_source_context_repair_llm_smoke.json
    phase1_click_llm_source_context_repair_statement_packets.json
    phase1_click_llm_source_context_repair_review_records.json
    phase1_click_llm_source_context_repair_quality_overlay.json
    phase1_click_llm_source_context_repair_claim_boundary.json
    phase1_click_llm_source_context_repair_decision.json
  reports/
    phase1_click_llm_source_context_repair_process.md
    phase1_click_llm_source_context_repair_click_inventory.md
    phase1_click_llm_source_context_repair_public_context_review.md
    phase1_click_llm_source_context_repair_llm_packet_plan.md
    phase1_click_llm_source_context_repair_statement_review.md
    phase1_click_llm_source_context_repair_quality_overlay.md
    phase1_click_llm_source_context_repair_decision.md
```

Optional small CSV outputs may be added if useful:

```text
experiments/phase1_compiler/results/phase1_click_llm_source_context_repair_*.csv
```

Allowed ignored outputs:

```text
experiments/phase1_compiler/tmp/click_llm_source_context_repair/
experiments/phase0_headroom/workspaces/click_llm_source_context_repair/
experiments/phase0_headroom/cache/click_llm_source_context_repair/
```

Committed artifacts must contain sanitized metadata, short summaries, hashes,
model/config identifiers without secrets, prompt/completion digests, and review
verdicts only.

## Definitions

Use these terms consistently:

```text
technical_certified:
  A task has already passed local benchmark-side certification gates.

release_eligible:
  A task is technical certified and has acceptable solver-visible source
  context, statement provenance, leakage status, ambiguity status, and scope
  clarity.

title_only_minor_risk:
  The current click status: the task is usable for exploratory work but source
  context is too thin for a clean-source claim.

public_context_repaired:
  The task moved from title-only context to a non-leaky public issue, PR,
  changelog, release note, or commit-body context sufficient for a
  solver-visible statement.

llm_assisted_statement_repaired:
  The task still lacks enough public natural-language context, but a
  solver-visible statement was generated or rewritten from a sanitized packet
  and then passed leakage, ambiguity, and sufficiency review.

clean_source_candidate:
  The task has either public_context_repaired or
  llm_assisted_statement_repaired status and no remaining major leakage,
  ambiguity, or scope blocker.
```

## Diagnostic Policy

The worker should codify this policy in outputs:

1. Click title-only source quality is a claim-boundary caveat, not proof that
   past paid results are invalid.
2. Adapter differences are not a blocker by themselves; the latest diagnostic
   already found the supplement fair enough to interpret as ACUT configuration
   evidence.
3. Source repair must be outcome-blind. Task outcomes can be joined only after
   repair decisions are frozen, and only for exploratory interpretation.
4. LLM-generated or LLM-reviewed text is allowed only as sanitized sidecar
   evidence. It does not change historical paid results.
5. A generated statement must not expose hidden oracle material or raw target
   patches, and it must not contain direct implementation recipes.
6. If LLM assistance improves click source quality, report it as traction
   evidence for Barcarolle's supply/compiler workflow, not as predictive
   validity.
7. If click cannot be repaired enough, recommend replacement or broader supply
   mining without treating the earlier exploratory supplement as unfair.

## Step 0 - Preflight And Scope Check

Goal: prove the run is scoped to click source-quality repair and cannot change
completed paid outcomes.

Actions:

1. Read `AGENTS.md`, `PROCESS.md`, this runbook, and the required input
   artifacts.
2. Record branch, HEAD, date, Python version, `uv --version`, and whether
   `LLM_BASE_URL` / `LLM_API_KEY` are present without printing values.
3. Record `git status --short --untracked-files=all` and `git diff --check`.
4. Classify dirty/untracked files. The known external-review bundle may remain
   untracked unless the user explicitly asks to package or remove it.
5. Confirm no paid ACUT solver cells are allowed.
6. Confirm completed paid outcomes, score tables, split labels, task IDs, and
   completed decisions will not be changed.
7. Write preflight result and process report.

Acceptance:

- Preflight records branch, HEAD, dirty-tree classification, endpoint-variable
  presence, cost-boundary status, and required input availability.
- No paid calls have run.
- The report says source repair is outcome-blind and does not modify completed
  paid results.

Suggested commit:

```text
Record click source repair preflight
```

## Step 1 - Click Candidate Inventory

Goal: freeze the click task universe and outcome-blind processing order.

Actions:

1. Load the current click release-eligible rows from committed packaging,
   source-hardening, and blocked-split artifacts.
2. Verify the expected count is 30 click tasks and that all carry the
   title-only/minor-risk caveat, or record the exact difference.
3. Build an outcome-blind task table with:
   - task id;
   - source reservoir;
   - public anchor type;
   - title / short public summary digest;
   - file path buckets;
   - task-family bucket;
   - time bucket;
   - editable scope bucket;
   - statement digest;
   - existing source-quality bucket;
   - existing leakage/ambiguity bucket.
4. Do not load paid outcomes, adapter outcomes, B_eval/H_future outcome labels,
   or failure labels before freezing the inventory.
5. Freeze the processing order lexicographically by task id, with optional
   secondary grouping by task-family for budgeted sampling.

Expected outputs:

```text
phase1_click_llm_source_context_repair_click_inventory.json
phase1_click_llm_source_context_repair_click_inventory.md
```

Acceptance:

- The inventory can be reproduced from committed artifacts.
- Outcome fields are absent from the inventory.
- The report states how many click tasks are in scope and whether all are still
  title-only/minor-risk.

Suggested commit:

```text
Inventory click source repair candidates
```

## Step 2 - Public Context Recovery

Goal: repair as much click source context as possible without model calls.

Actions:

1. For every in-scope click task, search committed metadata and public click
   history for non-leaky context:
   - public issue;
   - public pull request;
   - commit body;
   - changelog entry;
   - release note;
   - documentation reference.
2. Store only short sanitized summaries and stable public references or digests.
   Do not commit full raw public API responses.
3. Classify each task:
   - `accepted_public_context`;
   - `insufficient_public_context`;
   - `rejected_leaky_public_context`;
   - `missing_public_context_evidence`.
4. Draft revised solver-visible source-context summaries only for tasks with
   accepted public context.
5. Run deterministic leakage and ambiguity checks from existing statement
   quality tooling where available.

Expected outputs:

```text
phase1_click_llm_source_context_repair_public_context_review.json
phase1_click_llm_source_context_repair_public_context_review.md
```

Acceptance:

- Every task has a public-context verdict.
- The report states how many click tasks can be repaired without LLM calls.
- No raw public API payloads, raw diffs, or raw test patches are committed.

Suggested commit:

```text
Review click public source context
```

## Step 3 - LLM Packet Plan And Cost Gate

Goal: decide whether to run the LLM branch and define exactly what it may see.

Actions:

1. Select tasks for LLM assistance from the `insufficient_public_context` or
   `missing_public_context_evidence` set only. Selection must be outcome-blind.
2. If the full set fits under the hard cap, plan all remaining tasks.
3. If the full set does not fit, plan:
   - a 3-task smoke sample; then
   - a deterministic task-family-covered sample if the smoke succeeds.
4. Build sanitized packets containing only:
   - task id;
   - repo name;
   - public title or short public context summary;
   - commit subject/body summary when available;
   - implementation file paths;
   - test file paths;
   - behavior-level changed-test summary;
   - behavior-level touched-API summary;
   - source-quality and ambiguity-risk labels;
   - short digests of target/test changes.
5. Exclude:
   - raw target patch;
   - raw hidden test patch;
   - exact added assertions copied into the statement;
   - target commit hash in the solver statement;
   - direct implementation recipe;
   - paid outcomes or adapter outcomes.
6. Estimate token cost and stop before model calls if endpoint compliance or
   cost accounting cannot be proven.

Expected outputs:

```text
phase1_click_llm_source_context_repair_llm_packet_plan.json
phase1_click_llm_source_context_repair_llm_packet_plan.md
```

Acceptance:

- The packet plan names the selected tasks and why the selection is
  outcome-blind.
- Endpoint and cost gates are explicit.
- No model call has run unless the gate passes.

Suggested commit:

```text
Plan click LLM repair packets
```

## Step 4 - Endpoint-Compliant LLM Statement Generation And Review

Goal: use LLM assistance only for sanitized statement repair, then independently
review the result.

Actions:

1. Run the 3-task smoke first if any paid LLM calls are needed.
2. Use an endpoint-compliant wrapper or script that records:
   - endpoint variables were present;
   - model/config id without secrets;
   - prompt template digest;
   - completion digest;
   - generated statement id;
   - token-estimated cost;
   - ignored raw prompt/completion storage path, if retained.
3. Generate or rewrite solver-visible statements from sanitized packets only.
4. Review every generated statement. Prefer a separate prompt/template or
   separate reviewer invocation. The review must classify:
   - leakage status;
   - ambiguity status;
   - scope clarity;
   - source sufficiency;
   - whether the statement includes an implementation recipe;
   - final release-quality recommendation.
5. If the smoke fails endpoint, cost, schema, leakage, or quality gates, stop
   the full LLM branch and write the blocker.
6. If the smoke passes and cost allows, continue through the planned task set.

Expected outputs:

```text
phase1_click_llm_source_context_repair_llm_smoke.json
phase1_click_llm_source_context_repair_statement_packets.json
phase1_click_llm_source_context_repair_review_records.json
phase1_click_llm_source_context_repair_statement_review.md
```

Acceptance:

- No paid ACUT solver cells run.
- All paid LLM calls use `LLM_BASE_URL` and `LLM_API_KEY`.
- Raw prompts and raw completions are not committed.
- Every generated statement has a review record before it can count as
  repaired.

Suggested commit:

```text
Run click LLM statement repair
```

If no paid LLM calls run because the gate blocks, use:

```text
Record click LLM repair blocker
```

## Step 5 - Quality Overlay And Claim Boundary

Goal: recompute click source-quality status without rewriting historical
artifacts.

Actions:

1. Build an overlay with one row per click task:
   - previous source-quality bucket;
   - public-context verdict;
   - LLM-assisted repair verdict, if any;
   - final source-quality bucket;
   - release-quality recommendation;
   - leakage/ambiguity/scope labels;
   - statement digest;
   - provenance class.
2. Compute:
   - tasks upgraded from title-only/minor-risk to clean or cleaner source;
   - tasks still requiring caveats;
   - tasks rejected or blocked;
   - remaining title-only share;
   - source reservoir diversity;
   - whether click still satisfies the 30-task third-repo gate under each claim
     boundary.
3. Define claim-boundary labels:
   - `click_clean_enough_for_three_repo_claim`;
   - `click_usable_with_visible_caveat`;
   - `click_repair_partial_needs_more_supply`;
   - `click_should_be_replaced_for_clean_claim`.
4. Only after the overlay is frozen, optionally join completed outcome summaries
   to discuss exploratory traction. Do not use outcomes to change overlay
   verdicts.
5. Update `PROCESS.md` only if the run changes the active source-quality
   boundary, paid/no-paid boundary, or recommended next action category.

Expected outputs:

```text
phase1_click_llm_source_context_repair_quality_overlay.json
phase1_click_llm_source_context_repair_claim_boundary.json
phase1_click_llm_source_context_repair_quality_overlay.md
```

Acceptance:

- The overlay does not rewrite historical certification or paid results.
- The claim boundary is explicit and conservative.
- Any outcome join is clearly labeled post-decision diagnostic context.

Suggested commit:

```text
Overlay click source repair quality
```

## Step 6 - Decision And Closeout

Goal: turn the repair evidence into the next action category.

Actions:

1. Write a decision report with:
   - LLM calls run or blocked;
   - token-estimated LLM cost;
   - public-context repair count;
   - LLM-assisted repair count;
   - final click claim-boundary label;
   - whether click can support a cleaner three-repo story;
   - whether future paid ACUT cells remain blocked;
   - whether `PROCESS.md` was updated.
2. Choose one primary decision label:

```text
click_source_repair_clean_enough_for_three_repo_claim
click_source_repair_usable_with_visible_caveat
click_source_repair_partial_needs_more_supply
click_source_repair_blocked_by_endpoint_or_cost
click_source_repair_should_replace_click_for_clean_claim
```

3. Record recommended next action categories only. Do not draft or create the
   next runbook.
4. Run focused tests and `git diff --check`.

Expected outputs:

```text
phase1_click_llm_source_context_repair_decision.json
phase1_click_llm_source_context_repair_decision.md
```

Acceptance:

- The decision states whether the run produced traction evidence, clean-source
  evidence, or only a blocker.
- The decision does not claim predictive validity.
- The decision does not recommend paid ACUT reruns unless a concrete
  benchmark-side bug is found.
- Verification commands and results are recorded.

Suggested commit:

```text
Close click LLM source repair run
```

## Final Report Template

Use this structure in the final closeout report:

```text
# Click LLM-Assisted Source-Context Repair Decision

Decision label: ...

What happened: ...
Why it matters: ...
Action suggested next: ...

- Click tasks in scope:
- Public-context repaired:
- LLM-assisted repaired:
- Still title-only/minor-risk:
- Rejected or blocked:
- Paid LLM calls:
- Paid ACUT solver cells:
- Token-estimated LLM cost:
- Predictive validity established:
- Click claim boundary:
- PROCESS.md updated:

## Boundary

...

## Verification

- focused tests:
- full relevant suite:
- git diff --check:
```
