# Phase 1 Statement-Hardened Holdout Preregistration Runbook

Status: implementation runbook, 2026-05-25.

This runbook is for one dedicated Codex CLI session. Its job is to prepare a
new statement-hardened preregistration after the `attrs` H_future
statement-quality audit found that the current `attrs` H_future evidence is not
clean enough for the proposal's predictive-validity claim.

The goal is local preregistration, not paid validation. The worker should decide
whether there is enough clean statement-hardened supply to freeze a new release,
write the frozen manifest and decision artifacts, and stop before any paid ACUT
or paid LLM call.

## Starting Point

Current committed evidence:

```text
two-repo pilot:
  repos: boltons, attrs
  B_eval scoreable cells: 16
  H_future scoreable cells: 15
  policy violations: 1
  predictive_validity_established: false
  production ranking: not_produced

attrs H_future original observation:
  scoreable pass rate: 1/7
  verified fails: 6
  policy violations: 1

statement-quality audit:
  primary status: not_clean_enough_for_predictive_validity_claim
  material statement-quality risk tasks: 4/4 attrs H_future tasks
  strict clean-statement attrs H_future scoreable cells: 0
  next branch: prepare_statement_hardened_preregistration
```

Important source reports:

```text
experiments/phase1_compiler/reports/phase1_attrs_h_future_evidence_status.md
experiments/phase1_compiler/reports/phase1_attrs_h_future_task_design_audit.md
experiments/phase1_compiler/reports/phase1_attrs_h_future_statement_sensitivity.md
experiments/phase1_compiler/reports/phase1_attrs_h_future_statement_preview.md
```

The proposal in `barcarolle-research-0519.md` keeps
the direction narrow:

```text
Barcarolle is a target-repository benchmark compiler. Its contribution is not
raw task generation, but selecting, weighting, splitting, calibrating, and
quality-controlling a repo-specific benchmark so that it can predict future
target-repo work.
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing <repo>/docs/experiments/phase-1-statement-hardened-holdout-preregistration-runbook.md.

Work in <repo>. Use uv for repo-local Python tooling.
Make a cohesive git commit after every completed step that changes files. Do
not batch unrelated steps into one commit. If a step has no file changes, record
that fact in the process report and do not create an empty commit. Do not push
unless the user explicitly asks.

Main goal: prepare a local-only statement-hardened holdout preregistration after
the attrs H_future statement-quality audit. Decide whether enough clean supply
exists to freeze a new release. If yes, freeze the manifest, statement digests,
selection rule, and paid-validation gate. If no, write a precise blocker and
record a replacement-supply recommendation.

Do not run paid ACUT cells or paid LLM calls. Do not rerun existing scoreable
cells. Do not rerun the confirmed attrs__hist__027 policy violation. Do not
modify Codex, Kilo, or any ACUT internals. Do not rewrite historical score
tables. Improved statements, previews, and preregistration artifacts are new
sidecar evidence only.

Keep Barcarolle on the benchmark/compiler side of the ACUT boundary. Barcarolle
may inspect sanitized score artifacts, public source-context metadata, certified
task metadata, local target-repo history, statement-quality diagnostics, package
manifests, and local certification records. Barcarolle must not use hidden
verifier material to tune solver statements or weaken scope policy.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
GitHub API responses, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, raw patch bodies, full public issue/PR bodies, or
large raw outputs. Commit only small sanitized configs, tools, tests, manifests,
sidecar audits, summaries, reports, digests, and short excerpts.

The final user-facing summary should be simple Chinese. It should say whether a
statement-hardened release was frozen, whether paid validation is still blocked,
and what next action is recommended. Do not draft or create the next runbook.
```

## Research Boundary

This runbook must preserve three distinctions:

```text
historical observation:
  The old paid two-repo result, including attrs H_future 1/7, remains immutable.

statement-hardened preregistration:
  A new local release candidate with explicit statement-quality gates and
  frozen statement digests.

future paid validation:
  A separate future action that requires explicit user approval and must run
  only the newly frozen release under a new prefix.
```

Do not call the new preregistration a repaired score. Do not call diagnostic
statement previews scoreable evidence.

