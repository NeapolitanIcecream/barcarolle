# Barcarolle Phase 1 Proposal Report V1

Status: final-shape proposal draft with explicit placeholders, 2026-05-30.

This document is written in the shape of the proposal-approval report that
should exist when remaining pre-proposal work is complete. Bracketed
`[NEEDS ...]` markers are contracts for missing evidence, figures, citations,
numbers, decisions, or result-dependent paragraphs. They are not claims.

## 1. Executive Summary

Coding-agent evaluation has a target-repository prediction problem. Public
benchmarks and scalable task generators can show broad capability or produce
large executable task pools, but a team choosing an Agent Configuration Under
Test, or ACUT, still needs to know how that configuration is likely to perform
on future work in its own repository.

Barcarolle addresses the benchmark-construction layer between task supply and
agent evaluation. Given a target repository, candidate tasks, an ACUT boundary,
target-work assumptions, and an evaluation budget, Barcarolle asks which tasks
should be selected, split, weighted or left unweighted, refreshed, and
interpreted as evidence about future target-repository performance.

The long-term north star is predictive validity:

```text
Can a Barcarolle-compiled repo-specific benchmark predict future target-repo
ACUT performance better than naive same-repo sampling, general benchmark
scores, or other simple baselines?
```

This report does not claim that predictive validity has been established.
Phase 1 supports a narrower proposal claim: repo-specific benchmark
compilation is a real, measurable, and technically tractable research problem.
The evidence includes a clean negative result for naive weighting, corrected
adapter and source-quality boundaries, weak retrospective route-finding signal,
and an outcome-blind candidate policy ready for stricter review and protocol
hardening.

The proposal ask is to approve the next research phase only under this bounded
claim: strengthen the evidence and validation design needed to test
repo-specific predictive validity later. Paid ACUT validation remains
unauthorized until the protocol, baselines, support thresholds, fallback rules,
and uncertainty plan pass the gates in this report.

[NEEDS PARAGRAPH: final approval-language ask, including requested duration,
staffing, non-paid work scope, and conditions under which paid validation could
later be considered.]

## 2. Problem And Stakes

Repository teams do not deploy coding agents against an abstract benchmark
distribution. They deploy them against future issues, APIs, test conventions,
dependency constraints, review norms, and failure modes in their own codebase.
A benchmark can be executable and fair while still being weak evidence for
that team's future workload.

The central condition is target-repository shift. General benchmark scores,
large generated task pools, and uncalibrated same-repo samples may all miss the
distribution that matters: later work in the repository where the ACUT will be
used. If that gap remains unresolved, teams risk tuning, selecting, or trusting
coding agents from evidence that is auditable in general but not
decision-relevant for their repository.

The practical stakes are threefold:

- Evaluation: teams need estimates of future repository success rate, not only
  global rank or aggregate public benchmark pass rate.
- Tuning: agent developers need feedback that identifies which repository
  strata, task families, or source reservoirs matter for improvement.
- Governance: benchmark reports need uncertainty, leakage, source-quality, and
  adapter boundaries so claims do not outrun the evidence.

Barcarolle therefore proposes a benchmark compiler, not another task factory
or public leaderboard. Task generators improve the candidate supply layer.
Barcarolle decides how candidate supply becomes a calibrated, versioned,
repo-specific benchmark release.

[NEEDS CITATION: concise comparison to SWE-bench-family, SWE-Bench Pro,
SWE-bench-Live, SWE-smith, SWE-Bench++, R2E-Gym, and related generated-task or
live-benchmark systems.]

## 3. Research Question And North Star

The research question is:

```text
For a target repository r and ACUT configuration a, can a compiled benchmark
release B_{r,tau} estimate future target-repo success W_r(a) better than simple
repo-local or generic alternatives?
```

The estimand is future target-repo ACUT success rate:

```text
W_r(a) = E_{x ~ future target-repo work}[success(a, x)]
```

The benchmark score is a candidate predictor of that future success rate. A
Barcarolle claim becomes strong only when a benchmark release predicts
outcome-unseen future work better than preregistered baselines under a frozen
ACUT, task-supply, adapter, metric, and invalid-cell policy.

Current claim boundary:

```text
Phase 1 supplies traction evidence and a credible validation path. It does not
establish formal predictive validity.
```

This distinction governs the rest of the report. Retrospective pseudo-future
analysis can motivate candidate selection, debug baselines, and identify
failure modes. It cannot by itself establish predictive validity. A formal
predictive-validity claim requires true future holdout evidence or a strict
preregistered rolling-origin design with enough support.

