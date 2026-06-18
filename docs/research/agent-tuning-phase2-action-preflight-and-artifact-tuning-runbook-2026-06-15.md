# Agent Tuning Phase 2 Action Preflight And Artifact Tuning Runbook 2026-06-15

Status: mandatory Phase 2 runbook for moving from Agent Tuning feasibility to a
minimal before/after tuning demo.

This runbook must not treat Phase 1's request-context proof as enough. Phase 2
has a hard first gate:

> Before any GEPA/Phoenix optimization, prove that a repo-local tuning artifact
> can change real Agent action behavior, such as command execution, file reads,
> file edits, final diff, or public-test execution.

Only if that gate passes may the executing Agent run a bounded artifact-tuning
loop and a frozen Holdout before/after validation.

## Current State

Agent Tuning Phase 1 ended with:

```text
ready_for_phase2_with_restrictions
```

The important Phase 1 findings are:

- real Codex/Kilo-style workspace Agents can receive repo-local text artifacts
  in their request path;
- Kilo `AGENTS.md` and Kilo `.kilo/rules` with `kilo.jsonc` are the most
  reliable initial surfaces;
- skill tests showed metadata visibility, not full on-demand `SKILL.md`
  loading;
- behavior-change evidence reached request-context only, not command/diff/test
  action level;
- no paid LLM/Agent calls were used.

Canonical Phase 1 artifacts:

- `experiments/agent_tuning_demo/reports/phase1_feasibility_closeout_zh.md`
- `experiments/agent_tuning_demo/results/phase1_feasibility_closeout.json`
- `experiments/agent_tuning_demo/reports/injection_smoke_tests_zh.md`
- `experiments/agent_tuning_demo/reports/behavior_change_smoke_test_zh.md`
- `docs/research/agent-tuning-tuner-compatibility-2026-06-14.md`

## Target Demo Claim

If this runbook succeeds, the maximum claim is:

> On a frozen target-repo split, Barcarolle used target-repo Agent failures to
> optimize a deployable repo-local Agent artifact, injected it into a real
> workspace Agent under fixed conditions, and validated the before/after result
> on held-out tasks.

This is still not a proof of long-term predictive validity, cross-repo
generalization, model fine-tuning, or full black-box Agent tuning.

## Non-Goals

- Do not claim that GEPA/Phoenix tunes full opaque Codex/Kilo internals.
- Do not optimize model choice or reasoning effort in this runbook.
- Do not tune multiple artifact surfaces at once.
- Do not use skills as the first surface unless `AGENTS.md` and Kilo rules both
  fail action-level preflight.
- Do not run many tuned variants on Holdout.
- Do not use Holdout details in optimizer input, prompt, failure labels, or
  candidate artifact generation.
- Do not continue into paid optimizer rollout if action-level preflight fails.

## Required Reading

Read before changing code:

- `AGENTS.md`
- `PROCESS.md`
- `docs/research/agent-tuning-phase1-feasibility-runbook-2026-06-14.md` if
  present
- `experiments/agent_tuning_demo/reports/phase1_feasibility_closeout_zh.md`
- `experiments/agent_tuning_demo/results/phase1_feasibility_closeout.json`
- `experiments/agent_tuning_demo/reports/tuning_surface_inventory_zh.md`
- `docs/research/agent-tuning-tuner-compatibility-2026-06-14.md`
- `experiments/agent_tuning_demo/tools/tuning_artifacts.py`
- `experiments/agent_tuning_demo/tools/agent_injection_smoke.py`
- `experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md`
- `experiments/agent_selection_demo/results/selection_score_table.csv`
- `experiments/agent_selection_demo/results/holdout_score_table.csv`
- `experiments/agent_selection_demo/results/doubled_timeout_top2_repeat_score_table.csv`
- `experiments/phase0_headroom/tools/kilo_workspace_adapter.py`
- `experiments/phase0_headroom/tools/workspace_acut_run.py`

Preserve unrelated untracked files. If the Phase 1 runbook/prompt files are
still untracked, do not delete or overwrite them.

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

Add new Phase 2 artifacts with `phase2_` prefixes.

## Paid-Call Boundary

Default to no-paid dry runs whenever possible.

Paid calls are permitted only for:

1. a minimal action-level preflight if fake/local testing cannot prove actions;
2. a bounded Phase 2 tuning rollout after the action-level gate passes;
3. final baseline-vs-tuned Holdout validation after the chosen artifact hash is
   frozen.

All paid LLM or Agent calls must use:

```text
LLM_BASE_URL
LLM_API_KEY
```

No fallback auth is allowed. Record paid cell count, estimated cost, observed
usage coverage, and any conservative estimates. Keep raw transcripts, raw
prompts, raw completions, solver workspaces, verifier workspaces, and secrets in
ignored paths only.