## Claim Boundary

Allowed claims:

```text
statement_hardened_preflight_recorded
statement_quality_gate_verified
candidate_holdout_supply_screened
statement_hardened_release_frozen
statement_hardened_preregistration_written
paid_validation_gate_defined
replacement_supply_needed
future_paid_validation_requires_user_approval
historical_paid_results_preserved
```

Disallowed claims:

```text
predictive_validity_established
production_benchmark_ranking
attrs_h_future_paid_result_repaired
attrs_policy_violation_repaired
rerun_equivalent_score_from_statement_preview
hidden_oracle_informed_statement_rewrite
old_two_repo_result_overwritten
paid_validation_completed
task_generator_yield_as_main_contribution
```

Interpretation rules:

- Selection must be based on public context, certification metadata,
  statement-quality gates, task strata, and cost/coverage constraints. Do not
  select tasks because an ACUT passed or failed them in a paid run.
- Existing paid outcomes may be cited only as historical motivation and
  comparison context.
- If the clean statement-hardened release cannot reach a meaningful minimum
  size, the correct output is a blocker or replacement-supply recommendation.
- If a PR-context task is kept, the preregistration must say why it is still
  sufficiently problem-like and non-leaky.
- Editable scope must be implementation-only. Tests, verifier files, and
  generated metadata must not be listed as editable.

## Commit Discipline

Every step that changes files must be committed before moving on. Use one or
more commits per step when the step naturally contains separate units.

Suggested commit messages:

```text
Record statement-hardened preregistration preflight
Add statement-hardened preregistration tooling
Screen statement-hardened holdout supply
Render statement-hardened release previews
Freeze statement-hardened release manifest
Write statement-hardened preregistration
Decide statement-hardened validation branch
Record statement-hardened preregistration closeout
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
provider cost change: USD 0
```

Allowed external lookup:

```text
Non-paid GitHub metadata lookup is allowed only for public issue/PR pages that
are already referenced by sanitized task metadata. Commit only source refs,
lengths, digests, and short sanitized excerpts. Do not commit raw API responses
or full issue/PR bodies.
```

Stop before any paid work and write a blocker if:

- the next step requires a paid ACUT or paid LLM call;
- the next step requires a provider endpoint test;
- the worker cannot separate hidden verifier material from public context;
- the worker would need to modify ACUT internals;
- the worker would need to change historical score tables instead of adding
  sidecar artifacts.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_statement_hardened_holdout_preregistration.yaml
  tools/
    phase1_statement_hardened_preregistration.py
  tests/
    test_phase1_statement_hardened_preregistration.py
  results/
    phase1_statement_hardened_holdout_preflight.json
    phase1_statement_hardened_candidate_inventory.json
    phase1_statement_hardened_candidate_screen.json
    phase1_statement_hardened_release_preview.json
    phase1_statement_hardened_release_manifest.json
    phase1_statement_hardened_preregistration.json
    phase1_statement_hardened_validation_decision.json
  reports/
    phase1_statement_hardened_holdout_process.md
    phase1_statement_hardened_candidate_inventory.md
    phase1_statement_hardened_candidate_screen.md
    phase1_statement_hardened_release_preview.md
    phase1_statement_hardened_preregistration.md
    phase1_statement_hardened_validation_decision.md
```

Optional if the local release cannot be frozen:

```text
experiments/phase1_compiler/
  results/
    phase1_statement_hardened_blocker.json
  reports/
    phase1_statement_hardened_blocker.md
docs/experiments/
  phase-1-statement-hardened-replacement-supply-runbook.md
```

Optional if the local release is frozen and the only remaining step is paid
validation:

```text
docs/experiments/
  phase-1-statement-hardened-paid-validation-runbook.md
```

Use a new paid result prefix only in a future runbook. Do not write new outputs
into old `phase1_two_repo_future_holdout_*` prefixes.

## Release Design Defaults

The worker may revise these defaults only if the evidence clearly supports it
and the rationale is committed.

```text
target release type:
  statement_hardened_two_repo_holdout_preregistration