[NEEDS FIGURE: north-star validation design showing target repo history,
compiled benchmark release, future work window, ACUT outcomes, simple
baselines, and prediction-error metrics.]

[NEEDS DECISION: final wording for whether the next formal estimand is
per-adapter, adapter-specific, or a preregistered ACUT mixture.]

## 4. Barcarolle Thesis And Boundary

Barcarolle's thesis is that repo-specific benchmark releases should be
compiled, calibrated, and validated against future target-repository work. The
research object is the release construction and evidence model, not the ACUT
harness.

The ACUT owns its own file search, editing strategy, prompts, tools, retrieval,
runtime budget, public-test policy, retry behavior, and model calls. Barcarolle
provides solver-visible task statements and allowed context, builds clean
solver workspaces, invokes a configured ACUT harness against those workspaces,
captures the resulting diff, replays it in a verifier workspace, injects
private oracle material only in the verifier workspace, and records score,
cost, latency, and sanitized artifacts.

Barcarolle is also not a general task generator. It may use internal
repo-history mining, public issue/PR context, external task systems, synthetic
tasks, or private customer regressions as candidate supply. Those sources are
inputs. The compiler contribution is deciding which certified candidates enter
the release, how they are stratified or weighted, how splits are defined, how
uncertainty is reported, and how future validation is interpreted.

The project boundary excludes:

- reimplementing ACUT internals;
- treating one-shot chat-completion diff generation as the primary scoreable
  protocol;
- making a public leaderboard the central deliverable;
- making task-generation yield the core research claim;
- treating license issuance or deployment authorization as the Phase 1
  research product.

[NEEDS CITATION: one paragraph contrasting benchmark compilation against task
generation, live benchmark maintenance, and agent-training environment
production.]

## 5. Proposed Benchmark-Compiler Design

### 5.1 Inputs

A Barcarolle compiler instance is defined by:

```text
target repository r
time cutoff tau
candidate task sources S
ACUT boundary A
evaluation budget C
target-work distribution assumptions T_r
tuning or evaluation objective O
```

The design requires explicit source, cutoff, and ACUT boundaries because a
score is not interpretable without knowing what future work it is meant to
predict and which agent configuration produced it.

### 5.2 Compiler Layers

The proposed system has six layers:

| Layer | Proposal role |
| --- | --- |
| Task source adapters | Normalize candidate tasks from repo history, public issue/PR context, external systems, synthetic tasks, and private regressions. |
| Task certification | Gate replayability, oracle validity, flakiness, ambiguity, leakage, source quality, task boundary, and cost. |
| Target-work profile modeling | Estimate future-work strata from pre-cutoff public or user-supplied signals, with support and uncertainty labels. |
| Benchmark assembly and weighting | Select, split, and optionally weight certified tasks under budget and support constraints. |
| Score calibration and uncertainty | Report prediction error, intervals or qualitative uncertainty, insufficient-support labels, and invalid-cell sensitivity. |
| Tuning and evaluation interfaces | Emit scorecards, failure labels, cost summaries, and optimizer-readable outputs without taking over the ACUT harness. |

[NEEDS FIGURE: compiler architecture showing source adapters through release
score model, plus future-work validation feedback.]

### 5.3 Release Output

The output is a versioned benchmark release, not a raw task list. A release
contains:

- certified task set;
- task strata and taxonomy;
- dev, eval, canary, and holdout split definitions where applicable;
- source and oracle metadata;
- leakage, ambiguity, flakiness, and replay reports;
- selection and weighting policy;
- aggregation and uncertainty rules;
- adapter and ACUT boundary statement;
- failure taxonomy;
- refresh policy;
- sanitized artifact manifest.

[NEEDS TABLE: release artifact schema with required fields, owner, and claim
function.]

### 5.4 Candidate Assembly Policy

The next candidate policy should be presented as an inspectable selector, not
as the whole Barcarolle compiler. The current frozen candidate is best named:

```text
coverage_constrained_unweighted_v1_with_labeled_fallbacks
```

It is deterministic and outcome-blind under the current audit, with a fixed
per-repo budget and forbidden outcome inputs. It remains a candidate for
hardening, not a validated predictive compiler. Its `boltons` fallback changes
the claim and must be visible in any future validation.

[NEEDS PSEUDOCODE: candidate benchmark assembly policy, including supported
feature checks, coverage objective, deterministic tie-breaks, fallback route,
and forbidden outcome inputs.]

[NEEDS DECISION: fallback-share threshold above which the primary
coverage-policy claim is invalid or must be reported only as a composite
policy.]

