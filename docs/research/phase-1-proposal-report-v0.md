# Barcarolle Phase 1 Proposal Report V0

Status: proposal argument draft, 2026-05-30.

This report argues for continued Barcarolle research toward repo-specific
predictive validity. It is not the internal milestone roadmap. Roadmap and
claim-planning details live in
`docs/research/phase-1-proposal-roadmap-and-claim-planning.md`; this report
uses only the next-phase detail needed to support the proposal argument.

## 1. Executive Thesis

Teams that evaluate coding agents face a practical prediction problem: a
public benchmark score or a large generated task pool does not directly tell
them how an agent configuration will perform on future work in their own
repository. Barcarolle's research object is the benchmark-construction layer
between task supply and agent evaluation: given a target repository, candidate
tasks, an agent configuration boundary, and a limited evaluation budget, which
tasks should be selected, split, weighted or left unweighted, refreshed, and
interpreted as evidence about future target-repository performance?

The long-term north star is predictive validity for repo-specific benchmarks:

```text
Can a Barcarolle-compiled repo-specific benchmark predict future target-repo
ACUT performance better than naive same-repo sampling, general benchmark
scores, or other simple baselines?
```

Phase 1 does not prove that north-star claim. Its defensible proposal claim is
narrower and more useful:

```text
Phase 1 shows that repo-specific benchmark construction is a real, measurable,
and technically tractable research problem. The phase produced a clean negative
result for naive weighting, a conservative mainline correction, source-quality
and adapter-reporting governance, weak retrospective route-finding signal, and
a frozen outcome-blind candidate policy that is ready for no-paid adversarial
review and protocol hardening.
```

That claim justifies continued research. It does not authorize a paid
predictive-validity run, and it does not say Barcarolle is already a validated
predictive benchmark compiler.

## 2. The Research Problem

General SWE benchmarks and scalable task generators answer important questions
about broad agent capability and task production. Barcarolle addresses a
different question: how should a small, auditable benchmark for one target
repository be compiled so that its score can become evidence about later work
in that same repository?

The condition is target-repository shift. A repository team choosing an Agent
Configuration Under Test, or ACUT, cares about future changes, bug reports,
APIs, dependency constraints, test conventions, review norms, and failure modes
in its own codebase. A benchmark that is executable and fair in the general
sense can still be weak evidence for that team's future workload if task
selection, split construction, baseline choice, source quality, adapter
handling, or uncertainty reporting are misaligned with the target repository.

The consequence is practical. Without repo-specific predictive evidence,
teams risk tuning or trusting coding agents from evidence that is auditable but
not decision-relevant for the repository where the agent will operate. The
proposal therefore asks readers to fund or continue a benchmark compiler, not
another leaderboard and not another task factory.

[NEEDS BACKGROUND PARAGRAPH: concise comparison against SWE-bench-family,
SWE-smith-style, SWE-Bench++-style, and live benchmark systems using vetted
citations or local evidence.]

## 3. Why Existing Benchmarks And Task Generators Do Not Solve It

Stronger task generators improve the supply layer, but they do not by
themselves solve the compiler problem. They can increase the number of
candidate tasks, improve environment construction, or provide better
issue-like statements. Barcarolle still has to decide which candidates enter a
repo-specific release, how source reservoirs are capped and labeled, how
leakage and ambiguity are certified, how target-work distribution is modeled,
how score uncertainty is reported, and how the release is validated against
future work.

This distinction is already part of the project boundary. `AGENTS.md` and
`docs/architecture/system-design.md` define Barcarolle as a target-repository
benchmark compiler, not an ACUT harness, general SWE task factory, agent-license
product, or public leaderboard. The ACUT owns search, editing, tool use, retry
policy, model calls, and harness behavior. Barcarolle builds clean solver
workspaces, provides solver-visible task context, captures final diffs,
replays them in verifier workspaces, and records score, cost, latency, and
sanitized artifacts.