Recommended cap for this runbook:

```text
action_preflight_paid_cells_max: 4
optimization_paid_cells_max: 32
holdout_paid_cells_max: 20
total_paid_cells_max: 56
```

If the run can complete with fewer cells, spend fewer cells.

## Package 1: Phase 2 Protocol Freeze

Goal: freeze the Phase 2 protocol before action preflight and before any
optimizer sees data.

Tasks:

1. Choose the initial real-Agent route:
   - default: Kilo workspace Agent + repo `AGENTS.md` appendix;
   - fallback 1: Kilo `.kilo/rules/barcarolle.md` plus `kilo.jsonc`;
   - fallback 2: Codex repo `AGENTS.md` after Codex action preflight;
   - fallback 3: DSPy-native coding workflow only if real-Agent action behavior
     cannot be proven.
2. Choose the target repository and candidate task pool:
   - default: `mahmoud/boltons`;
   - use optimizer-visible Selection-side tasks for train/dev;
   - keep Holdout/future tasks unavailable until artifact hash freeze.
3. Choose the target Agent:
   - prefer a Kilo configuration with measurable headroom;
   - use existing sanitized score tables to avoid picking a saturated Agent;
   - if Kilo GPT mainline is too strong, prefer Kilo low-cost or another
     weaker-but-fixable Kilo route.
4. Freeze initial split manifest:
   - `selection_train`;
   - `selection_dev`;
   - `holdout`.
5. Freeze allowed artifact:
   - exactly one text artifact for the first run, preferably an `AGENTS.md`
     appendix;
   - no simultaneous skill + rule + policy bundle.
6. Freeze metrics:
   - action-level preflight success;
   - Selection-dev paired net wins;
   - Holdout paired net wins;
   - pass rate;
   - invalid patch / timeout / verifier replay success;
   - cost and latency;
   - behavior-change markers.
7. Freeze leakage controls:
   - optimizer exporter refuses Holdout artifacts;
   - candidate artifact records include `visible_to_optimizer` and
     `holdout_derived`;
   - `holdout_derived: true` candidates are rejected by default;
   - chosen artifact hash must be frozen before Holdout runs.

Deliverables:

- `experiments/agent_tuning_demo/reports/phase2_protocol_zh.md`
- `experiments/agent_tuning_demo/results/phase2_protocol.json`

Acceptance:

- Protocol records Agent, repository, splits, surface, metrics, caps, and
  leakage controls.
- Protocol explains why the selected Agent has tuning headroom.
- Protocol states exact stop conditions.

Commit after this package.

## Package 2: Action-Level Preflight Gate

Goal: prove artifact injection changes real Agent action behavior before any
optimizer rollout.

Use the Phase 2 primary surface first: Kilo repo `AGENTS.md` appendix.

Construct a tiny controlled fixture task where a public test command can be
observed safely. A recommended design:

1. Create a temporary Python fixture workspace with:
   - a small source file;
   - `tests/test_public_smoke.py`;
   - a test that writes a marker file such as
     `.barcarolle_public_test_marker` when run, then passes.
2. Create two artifacts:
   - Variant A: do not run tests;
   - Variant B: after editing, run
     `python -m pytest tests/test_public_smoke.py -q`.
3. Run the same Agent, model, timeout, task statement, and workspace setup for
   both variants.
4. Inspect sanitized observations:
   - marker file exists only for Variant B; or
   - command trace records the public test command only for Variant B; or
   - file read/edit/diff behavior differs in a way attributable to the
     artifact.

If a fake endpoint cannot drive tool calls, use the smallest paid harmless smoke
cells allowed by the paid-call boundary. Do not use hidden-verifier tasks for
this preflight.

Fallback order:

1. Kilo `AGENTS.md`;
2. Kilo `.kilo/rules` plus `kilo.jsonc`;
3. Codex `AGENTS.md`;
4. tuner-native fallback recommendation.

Deliverables:

- `experiments/agent_tuning_demo/reports/phase2_action_preflight_zh.md`
- `experiments/agent_tuning_demo/results/phase2_action_preflight.json`
- helper tests if new instrumentation is added

Acceptance:

- `action_level_preflight_passed = true`; or
- the report records a hard blocker and recommends fallback without running
  optimizer rollout.

Passing evidence must include at least one action-level difference:

- command executed;
- marker file written by public test;
- file read/edit behavior changed;
- final diff changed;
- public-test behavior changed.

Request-context-only differences are not enough.

Commit after this package.

## Package 3: Feedback Export And Failure Labels

Goal: produce optimizer-visible training feedback without leaking Holdout.