[NEEDS RESULT: ablation showing what the coverage objective contributes beyond
repo-stratified, temporal-recent, and many-seed random baselines.]

## 6. Validation Strategy For Predictive Validity

### 6.1 Study Modes And Claim Strength

The validation plan must separate evidence classes:

| Evidence class | Can support | Cannot support |
| --- | --- | --- |
| Retrospective pseudo-future replay | traction, debugging, baseline comparison, proposal motivation | formal predictive-validity claims |
| Strict preregistered rolling-origin with outcome-unseen future cells | conditional predictive evidence within the frozen scope | broad claims outside the preregistered repos, adapters, and supply |
| True future holdout | strongest route to repo-specific predictive-validity evidence | claims outside the frozen estimand and release boundary |

Pseudo-future replay is useful because it can reveal whether a policy is worth
challenging. It is not enough for a final predictive-validity claim because the
task universe, features, repositories, and fallback decisions may already have
been influenced by inspected outcomes.

[NEEDS DECISION: whether the next approval package treats strict rolling-origin
as sufficient for a limited claim, or requires true future holdout before any
predictive-validity language.]

### 6.2 Baselines

A validation result is only meaningful against strong simple baselines. The
baseline suite should include, at minimum:

- temporal recent baseline with the same budget, eligibility, and frozen
  tie-breaks;
- repo unweighted same-budget baseline;
- repo stratified-by-target-profile baseline;
- many-seed random same-budget distribution with percentile reporting;
- baseline envelope against the best preregistered simple baseline overall and
  by diagnostic slice;
- external or general benchmark baseline where candidate supply and licensing
  permit a clean comparison.

[NEEDS RESULT: many-seed random baseline distribution and candidate percentile
for the current candidate.]

[NEEDS RESULT: baseline-envelope comparison against the best preregistered
simple baseline overall, per adapter, per repo, and per time window.]

### 6.3 Metrics And Reporting

Primary reporting should be adapter-stratified. Pooled summaries can appear
only as secondary diagnostics unless the estimand explicitly defines an ACUT
mixture.

Primary metrics:

- MAE against future target-repo pass rate;
- catastrophic miss rate with a numeric threshold;
- signed error by adapter, repo, and window;
- invalid/non-scoreable sensitivity;
- policy-compliance status.

Secondary metrics:

- RMSE;
- calibration interval coverage if intervals are available;
- uncertainty or bootstrap/randomization summaries;
- cost and latency by ACUT configuration.

[NEEDS DECISION: catastrophic-miss threshold and invalid-cell sensitivity rule.]

[NEEDS ANALYSIS: power and budget note explaining what effect size a future
paid validation could plausibly detect.]

### 6.4 Success Gates

The future success rule should be joint, not "margin or majority." A candidate
should need to satisfy all applicable gates:

- beat the best preregistered simple baseline by a practically meaningful MAE
  margin;
- improve more diagnostic slices than it worsens, with ties handled explicitly;
- be non-inferior on each adapter or narrow the claim to the adapter where
  support exists;
- avoid concentration in one repo, one adapter, or one time window;
- keep catastrophic misses within the predefined tolerance;
- pass invalid-cell and policy-compliance sensitivity checks;
- remain within the frozen source-quality and fallback thresholds.

[NEEDS DECISION: final practical MAE margin, relative improvement threshold,
slice-stability rule, repo/window non-concentration rule, and adapter
non-inferiority rule.]

## 7. Preliminary Evidence And Feasibility

Phase 1 evidence matters only where it answers three approval questions:

```text
Is the problem real?
Is the work technically tractable?
Is there enough traction to justify the next phase?
```

### 7.1 The Problem Is Real

The old weighted target-profile design failed cleanly. The paid pilot completed
its planned evidence and reported weighted gaps of `0.3148` for `attrs` and
`0.7481` for `boltons`, while simple same-budget baselines reported `0.25` and
`0.125`. The local bakeoff reproduced the metrics and diagnosed the metadata
objective as underidentified under sparse support. This is negative evidence
against naive weighting, but positive evidence that construction choices
materially affect the benchmark estimate.

Evidence:
`experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`;
`experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md`.

### 7.2 The Work Is Technically Tractable

Phase 1 showed that Barcarolle can preserve benchmark-side boundaries: prepare
workspace-mode ACUT runs, capture and replay diffs, keep hidden oracle material
out of solver workspaces, report endpoint and policy checks, repair source
context without rewriting outcomes, and freeze an outcome-blind candidate
policy before future score joins.