minimum viable local preregistration:
  at least 2 repos with statement-quality-gated candidates, or a precise
  blocker explaining why only attrs replacement is currently possible

preferred repos:
  boltons and attrs, because they are the current Phase 1 repos

preferred candidate source:
  existing certified clean supply and clean-outcome-unseen-supply artifacts

minimum statement-quality requirement:
  statement_quality_gate == pass, or manual_review_required with explicit
  rationale and no unresolved severe risk

minimum release shape if enough supply exists:
  4 B_eval tasks and 4 H_future tasks per repo, 2 adapters planned per task

fallback release shape:
  attrs-only statement-hardened diagnostic release, clearly marked not enough
  by itself for predictive-validity establishment
```

Do not choose tasks by paid outcome. For old paid tasks, the outcome field may
be used only to label historical context and must not influence selection.

## Step 0: Preflight And Evidence Lock

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, and git status.
2. Record existing untracked or unrelated paths without touching them.
3. Read the governing proposal:

```text
barcarolle-research-0519.md
```

4. Lock input digests for:

```text
experiments/phase1_compiler/results/phase1_attrs_h_future_evidence_status.json
experiments/phase1_compiler/results/phase1_attrs_h_future_task_design_audit.json
experiments/phase1_compiler/results/phase1_attrs_h_future_statement_sensitivity.json
experiments/phase1_compiler/results/phase1_attrs_h_future_statement_preview.json
experiments/phase1_compiler/results/phase1_two_repo_task_outcome_matrix.json
experiments/phase0_headroom/tools/statement_quality.py
```

5. Write:

```text
experiments/phase1_compiler/configs/phase1_statement_hardened_holdout_preregistration.yaml
experiments/phase1_compiler/results/phase1_statement_hardened_holdout_preflight.json
experiments/phase1_compiler/reports/phase1_statement_hardened_holdout_process.md
```

Acceptance:

- The preflight says paid calls were not made.
- Historical paid score tables are declared immutable inputs.
- The process report states that this runbook cannot establish predictive
  validity because no new paid validation is run.
- Input artifact digests are recorded.

Commit:

```text
Record statement-hardened preregistration preflight
```

## Step 1: Add Durable Preregistration Tooling

Actions:

1. Add or update:

```text
experiments/phase1_compiler/tools/phase1_statement_hardened_preregistration.py
experiments/phase1_compiler/tests/test_phase1_statement_hardened_preregistration.py
```

2. The tool must load only sanitized committed artifacts. Likely inputs:

```text
experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_certified_tasks.jsonl
experiments/phase0_headroom/candidate_sources/boltons_clean_outcome_unseen_supply_source_context.jsonl
experiments/phase0_headroom/candidate_sources/attrs_clean_outcome_unseen_supply_source_context.jsonl
experiments/phase1_compiler/results/phase1_attrs_h_future_evidence_status.json
experiments/phase1_compiler/results/phase1_two_repo_task_outcome_matrix.json
```

3. The tool must reuse:

```text
experiments/phase0_headroom/tools/statement_quality.py
```

4. The tool should provide functions to:

- build a candidate inventory;
- attach statement-quality diagnostics;
- compute statement previews;
- compute stable statement digests;
- screen candidates using public-context and scope gates;
- freeze a manifest from a deterministic selection rule;
- write JSON and Markdown outputs.

5. Add tests covering:

- old 240-character truncation is rejected or held for manual review;
- implementation scope excludes tests and generated metadata;
- statement digest changes when solver-visible statement text changes;
- paid outcome fields cannot be used by the selection function;
- PR-context candidates require a problem-context rationale or linked issue;
- strict gates can produce a blocker instead of silently freezing a weak
  release.

Acceptance:

```bash
uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_statement_hardened_preregistration.py
```

passes, and no raw artifacts are committed.

Commit:

```text
Add statement-hardened preregistration tooling
```

## Step 2: Build Candidate Inventory

Actions:

1. Run the preregistration tool in inventory mode.
2. For each candidate, record:

```text
repo_id
task_id
task_time
source_ref
source_kind
source_context_status
statement_quality_gate
statement_quality_risk_reasons
implementation_files
test_files
module_or_package
change_size_bucket or changed line counts if available
certification gate summary
split eligibility
historical_paid_context if present
selection_eligible_without_paid_outcome
```

3. Write:

```text
experiments/phase1_compiler/results/phase1_statement_hardened_candidate_inventory.json
experiments/phase1_compiler/reports/phase1_statement_hardened_candidate_inventory.md
```

Acceptance:

- Inventory covers at least `boltons` and `attrs` if local artifacts exist.
- Each candidate has statement-quality diagnostics.
- Historical paid outcomes, if present, are clearly separated as context and
  not used for eligibility.
- The report gives simple counts by repo, split eligibility, and
  statement-quality gate.

Commit:

```text
Build statement-hardened candidate inventory
```

## Step 3: Screen Candidates And Decide Release Feasibility

Actions:

1. Apply deterministic gates:

```text
certified task status required
public source context required
statement_quality_gate must pass, or explicit manual-review rationale required
editable implementation scope must be non-empty
editable implementation scope must exclude tests
hidden verifier material must not appear in statement preview
target commit or raw diff must not appear in statement preview
PR-context candidates need linked issue or explicit problem-context rationale
```

2. Compute feasibility for:

```text
two_repo_statement_hardened_release
attrs_only_statement_hardened_diagnostic_release
replacement_supply_needed
```

3. Write:

```text
experiments/phase1_compiler/results/phase1_statement_hardened_candidate_screen.json
experiments/phase1_compiler/reports/phase1_statement_hardened_candidate_screen.md
```

Acceptance:

- The screen report says whether the preferred two-repo release is feasible.
- If not feasible, it names the missing supply by repo, split, and reason.
- The report does not recommend paid validation unless a frozen release can be
  built.

Commit:

```text
Screen statement-hardened holdout supply
```

## Step 4: Render Statement-Hardened Release Previews

Actions:

1. For the selected candidate set or best feasible candidate set, render
   solver-visible statement previews.
2. Each preview must include:

```text
repo_id
task_id
source ref
problem summary
short sanitized public excerpt
editable implementation scope
known non-editable test paths
verifier command metadata
statement_quality diagnostics
statement digest
```

3. Each preview must exclude:

```text
target commit hash
target diff
gold patch
hidden verifier content
raw public issue/PR body
paid outcome
solver transcript
```

4. Write:

```text
experiments/phase1_compiler/results/phase1_statement_hardened_release_preview.json
experiments/phase1_compiler/reports/phase1_statement_hardened_release_preview.md
```

Acceptance:

- No preview is cut mid-code or mid-sentence.
- Editable paths contain implementation files only.
- Every preview has a stable digest.
- The report states that previews are not scoreable results.

Commit:

```text
Render statement-hardened release previews
```

## Step 5: Freeze Release Manifest Or Write Blocker

Actions:

1. If the candidate screen is feasible, freeze:

```text
experiments/phase1_compiler/results/phase1_statement_hardened_release_manifest.json
```

The manifest must include:

```text
schema_version
release_id
created_at
selection_rule
selected_repos
selected_splits
selected_task_ids
planned_adapters
planned_cells
statement_digests
allowed_context_refs
editable_implementation_paths
non_editable_test_paths
verifier_command_metadata
statement_quality_diagnostics
input_artifact_digests
historical_result_policy
paid_validation_prefix_reserved
```

2. If the candidate screen is not feasible, write:

```text
experiments/phase1_compiler/results/phase1_statement_hardened_blocker.json
experiments/phase1_compiler/reports/phase1_statement_hardened_blocker.md
```

and draft:

```text
docs/experiments/phase-1-statement-hardened-replacement-supply-runbook.md
```

3. Do not produce both a frozen release and a blocker unless the blocker is for
   a clearly separate optional branch.

Acceptance for frozen release:

- The manifest is deterministic.
- The manifest references only sanitized committed artifacts.
- The manifest has enough planned cells for its claim boundary.
- The manifest says future paid validation needs explicit user approval.

Acceptance for blocker:

- The blocker says exactly what supply is missing.
- The blocker recommends local replacement mining before paid validation.
- The blocker does not claim predictive validity.

Commit:

```text
Freeze statement-hardened release manifest
```

or:

```text
Record statement-hardened release blocker
```

## Step 6: Write Preregistration

Actions:

1. If a manifest was frozen, write:

```text
experiments/phase1_compiler/results/phase1_statement_hardened_preregistration.json
experiments/phase1_compiler/reports/phase1_statement_hardened_preregistration.md
```

2. The preregistration must define:

```text
research question
release id and manifest digest
repos and splits
planned adapters
planned paid prefixes
endpoint rule: LLM_BASE_URL plus LLM_API_KEY only
cost cap proposal
stop conditions
scoreability rules
policy-violation handling
comparison metrics
uncertainty metrics
decision thresholds
claims allowed after paid validation
claims still disallowed
```

3. The preregistration must say how old results are handled:

```text
Old attrs H_future results are historical observations only.
They are not corrected, repaired, rerun-equivalent, or merged into the new
release score.
```

4. If no manifest was frozen, write a short no-preregistration report saying
   why.

Acceptance:

- The preregistration is complete enough for a future paid-validation runbook.
- It does not authorize paid calls by itself.
- It includes clear cost and stop gates for any future runbook.

Commit:

```text
Write statement-hardened preregistration
```

## Step 7: Decide Next Branch

Actions:

1. Write:

```text
experiments/phase1_compiler/results/phase1_statement_hardened_validation_decision.json
experiments/phase1_compiler/reports/phase1_statement_hardened_validation_decision.md
```

2. Choose exactly one primary decision:

```text
ready_for_user_approved_paid_validation:
  Use only if a frozen manifest and preregistration exist.

