# Proposal Report Skeleton Process

Status: `step0_preflight_complete`.

Runbook: `docs/experiments/phase-1-proposal-report-skeleton-runbook.md`

## Boundary

This M1 execution is no-paid writing and planning work. No paid ACUT solver
cells, paid LLM calls, external GPT-5.5-Pro calls, or hidden-oracle work were
run during Step 0.

The active objective is to write a proposal-report skeleton, argument map,
evidence/TODO matrix, and claim boundary that keep predictive validity as the
long-term north star while limiting the short-term proposal claim to traction
evidence and a credible research path.

## Preflight

| Field | Value |
| --- | --- |
| Branch | `codex/restart-benchmark-compiler` |
| HEAD | `da8d9977f823952932efb67ecab5c068f1bc5531` |
| Local timestamp | `2026-05-30 15:06:54 CST` |
| Paid ACUT cells run | `0` |
| Paid LLM calls run | `0` |
| External reviewer calls run | `0` |

Initial worktree status:

```text
 M PROCESS.md
?? docs/experiments/phase-1-proposal-report-skeleton-runbook.md
?? docs/research/
?? experiments/phase1_compiler/external_review/phase1_candidate_policy_validation_protocol_gpt55_bundle_20260530/
?? experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/
```

The pre-existing dirty state is treated as user/workspace context. Step-level
commits should stage only the files changed for this M1 execution.

## Required Input Availability

All required inputs named by the runbook were available:

- `AGENTS.md`
- `PROCESS.md`
- `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`
- `docs/architecture/system-design.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0519.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0526.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0526-1.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0530.md`
- `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`
- `experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md`
- `experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md`
- `experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md`
- `experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md`
- `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md`
- `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md`
- `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md`
- `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md`
- `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_decision.md`
- `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_policy_spec.md`
- `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md`
- `experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md`

Missing required inputs: none.

## Reader-Role Brief

Working title: Barcarolle Phase 1 proposal report skeleton.

Target readers:

- project/proposal reviewers deciding whether Barcarolle should continue;
- coding-agent evaluation researchers skeptical of benchmark overclaiming;
- agent developers who need repo-specific evaluation and tuning feedback.

Secondary readers:

- future Barcarolle contributors who need a clean claim boundary;
- reviewers of candidate policy, validation protocol, and paid-readiness plans.

Writer role: investigator and evaluator. The report should interpret Phase 1
evidence without selling unproved predictive validity.

Readers probably know that public SWE benchmarks and task generators exist, and
that coding-agent evaluations are vulnerable to leakage, sample bias, task
supply bottlenecks, and overclaiming. They may not know why a target-repository
benchmark compiler is a different research object from a general SWE task
factory.

Readers probably believe that a benchmark project must earn predictive claims
through future or strictly preregistered validation, not through retrospective
storytelling. They may also believe that small-N paid pilots are useful only if
the artifact and claim boundary are clean.

Readers likely value:

- outcome-blind selection rules;
- reproducible artifacts and clear benchmark-side boundaries;
- adapter-stratified reporting rather than pooled averages that hide failures;
- honest treatment of negative and underpowered evidence;
- concrete validation gates before paid ACUT work.

Readers will likely ask:

- Why is repo-specific predictive validity a meaningful research target?
- Why is Barcarolle not just another SWE task generator?
- What did Phase 1 support, and what did it fail to support?
- Why did naive target-profile weighting fail?
- Does the retrospective signal justify more work without claiming success?
- What evidence is still needed before reviewers should trust the proposal?

Readers may object that:

- Phase 1 has not proved predictive validity;
- the current candidate is too close to a simple coverage heuristic;
- `boltons` fallback changes the candidate-policy claim;
- adapter differences mean the current signal is not adapter-general;
- pseudo-future replay can be transductive even when task selection is
  outcome-blind;
- task-supply/generator work could distract from the benchmark compiler claim.

Credible evidence for these readers includes:

- committed decision reports and JSON artifacts, not raw transcripts;
- exact pilot counts, scoreability, endpoint compliance, and policy checks;
- baseline comparisons against simple alternatives;
- adapter- and repo-stratified metrics with uncertainty labels;
- explicit classification of allowed, draft, and prohibited claims;
- future validation plans that separate true future holdout from retrospective
  traction evidence.

The proposal must get readers to accept that Phase 1 does not establish
predictive validity, but it does establish a real, measurable, technically
tractable research problem: benchmark construction choices materially affect
repo-specific estimates, naive weighting fails in diagnosable ways, and the
next phase can be governed by stronger policies, baselines, and validation
criteria.

## Step Evidence

### Step 0

Completed:

- branch, HEAD, date, worktree status, and required-input availability recorded
  in `experiments/phase1_compiler/results/phase1_proposal_report_skeleton_preflight.json`;
- `AGENTS.md`, `PROCESS.md`, the proposal roadmap, system design, local research
  plans, and canonical reports were read or checked for availability;
- reader-role brief written above.

Acceptance:

- no paid calls made;
- missing inputs recorded as none;
- pre-existing dirty worktree state recorded;
- reader-role brief written.

### Step 1

Completed:

- wrote `docs/research/phase-1-proposal-argument-map.md`;
- separated the north-star claim, short-term proposal claim, allowed Phase 1
  claims, and prohibited claims;
- mapped reasons, evidence, warrants, objections, and responses;
- classified GPT-5.5-Pro recommendations as accept now, consider for no-paid
  proposal evidence, defer, or reject as short-term scope expansion.

Acceptance:

- predictive validity remains the north star;
- the short-term claim is stronger than artifact hygiene but does not claim
  predictive validity;
- GPT-5.5-Pro recommendations inform scope without expanding M1 by default;
- no paid calls made.

### Step 2

Completed:

- wrote `docs/research/phase-1-proposal-report-v0.md`;
- used the required report structure: problem, north star, thesis, Phase 1
  evidence, lessons, candidate path, validation path, research plan, risks and
  boundaries, and milestones;
- marked unsupported or incomplete material with `Draft` labels and
  `[NEEDS ...]` placeholders;
- cited local reports and planning files by path.

Acceptance:

- report can be read end-to-end as a proposal skeleton;
- every major claim has evidence, an evidence path, or an explicit placeholder;
- Phase 1 evidence is not overstated;
- task-supply/generator work is framed as Layer 1 support, not the project
  core;
- no paid calls made.

### Step 3

Completed:

- wrote `docs/research/phase-1-proposal-evidence-todo-matrix.md`;
- wrote
  `experiments/phase1_compiler/results/phase1_proposal_report_skeleton_evidence_todo_matrix.json`;
- included required rows for the north star, short-term claim, weighted failure,
  retrospective signal, adapter reporting, source repair, candidate fallback,
  `boltons` fallback, pseudo-future boundary, baseline strengthening, Task
  Supply v2 relevance, and paid-validation readiness;
- routed missing evidence to M2-M6 rather than running new experiments.

Acceptance:

- matrix drives later milestones;
- no prohibited claim is left as a draft claim;
- no paid calls made.