The Task Supply v2 bakeoff reinforces the same warrant. It found that broader
local mining increased candidate visibility, but certified supply was still
not paid-ready; it recommended continued internal repo-history v2 work,
certification, source-mixing policy, and external-source adapters as later
spikes. The result supports task supply as Layer 1 infrastructure. It does not
move the core proposal claim away from benchmark compilation and predictive
validation. Evidence:
`experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md`.

## 4. Barcarolle's Approach

Barcarolle compiles candidate task pools into calibrated, versioned
repo-specific benchmark releases. The architecture separates six layers:
source adapters, task certification, target-work profile modeling, assembly
and weighting, score calibration and uncertainty, and tuning/evaluation
interfaces. Evidence: `docs/architecture/system-design.md`.

The key output is not a pile of tasks. It is a benchmark release with an
explicit evaluation boundary: certified task set, strata, splits, source and
oracle metadata, leakage and replay reports, aggregation rules, uncertainty
labels, failure taxonomy, and refresh policy. The research question is whether
that release estimates future target-repo ACUT success rate better than simple
alternatives.

This framing also explains why negative evidence matters. If a construction
rule fails cleanly, the project learns about the estimator. If source quality
or adapter handling changes interpretation, those are not side issues; they
are part of the benchmark boundary that makes future predictive evidence
auditable.

[NEEDS FIGURE: north-star validation design showing target repo history,
compiled benchmark release, future work window, ACUT performance, baselines,
and prediction-error metrics.]

## 5. Phase 1 Evidence

### 5.1 Naive Weighted Matching Failed Cleanly

The weighted design paid pilot completed and scored all planned cells:
`44/44/44`. Its weighted gaps were `0.3148` for `attrs` and `0.7481` for
`boltons`, while simple same-budget baselines had gaps of `0.25` for `attrs`
and `0.125` for `boltons`. The pilot explicitly made no precision-target
predictive-validity claim. Evidence:
`experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`.

The local algorithm bakeoff then reproduced the pilot metrics and diagnosed
the old metadata objective as underidentified: near-optimal metadata splits
could have materially different observed gaps, and block-randomized or
shrinkage-weighted variants did not show a stable promotion signal. The
decision kept simple stratified designs as the conservative mainline. Evidence:
`experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md`.

The warrant is not "weighting is impossible." The warrant is that sparse,
high-dimensional metadata matching and uncalibrated marginal weights can look
precise while failing to estimate future performance. That failure makes the
benchmark-construction problem more concrete.

### 5.2 Exploratory Paid Runs Were Interpretable, Not Validating

The three-repo paid pilot recorded `120` planned, completed, and scoreable
cells, a scoreability rate of `1.0`, `0` policy violations, endpoint compliance
pass, and a `repo_stratified` primary design with primary gap `0.1`. The report
labels the run complete and threshold-met for pilot purposes, while stating
that predictive validity was not established. Evidence:
`experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md`.

This matters because the proposal is not built only on successful outcomes. It
is built on the ability to produce interpretable outcomes without changing the
primary design after results are known, exposing hidden oracle material, or
collapsing exploratory pilot evidence into a validation claim.

### 5.3 Adapter And Source Boundaries Became Part Of The Evidence

The blocked split supplement diagnostics concluded that Kilo's higher pass
rate can be reported as an ACUT-configuration result, not a model-only claim,
and that more paid cells were not recommended. Evidence:
`experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md`.

The click source-context repair upgraded all `30` frozen click tasks through
sanitized public issue and pull-request context, with `0` paid LLM calls and
`0` paid ACUT solver cells. This removed the visible click title-only/minor-risk
source-quality caveat for the three-repo story without rewriting completed
paid outcomes. Evidence:
`experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md`.

The warrant is that a repo-specific benchmark cannot treat source quality and
adapter boundaries as bookkeeping. If task statements are weak or adapter
effects are pooled away, the benchmark score becomes harder to interpret as
future target-repo evidence.

### 5.4 Retrospective Signal Is Directional Only