replacement_supply_needed_before_paid_validation:
  Use if not enough clean statement-hardened supply exists.

attrs_only_diagnostic_preregistration_ready:
  Use only if the release can test the statement-confound hypothesis but cannot
  establish two-repo predictive validity by itself.

blocked_on_protocol_decision:
  Use if the worker cannot choose between same-task statement repair and
  replacement holdout without user input.
```

3. If the decision is `ready_for_user_approved_paid_validation`, record this
   suggested follow-up path without creating or editing the file:

```text
docs/experiments/phase-1-statement-hardened-paid-validation-runbook.md
```

4. If the decision is `replacement_supply_needed_before_paid_validation`, record
   this suggested follow-up path without creating or editing the file:

```text
docs/experiments/phase-1-statement-hardened-replacement-supply-runbook.md
```

Acceptance:

- The decision is written in simple terms.
- It says whether paid validation is still blocked.
- It states the suggested follow-up runbook path.
- It does not create or edit any follow-up runbook file.
- It does not claim predictive validity.

Commit:

```text
Decide statement-hardened validation branch
```

## Step 8: Closeout

Actions:

1. Update:

```text
experiments/phase1_compiler/reports/phase1_statement_hardened_holdout_process.md
```

with:

```text
steps completed
commits created
tests run
paid calls made: false
raw artifacts committed: false
release frozen: true/false
preregistration written: true/false
primary decision
next runbook path
follow-up runbook written by worker: false
```

2. Run:

```bash
git diff --check
git status --short
```

3. If there are changed files from this closeout, commit them.

Acceptance:

- Worktree status contains only intentional changes or pre-existing unrelated
  untracked files.
- Final process report is consistent with JSON decision artifacts.
- No paid calls were made.

Commit:

```text
Record statement-hardened preregistration closeout
```

## Verification Commands

At minimum, run:

```bash
uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_statement_hardened_preregistration.py

uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py \
  experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py \
  experiments/phase0_headroom/tools/test_workspace_acut_run.py

git diff --check
```

If broader code paths were touched, expand the test scope accordingly.

## Final Response Template

Use simple Chinese:

```text
这轮 runbook 完成后的结论：

1. 是否成功冻结了 statement-hardened release。
2. 是否写好了 preregistration。
3. 是否还禁止 paid validation，以及下一份 runbook 是哪一份。

不要说旧 attrs H_future 分数被修好了。
不要说 predictive validity 已经建立。
```