Source and adapter handling are part of this tractability result. Click source
context was repaired for all frozen click tasks with no paid LLM calls and no
paid ACUT solver cells. Adapter-level reporting now treats Codex and Kilo as
ACUT configurations rather than model-only comparisons.

Evidence:
`experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md`;
`experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md`;
`experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md`.

### 7.3 There Is Traction, Not Validation

The no-paid retrospective pseudo-future analysis found weak directional signal:
the best simple baseline was `temporal_recent_baseline` with MAE `0.2149`, and
the best promoted research candidate was `coverage_constrained_unweighted`
with MAE `0.209`. The uncertainty report labeled the result
`directional_only`, `too_sparse_for_formal_predictive_validity`, and
`traction_evidence_only`.

The signal is fragile. The candidate was worse than the temporal baseline on
`codex_workspace` (`0.267` versus `0.2417`) and better on `kilo_workspace`
(`0.151` versus `0.1881`). This supports route-finding and protocol hardening,
not a predictive-validity claim.

Evidence:
`experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md`;
`experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md`;
`experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md`;
`experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md`.

[NEEDS TABLE: one-page preliminary evidence summary with reader question,
claim strength, key result, supporting report, limitation, and remaining
placeholder.]

## 8. Project Plan, Decision Gates, And Resource Ask

The next phase should be pulled by the predictive-validity claim, not by a
generic expansion of task supply. The work packages are proposal-level units:

| Work package | Output | Approval function |
| --- | --- | --- |
| Comparator and literature framing | cited related-work section and benchmark/task-generator comparison | shows Barcarolle is a distinct benchmark-compiler project |
| Evidence consolidation | final evidence table, adapter/repo fragility summary, fallback accounting, baseline tables | fills proposal blanks without overclaiming |
| Compiler policy hardening | candidate policy pseudocode, fallback threshold, ablation against simple baselines | makes the candidate object inspectable |
| Validation protocol hardening | frozen estimand, study mode, baselines, metrics, invalid-cell rules, success gates, power note | prevents paid or future validation from becoming post-hoc |
| Proposal package completion | final report, appendices, reviewer response, decision memo or presentation | gives reviewers an approval-ready artifact |

Decision gates:

- Gate 1: all prohibited claims remain excluded.
- Gate 2: every result-dependent claim has either evidence or a precise
  `[NEEDS ...]` placeholder.
- Gate 3: baseline, adapter, fallback, invalid-cell, and uncertainty rules are
  frozen before any future outcomes are joined.
- Gate 4: any paid-validation discussion is blocked unless no-paid evidence
  and protocol gates justify it.
- Gate 5: the final approval artifact distinguishes task supply, benchmark
  compilation, ACUT harnessing, and productization.

[NEEDS NUMBER: requested no-paid research duration and staffing.]

[NEEDS NUMBER: upper-bound paid-validation budget only if the protocol gates
later authorize a paid decision.]

[NEEDS DECISION: whether the next approval artifact is a full report, short
decision memo, slide deck, or combined packet.]

## 9. Risks, Objections, And Mitigations

### Objection: The failed weighted design shows the compiler idea failed.

Response: The failed weighted design should not be defended. It is evidence
that naive high-dimensional metadata matching and uncalibrated weights are
unsafe under sparse support. The compiler research claim survives only if the
next phase learns from that failure through stronger baselines, support
thresholds, fallback rules, and outcome-unseen validation.

Mitigation:

- keep the old weighted target-profile design as diagnostic or negative-control
  evidence;
- require no-paid local evidence before promoting any new weighted policy;
- report insufficient support instead of forcing weights.

### Objection: Stronger task generators make Barcarolle unnecessary.

Response: Stronger task generators improve candidate supply. They do not decide
which tasks should enter a repo-specific release, how the release should be
stratified, how source reservoirs should be capped, how adapter results should
be interpreted, or whether the release predicts future work.

Mitigation:

- treat external generators and Task Supply v2 as source adapters;
- require local certification before generated tasks enter a release;
- keep predictive benchmark compilation as the contribution.

### Objection: The retrospective edge is too small.

Response: Correct. The current edge is traction evidence only. It does not meet
the standard for formal predictive validity and should not authorize paid
validation.

Mitigation:

- add many-seed random and baseline-envelope comparisons;
- require adapter-stratified support or narrow the claim;
- define a practically meaningful MAE margin with power/budget context.

### Objection: The current candidate is a composite policy because of fallback.

Response: The proposal should state this directly. The object is
`coverage_constrained_unweighted_v1_with_labeled_fallbacks`, not a uniformly
applied coverage policy.

Mitigation:

- quantify fallback share by repo and task slot;
- set a threshold at which the coverage-policy claim is invalid;
- report including and excluding fallback repos if validation proceeds;
- repair feature support where that is the cleaner path.

### Objection: Adapter differences make the result hard to interpret.

Response: Adapter differences are part of the ACUT configuration. They should
be reported as such rather than pooled away.

Mitigation:

- report adapter-level metrics first;
- decide whether the claim is per-adapter, adapter-specific, or mixture-based;
- prevent pooled improvement from rescuing adapter-level failure.

### Objection: The validation design can still become post-hoc.

Response: The proposal should freeze the components that make interpretation
possible before future outcomes are joined.

Mitigation:

- freeze repos, cutoffs, candidate supply, feature extraction, baselines,
  seeds, adapters, metrics, invalid-cell rules, and success thresholds;
- mark pseudo-future replay as traction only;
- require a separate paid-readiness decision before paid ACUT validation.

[NEEDS TABLE: risk register with likelihood, impact, mitigation owner, and
decision gate.]

## 10. Expected Deliverables

The approved project should produce:

- a final proposal report with all placeholders resolved or explicitly
  deferred;
- a benchmark-compiler design document with diagrams and release schema;
- a candidate policy specification with pseudocode, support checks, and
  fallback governance;
- a validation protocol that separates traction evidence from predictive
  validity;
- a baseline suite with random percentile, temporal, stratified, unweighted,
  and external/general comparisons where feasible;
- adapter-stratified score reporting templates;
- a preliminary evidence table and appendix links;
- a claim-boundary checklist for reviewers;
- a sanitized artifact manifest for every evidence package;
- a decision memo or presentation for approval.

[NEEDS DELIVERABLE DETAIL: exact artifact list, acceptance criteria, and
reviewer-facing owner for each deliverable.]

## 11. Appendices And Evidence Index

The main body intentionally avoids a chronological Phase 1 ledger. Detailed
evidence should be attached or indexed here.

### Appendix A: Current Claim Boundary

Primary guardrails:

- predictive validity is the north star, not an established result;
- the short-term claim is traction evidence plus a credible validation path;
- paid validation is not authorized by the current evidence;
- pseudo-future replay supports traction and debugging only;
- adapter-level results are primary;
- Task Supply v2 is source infrastructure, not the core research claim.

Evidence:
`docs/research/phase-1-proposal-claim-boundary.md`;
`docs/research/phase-1-proposal-evidence-todo-matrix.md`.

### Appendix B: Preliminary Evidence Reports

Key reports:

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
- `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_validation_protocol.md`
- `experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md`

[NEEDS APPENDIX TABLE: compact report index with evidence type, claim function,
numeric result, limitation, and whether it belongs in main text.]

### Appendix C: Related Work And External Review Inputs

Sources to integrate:

- `/Users/chenmohan/Downloads/barcarolle-research-0519.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0526.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0526-1.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0530.md`

[NEEDS CITATION: replace local research-plan references with reviewer-facing
citations where claims depend on public literature.]

[NEEDS DECISION: which external-review findings are accepted now, considered
for no-paid evidence work, deferred, or rejected as scope expansion.]

### Appendix D: Placeholder Register

P0 before reviewer-ready proposal:

- [NEEDS CITATION: related-work comparison for benchmark families and task
  generation systems]
- [NEEDS FIGURE: north-star validation design]
- [NEEDS FIGURE: compiler architecture]
- [NEEDS PSEUDOCODE: candidate benchmark assembly policy]
- [NEEDS TABLE: release artifact schema]
- [NEEDS TABLE: one-page preliminary evidence summary]
- [NEEDS RESULT: many-seed random baseline distribution and candidate
  percentile]
- [NEEDS RESULT: baseline-envelope comparison]
- [NEEDS RESULT: coverage objective ablation]
- [NEEDS DECISION: fallback-share threshold]
- [NEEDS DECISION: estimand and adapter claim]
- [NEEDS DECISION: catastrophic-miss and invalid-cell rules]
- [NEEDS DECISION: joint success gate]
- [NEEDS ANALYSIS: power and budget note]
- [NEEDS NUMBER: no-paid staffing and duration]
- [NEEDS NUMBER: conditional paid-validation budget ceiling]
- [NEEDS DELIVERABLE DETAIL: acceptance criteria and owners]

P1 before final publication or broader project review:

- [NEEDS APPENDIX TABLE: report evidence index]
- [NEEDS DECISION: approval artifact format]
- [NEEDS DECISION: external-review triage categories]
- [NEEDS CITATION: public-literature replacements for local research-plan
  references]