The no-paid retrospective pseudo-future analysis found weak directional signal
for the best Barcarolle-style candidate. The best simple baseline was
`temporal_recent_baseline` with MAE `0.2149`; the best Barcarolle candidate
was `coverage_constrained_unweighted` with MAE `0.209`. The uncertainty report
labels the result `directional_only`, `too_sparse_for_formal_predictive_validity`,
and `traction_evidence_only`. Evidence:
`experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md`,
`experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md`,
`experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md`.

The adapter-level metrics are the most important limitation. The candidate was
worse than `temporal_recent_baseline` on `codex_workspace` (`0.267` versus
`0.2417`) and better on `kilo_workspace` (`0.151` versus `0.1881`). Evidence:
`experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md`.

This evidence supports route finding, not validation. It says the next phase
has a concrete candidate and concrete failure modes to challenge. It does not
say the candidate has passed a predictive-validity threshold.

### 5.5 A Reviewable Candidate Now Exists

The candidate policy protocol froze `coverage_constrained_unweighted_v1` as a
deterministic, outcome-blind policy with budget `6` per repo and seed
`2026053001`. Forbidden inputs include terminal outcomes, pass/fail labels,
adapter outcomes, score-table rows, raw ACUT transcripts, and hidden verifier
output. The outcome-blindness audit reported `true`, with `0` forbidden-field
violations and no score-table reads for selection. Evidence:
`experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_policy_spec.md`,
`experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_outcome_blindness_audit.md`.

The selection manifest chose `18` tasks across `attrs`, `boltons`, and `click`
and recorded `9` coverage gaps. `attrs` and `click` used the coverage policy
without fallback; `boltons` selected `6` tasks with
`insufficient_feature_support` fallback. Evidence:
`experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md`.

The honest name for the current object is therefore:

```text
coverage_constrained_unweighted_v1_with_labeled_fallbacks
```

It is useful because it is deterministic, outcome-blind, and challengeable. It
is limited because one repo falls back and the retrospective edge is weak.

[NEEDS TABLE: one-page Phase 1 evidence summary with claim strength,
supporting report, numeric result, and limitation.]

## 6. Interpretation: What This Evidence Shows And Does Not Show

Phase 1 shows that benchmark construction choices matter. The weighted pilot
failed despite clean execution; the local bakeoff found the old objective
underidentified; adapter-stratified reporting changed interpretation; source
repair changed the source-quality boundary; and the retrospective analysis
exposed both a candidate route and its fragility. Those are substantive
research findings about the benchmark compiler boundary.

Phase 1 also shows that the work is technically tractable. The project can
prepare solver workspaces, enforce benchmark-side policy checks, capture and
replay diffs, maintain endpoint and artifact boundaries, repair source context
without paid reruns, freeze outcome-blind policies, and report no-paid
retrospective evidence with limitations attached.

The evidence does not show that Barcarolle has achieved predictive validity.
There is no strict future holdout result. The current retrospective edge over
the best simple baseline is small. Candidate support is adapter- and
repo-fragile. `boltons` fallback makes the current policy composite. The
success criteria need hardening beyond a loose margin-or-majority rule. Paid
validation remains blocked by default.

The safest current claim is therefore the proposal claim, not the north-star
claim: Barcarolle has made repo-specific predictive validity concrete enough
to pursue with stronger baselines, stricter future-validation design, and
clearer fallback governance.

## 7. Research Agenda Toward Predictive Validity

The next phase should be pulled by the predictive-validity question, not by a
generic expansion of task supply. The immediate work is no-paid hardening:
triage adversarial review, consolidate proposal-critical evidence, define the
current candidate and fallback limits precisely, and replace the loose success
rule with a joint gate that can be frozen before any future outcomes are
joined.

The validation path should distinguish three evidence classes:

| Evidence class | What it can support | What it cannot support |
| --- | --- | --- |
| Pseudo-future replay over already inspected outcomes | Traction, debugging, baseline comparison, proposal motivation | Predictive-validity claims |
| Strict preregistered rolling-origin with outcome-unseen future cells | Conditional predictive evidence if support and thresholds are adequate | Broad generality beyond the frozen scope |
| True future holdout | The preferred route to repo-specific predictive-validity evidence | Claims outside the preregistered repos, adapters, and task supply |

Future success criteria should require more than pooled improvement. They
should specify the best simple baseline, adapter-stratified success or an
adapter-specific claim, repo/window non-concentration, fallback-share limits,
invalid-cell sensitivity, catastrophic-miss tolerance, and a practical MAE
margin justified by power or uncertainty analysis. Evidence:
`experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_validation_protocol.md`,
`experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_success_criteria.md`,
`/Users/chenmohan/Downloads/barcarolle-research-0530.md`.

[NEEDS ANALYSIS: many-seed random baseline and candidate percentile.]

[NEEDS ANALYSIS: baseline envelope against the best preregistered simple
baseline overall and per adapter/repo slice.]

[NEEDS NUMBER: fallback share by repo and task slot, with a policy threshold
for when fallback invalidates a primary coverage-policy claim.]

[NEEDS NOTE: power and budget limits for any future paid validation.]

## 8. Risks, Objections, And Responses

Objection: The failed weighted design shows Barcarolle's compiler idea does not
work.

Response: The failure shows that one naive compiler design should not be
promoted. It also shows why the compiler problem is worth studying: metadata
matching, weighting, target-profile support, and split construction can change
observed prediction error in diagnosable ways. The proposal should not defend
the failed weighted design. It should defend the research program that learned
from that failure.

Objection: Stronger task generators will make Barcarolle unnecessary.

Response: Stronger generators improve candidate supply, and Barcarolle should
reuse them where licensing, provenance, and certification permit. They do not
replace repo-specific release construction, source caps, leakage review,
adapter-stratified reporting, target-profile modeling, or validation against
future work. Task supply is necessary infrastructure; predictive benchmark
compilation remains the research claim.

Objection: The retrospective edge is too small to justify a predictive-validity
claim.

Response: Correct. The report should not make that claim. The edge justifies
only route-finding and protocol-hardening work: stronger baselines, many-seed
random comparisons, adapter/repo fragility reporting, fallback accounting, and
future outcome-unseen validation.

Objection: The current candidate is ambiguous because `boltons` uses fallback.

Response: The proposal should state the ambiguity rather than hide it. The
current object is a composite selector with labeled fallback behavior. Future
validation should either repair `boltons` feature support, report including
and excluding fallback repos, or freeze a fallback threshold before paid work.

Objection: Adapter differences make the result hard to interpret.

Response: Adapter differences are part of the ACUT configuration. The response
is not to pool them away, but to report adapter-level results first and define
whether a future claim is per-adapter, adapter-specific, or about a
preregistered ACUT mixture.

## 9. Proposal Ask / Next Phase

The proposal ask is continued no-paid research and writing work toward a
reviewer-ready predictive-validity proposal, followed only later by a paid
validation decision if the hardened evidence warrants it. The next phase should
produce:

- a proposal-ready evidence table that separates supported, diagnostic,
  traction-only, draft, and prohibited claims;
- a strengthened baseline package, including many-seed random and a stricter
  temporal comparator;
- explicit fallback accounting for
  `coverage_constrained_unweighted_v1_with_labeled_fallbacks`;
- a validation protocol that excludes pseudo-future replay from
  predictive-validity claims and defines a joint success gate;
- a concise reviewer response explaining why Barcarolle is a repo-specific
  benchmark compiler rather than a task generator project.

Paid ACUT validation should remain unauthorized until those no-paid gates are
closed. The near-term value of Barcarolle is not that Phase 1 already proves
the final claim. It is that Phase 1 turned a broad ambition into a concrete,
auditable research path toward testing whether repo-specific benchmark releases
can predict future target-repository ACUT performance.