Tasks:

1. Export Selection-train artifacts for the target Agent:
   - task id;
   - task statement or sanitized task summary;
   - public logs if available and safe;
   - verifier outcome summary;
   - sanitized failure labels;
   - diff stats;
   - command/test behavior summary if available;
   - cost/latency summary.
2. Do not export:
   - Holdout task IDs;
   - Holdout logs;
   - hidden test bodies;
   - raw prompts;
   - raw completions;
   - raw transcripts;
   - verifier workspace contents.
3. Create a compact failure taxonomy. Suggested labels:
   - insufficient_localization;
   - missed_existing_test_pattern;
   - did_not_run_targeted_tests;
   - wrong_api_semantics;
   - missing_regression_test;
   - overbroad_patch;
   - invalid_or_no_diff;
   - timeout_or_context_exhaustion;
   - verifier_replay_failure;
   - unknown.
4. Every label must cite sanitized evidence or be marked `unknown`.

Deliverables:

- `experiments/agent_tuning_demo/reports/phase2_feedback_export_zh.md`
- `experiments/agent_tuning_demo/results/phase2_optimizer_input.jsonl`
- `experiments/agent_tuning_demo/results/phase2_failure_labels.jsonl`
- `experiments/agent_tuning_demo/results/phase2_feedback_export_manifest.json`

Acceptance:

- Exporter excludes Holdout by construction.
- Failure labels are concrete enough for a proposer.
- Hygiene scan has no raw prompt/completion/transcript content.

Commit after this package.

## Package 4: Minimal GEPA Artifact-Tuning Loop

Goal: use a bounded optimizer/proposer to produce a repo-local artifact.

Primary:

```text
GEPA standalone / optimize_anything
```

Artifact:

```text
one AGENTS.md appendix
```

Backup if GEPA cannot be installed or integrated within the runbook:

```text
Phoenix-style prompt/rule proposer, or a bounded reflective text proposer
clearly labeled as non-GEPA
```

Do not mislabel fallback output as GEPA output.

Optimizer input:

- Selection-train failure labels and sanitized summaries only.

Evaluator:

- Selection-dev tasks only.
- Same Agent/model/budget/surface as frozen in Package 1.
- Baseline and candidate artifact runs under identical conditions.

Recommended bounds:

```text
max_iterations: 2
max_candidates_total: 3
max_metric_calls: 24
selection_dev_tasks: 4 to 8
```

Candidate artifact requirements:

- deterministic hash;
- no Holdout-derived content;
- no task-specific file names unless they come from allowed train evidence and
  are generalized;
- each rule cites targeted failure labels;
- rollback plan included;
- concise enough to fit Agent context budget.

Deliverables:

- `experiments/agent_tuning_demo/reports/phase2_candidate_artifacts_zh.md`
- `experiments/agent_tuning_demo/results/phase2_candidate_artifacts.json`
- `experiments/agent_tuning_demo/results/phase2_selection_dev_results.csv`
- `experiments/agent_tuning_demo/results/phase2_selection_dev_summary.json`

Acceptance:

- At least one candidate artifact is generated and evaluated; or
- report why proposer integration failed and give fallback.
- Selection-dev baseline vs candidate is reported as paired net wins, pass
  rates, invalid-run count, cost, and latency.
- If no candidate is at least non-regressing on Selection-dev, do not spend
  Holdout paid cells; close as negative or restricted.

Commit after this package.

## Package 5: Freeze Chosen Artifact

Goal: lock the chosen artifact before Holdout.

Tasks:

1. Select a candidate by frozen rule:
   - prefer higher Selection-dev paired net wins;
   - break ties by lower invalid-run count;
   - then lower cost/latency if observed usage is comparable;
   - otherwise choose smaller/clearer artifact.
2. Write the chosen artifact to a committed sanitized path.
3. Record:
   - artifact hash;
   - source candidate;
   - Selection-dev scores;
   - rules and targeted failure labels;
   - leakage audit;
   - exact command to apply/inject artifact.
4. Freeze the artifact before any Holdout run.

Deliverables:

- `experiments/agent_tuning_demo/reports/phase2_chosen_artifact_zh.md`
- `experiments/agent_tuning_demo/results/phase2_chosen_artifact.json`
- sanitized artifact file under
  `experiments/agent_tuning_demo/results/chosen_artifact/`

Acceptance:

- Chosen artifact hash is stable.
- Closeout states whether it passed the gate to run Holdout.
- No Holdout-derived evidence appears in the artifact or selection rationale.

Commit after this package.

## Package 6: Frozen Holdout Before/After Validation

Goal: validate the chosen artifact on held-out tasks after freeze.

Run only:

- baseline Agent on Holdout;
- tuned Agent with chosen artifact on the same Holdout.

Use:

- same model;
- same harness;
- same task set;
- same timeout;
- same public-test policy;
- same verifier;
- same score-join rules.

Do not compare a fresh tuned run against stale baseline unless the report marks
it as retrospective only. Prefer fresh baseline and fresh tuned cells under the
same conditions.

Recommended Holdout size:

```text
holdout_tasks: 6 to 10
paired_runs_per_task: 1
```

If budget allows and stochasticity is material, repeat only the top ambiguous
pairs. Do not expand to many variants.

Deliverables:

- `experiments/agent_tuning_demo/reports/phase2_holdout_validation_zh.md`
- `experiments/agent_tuning_demo/results/phase2_holdout_results.csv`
- `experiments/agent_tuning_demo/results/phase2_holdout_summary.json`

Acceptance:

- Paired baseline/tuned results exist for the frozen Holdout tasks; or
- report explains why Holdout was not run due to failed gates.
- Report includes paired net wins:

```text
net_wins = count(tuned_pass && baseline_fail)
         - count(baseline_pass && tuned_fail)
```

- Report includes cost/latency and invalid-run comparisons.

Commit after this package.

## Package 7: Final Phase 2 Report

Goal: produce the reader-facing Agent Tuning Demo package.

Deliverables:

- `experiments/agent_tuning_demo/reports/phase2_agent_tuning_demo_report_zh.md`
- `experiments/agent_tuning_demo/reports/phase2_closeout_zh.md`
- `experiments/agent_tuning_demo/results/phase2_closeout.json`
- update `PROCESS.md` with a short current-state entry and canonical links

Report structure:

1. What the demo tried to prove.
2. Why Phase 1 required an action-level gate.
3. Which Agent/surface/repo were used.
4. Action-level preflight result.
5. Train failure labels and candidate artifact generation.
6. Selection-dev before/after result.
7. Frozen Holdout before/after result.
8. Cost/latency/invalid-run impact.
9. Case studies:
   - one improved task if any;
   - one unchanged task;
   - one regression or remaining failure if any.
10. Supported claims.
11. Unsupported claims.
12. Recommended next work.

Supported claim if successful:

> Barcarolle can use target-repo feedback to tune a deployable repo-local Agent
> artifact and validate before/after behavior under a frozen protocol.

Unsupported claims:

- full predictive validity;
- cross-repo generalization;
- model fine-tuning;
- full opaque Codex/Kilo Agent tuning;
- GEPA/Phoenix superiority;
- statistical significance unless the data supports it;
- production-ready Agent tuning system.

Commit after this package.

## Validation And Hygiene

Run at minimum:

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
uv run --project experiments/phase0_headroom pytest experiments/phase0_headroom/tools/test_cli_workspace_adapters.py experiments/phase0_headroom/tools/test_workspace_acut_run.py -q
git diff --check
```

If paid cells were run, include a sanitized cost report. If observed token usage
coverage is incomplete, mark cost as estimate or inconclusive.

Hygiene checks:

```text
git ls-files experiments/agent_tuning_demo | rg '(\.venv|\.pytest_cache|\.DS_Store|raw|transcript|workspace|secret|prompt|completion)' || true
git diff --cached --name-only | rg '(\.venv|\.pytest_cache|\.DS_Store|raw|transcript|workspace|secret)' || true
```

Investigate any hits. Do not commit raw prompts, completions, transcripts,
solver workspaces, verifier workspaces, secrets, or large raw outputs.

## Terminal States

Use one of these final states:

- `phase2_success_holdout_improved`: action preflight passed, artifact tuned,
  Holdout tuned beats baseline.
- `phase2_success_no_holdout_regression`: action preflight passed, artifact
  tuned, Holdout does not regress but improvement is weak.
- `phase2_selection_dev_negative`: action preflight passed, but tuned artifact
  did not improve or was worse on Selection-dev; Holdout not run.
- `phase2_action_preflight_blocked`: no real-Agent action-level behavior change
  could be proven; optimizer rollout not run.
- `phase2_infrastructure_blocked`: tooling prevented a meaningful result after
  documented repair attempts.

Do not mark `phase2_success_*` unless the relevant evidence exists.

## Final Closeout Requirements

Final response and closeout must include:

- terminal state;
- paid cells and estimated/observed cost;
- action-level preflight result;
- optimizer/proposer used;
- target Agent and artifact surface;
- candidate artifact count;
- Selection-dev baseline/tuned matrix;
- Holdout baseline/tuned matrix if run;
- paired net wins;
- cost/latency/invalid-run comparison;
- tests and hygiene checks;
- exact supported and unsupported claims;
- commits made.
