# Barcarolle Phase 1 Proposal Report V0

Status: Draft M1 skeleton, 2026-05-30.

This report is a proposal-facing skeleton. It is designed to be readable before
all evidence gaps are filled. Sections marked `Draft` and placeholders marked
`[NEEDS ...]` must be resolved before the text is treated as proposal-ready.

## 1. Problem

Public SWE benchmarks and scalable task generators answer an important but
different question from the one Barcarolle is trying to answer. They can show
how an agent performs on a general corpus, or how many executable tasks a
pipeline can produce, but they do not by themselves say how a small benchmark
for one target repository should be selected, weighted, split, refreshed, and
interpreted to estimate future work in that same repository.

The practical problem is target-repository shift. A team choosing or tuning an
agent configuration does not only need to know whether that configuration ranks
well on a public benchmark. It needs to know whether the configuration will
succeed on future changes, bug reports, APIs, tests, dependency constraints,
review conventions, and failure modes in its own repository. The benchmark
construction question is therefore not merely "can we make tasks?" It is:
which candidate tasks should count, in what proportions, with which baselines
and uncertainty labels, under a fixed evaluation budget?

Barcarolle is scoped to that benchmark-construction problem. The repository
instructions and system design define Barcarolle as a target-repository
benchmark compiler, not an ACUT harness, public leaderboard, agent-license
product, or general SWE task factory. The ACUT owns its own search, editing,
tool-use, retry, and model-call behavior; Barcarolle builds a clean workspace,
provides solver-visible task context, captures the resulting diff, replays the
diff in a verifier workspace, and records score, cost, latency, and sanitized
artifacts. Evidence: `AGENTS.md`, `docs/architecture/system-design.md`.

Draft claim for this section:

```text
The bottleneck Barcarolle studies is not task production alone. It is benchmark
compilation under target-repository shift: selecting and interpreting a small,
auditable task set so its score can become evidence about future target-repo
ACUT performance.
```

[NEEDS BACKGROUND PARAGRAPH: concise comparison against SWE-bench-family and
task-generator systems using only vetted local sources or freshly verified
citations.]

## 2. North Star

The north star is predictive validity for repo-specific coding-agent
benchmarks. The long-term question is:

```text
Can a Barcarolle-compiled repo-specific benchmark predict future target-repo
ACUT performance?
```

The estimand is future target-repo ACUT success rate. A Barcarolle benchmark
score is useful to the extent that it predicts that future success rate better
than naive same-repo sampling, generic benchmark scores, or other simple
baselines. This is a research target, not a result already established by
Phase 1.

The north star also sets a boundary on the proposal. It prevents Barcarolle
from becoming a generic task factory narrative, but it also prevents the
proposal from claiming that current pilots already validate the compiler. The
right Phase 1 claim is narrower: Phase 1 produced traction evidence, negative
evidence, governance improvements, and a concrete validation agenda.

[NEEDS FIGURE: north-star validation design showing target repo history,
compiled benchmark release, future work window, ACUT performance, and
prediction-error metrics.]

## 3. Barcarolle Thesis

Barcarolle's thesis is that task generation is becoming a supply layer, while
benchmark compilation remains a separate target-repository research problem.
External generators, internal repo-history mining, synthetic tasks, manual
canaries, and private regression tasks can all feed candidate supply. They do
not replace the compiler's responsibility to certify tasks, model target work,
assemble and weight a benchmark, report uncertainty, and validate the release
against future target-repo outcomes.

The system design expresses this as layered architecture. Layer 1 adapters
normalize candidate tasks. Layer 2 certification checks replayability, oracle
validity, leakage, ambiguity, flakiness, and cost. Layer 3 models target work
distribution. Layer 4 assembles and weights the benchmark. Layer 5 calibrates
score and uncertainty. Layer 6 exposes tuning and evaluation interfaces.
Evidence: `docs/architecture/system-design.md`.

The proposal should therefore use Task Supply v2 as supporting infrastructure,
not as the core contribution. The source bakeoff found that broader local
mining increased candidate visibility, but certified supply was still not
paid-ready; it recommended continued internal repo-history v2 work, local
certification, source-mixing policy, and external-source adapters only as later
spikes. Evidence:
`experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md`.

Draft thesis:

```text
Barcarolle compiles candidate task pools into calibrated repo-specific
benchmark releases. It is evaluated by whether those releases improve
prediction of future target-repo ACUT performance, not by task count alone.
```

[NEEDS DECISION: whether the proposal uses "compiler" for the whole
Barcarolle system while describing the current candidate as a selector with
labeled fallback behavior.]

## 4. Phase 1 Evidence

Phase 1 produced several kinds of evidence. The most important point is that
they do not all have the same claim strength.

First, the weighted design paid pilot was clean enough to interpret and
negative enough to redirect the project. It planned, completed, and scored
`44/44/44` cells. The weighted design gaps were `0.3148` for `attrs` and
`0.7481` for `boltons`, while simple same-budget baselines did better. The
pilot explicitly made no precision-target predictive-validity claim. Evidence:
`experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`.

Second, the local algorithm bakeoff confirmed that the old metadata objective
was underidentified. It found no stable promotion signal for block-randomized
or shrinkage-weighted candidates and recommended keeping simple stratified
designs as the conservative mainline. Evidence:
`experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md`.

Third, the three-repo paid pilot produced exploratory evidence with clean
benchmark-side accounting. It recorded `120` planned, completed, and scoreable
cells, `0` policy violations, endpoint compliance pass, and a `repo_stratified`
primary design with primary gap `0.1`. It also explicitly stated that
predictive validity was not established. Evidence:
`experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md`.

Fourth, adapter-stratified reporting became a stable interpretation boundary.
The blocked split supplement diagnostics concluded that Kilo's higher pass
rate could be reported as an ACUT-configuration result, not as a model-only
claim, and did not recommend more paid cells. Evidence:
`experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md`.

Fifth, click source-quality repair removed a visible source-context caveat for
the three-repo story. All `30` frozen click tasks were repaired through
sanitized public issue and pull-request context, with `0` paid LLM calls and
`0` paid ACUT solver cells. Evidence:
`experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md`.

Sixth, the no-paid retrospective pseudo-future analysis found weak directional
signal. The best simple baseline was `temporal_recent_baseline` with MAE
`0.2149`; the best Barcarolle candidate was
`coverage_constrained_unweighted` with MAE `0.209`. The uncertainty report
labels the result `directional_only`, `too_sparse_for_formal_predictive_validity`,
and `traction_evidence_only`. Evidence:
`experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md`,
`experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md`,
`experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md`.

Seventh, the candidate policy and validation protocol are now concrete enough
to review. The policy spec froze `coverage_constrained_unweighted_v1`, budget
`6` per repo, seed `2026053001`, and forbidden outcome inputs. The selection
manifest selected `18` tasks, recorded `9` coverage gaps, and showed that
`boltons` fell back because of insufficient feature support. Evidence:
`experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_policy_spec.md`,
`experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md`.

[NEEDS TABLE: one-page Phase 1 evidence summary with claim strength,
supporting report, numeric result, and limitation.]

[NEEDS TABLE: retrospective baseline comparison with candidate, simple
baselines, diagnostic candidates, MAE, catastrophic miss rate, slices, and
claim label.]

## 5. What We Learned

Phase 1 changed the project in four concrete ways.

The first lesson is that naive weighted target-profile matching is not enough.
The old design matched sparse metadata and applied uncalibrated marginal
weights, but that did not produce a reliable estimator. This does not mean
weighting is permanently wrong. It means a small-N, high-dimensional, deterministic
metadata objective can look precise while failing to predict the quantity that
matters. Evidence:
`/Users/chenmohan/Downloads/barcarolle-research-0526.md`,
`experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`.

The second lesson is that clean negative evidence is useful. The paid pilot did
not support the old weighted claim, but because the run was clean and the
policy boundary was recorded, the failure could be interpreted as a design
problem rather than an artifact failure. That is why the conservative mainline
moved toward simple stratified or coverage-constrained candidates rather than
another paid replay of the old design.

The third lesson is that adapter handling is part of the estimand. Codex and
Kilo differences should be reported as ACUT-configuration differences unless
adapter and harness effects are explicitly ruled out. The retrospective metrics
show why this matters: the coverage-constrained candidate was worse than
`temporal_recent_baseline` on Codex and better on Kilo. Evidence:
`experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md`.

The fourth lesson is that pseudo-future evidence is useful only when it is kept
in its lane. Retrospective replay can guide candidate choice, surface baseline
weaknesses, and identify support gaps. It cannot establish predictive validity
if the study design has already been influenced by inspected outcomes.

Draft summary:

```text
The hard problem is not only making tasks. It is building a low-variance,
auditable estimator under sparse target strata, expensive validation, adapter
differences, and incomplete source support.
```

## 6. Current Candidate Path

Draft.

The current candidate should be described as a coverage-constrained unweighted
selector with labeled fallback behavior, not as the full Barcarolle compiler
and not as a validated predictor. The frozen policy is useful because it is
deterministic, outcome-blind, and reviewable. It is also limited because one of
three repos, `boltons`, uses fallback behavior due to insufficient feature
support. Evidence:
`experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md`.

The proposal should therefore use a name such as:

```text
coverage_constrained_unweighted_v1_with_labeled_fallbacks
```

This wording keeps the candidate honest. It allows the next phase to ask
whether a simple coverage-first, low-variance selector is a useful baseline or
stepping stone, while avoiding the stronger claim that the coverage policy has
already validated Barcarolle's full compiler thesis.

[NEEDS NUMBER: fallback share by repo and task slot.]

[NEEDS DECISION: whether `boltons` feature support should be repaired before
any future paid-validation discussion or whether paid-readiness should report
including/excluding fallback repos.]

## 7. Validation Path

Future predictive-validity evidence requires outcome-unseen validation. The
preferred design is a true future holdout. A strict rolling-origin design can
also support a predictive claim if repos, task supply, cutoffs, feature
extraction, baselines, seeds, invalid-cell rules, adapter handling, fallback
rules, and success thresholds are frozen before outcomes are inspected or
joined.

Pseudo-future replay should remain traction evidence only. It can motivate the
proposal, tune no-paid analysis, and prioritize gaps, but it should not be the
basis for the phrase "predictive validity established." This boundary follows
the candidate protocol and the 2026-05-30 adversarial review. Evidence:
`experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_validation_protocol.md`,
`/Users/chenmohan/Downloads/barcarolle-research-0530.md`.

The current success criteria need hardening before paid validation. The frozen
criteria include a minimum MAE margin of `0.01`, a majority-of-slices rule,
adapter-stratified reporting, and a requirement for future outcome-unseen or
preregistered rolling-origin support. The adversarial review argues that the
future rule should become a joint gate rather than a loose margin-or-majority
rule. Evidence:
`experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_success_criteria.md`,
`/Users/chenmohan/Downloads/barcarolle-research-0530.md`.

[NEEDS DECISION: pseudo-future versus predictive-validity boundary wording for
the final proposal.]

[NEEDS EXPERIMENT OR ANALYSIS: many-seed random baseline and candidate
percentile.]

[NEEDS ANALYSIS: baseline envelope against the best preregistered simple
baseline overall and per adapter/repo slice.]

[NEEDS NOTE: power/budget limits for a future paid run.]

## 8. Research Plan

Draft.

The next phase should be pulled by proposal evidence gaps rather than by every
possible experiment branch. The near-term work should triage external review,
consolidate proposal-critical evidence, and harden validation criteria before
any paid ACUT work is discussed.

M2 should triage external review findings into accepted fixes, no-paid proposal
evidence, deferred long-term work, and rejected scope expansion. M3 should fill
only evidence gaps that materially affect the proposal argument, such as the
retrospective baseline table, adapter/repo fragility summary, fallback-share
analysis, source-supply status, and evidence that predictive validity is a real
unsolved target. M4 should harden the validation protocol by separating
true-future validation from pseudo-future traction and by defining joint
success gates. M5 should turn the skeleton into proposal report v1. M6 should
translate the report into the presentation or memo format needed for project
approval.

This skeleton intentionally does not draft M2-M6 runbooks.

[NEEDS PRIORITIZATION: choose whether M2 review triage or M3 evidence
consolidation comes first after M1 closeout.]

## 9. Risks And Boundaries

The first risk is overclaiming. The proposal must not say that Phase 1 proves
predictive validity, that the current selector predicts future work better than
simple baselines in the formal sense, or that paid validation is authorized.

The second risk is underclaiming. If the proposal says only that Barcarolle
produced audited artifacts, it misses the research value of Phase 1. Phase 1
showed that construction choices matter, that naive weighting can fail in a
diagnosable way, that adapter-stratified reporting changes interpretation, and
that retrospective signal can guide route finding without becoming proof.

The third risk is candidate ambiguity. `coverage_constrained_unweighted_v1`
should not be presented as uniform across repos while `boltons` uses fallback.
The claim should be about a composite selector with explicit fallback behavior
unless the fallback issue is repaired.

The fourth risk is adapter-general overreach. The current retrospective signal
is not adapter-general. Pooled improvement must remain secondary unless a
future runbook preregisters a pooled estimand and adapter-level gates.

The fifth risk is task-supply drift. Task Supply v2 is necessary infrastructure
because weak candidate supply can block validation, but it should remain Layer
1 support. External generator adapters should be treated as candidate sources
that require Barcarolle-owned certification, source labels, caps, and local
validation.

[NEEDS BOUNDARY CHECKLIST: allowed, draft, and prohibited claims for reviewer
use.]

## 10. Milestones

Draft milestone sequence:

M1: Proposal report skeleton, argument map, evidence/TODO matrix, and claim
boundary. Status: this document.

M2: External review triage. Classify GPT-5.5-Pro recommendations as accepted
now, no-paid proposal evidence, deferred, or rejected as short-term expansion.

M3: Proposal evidence consolidation. Fill the evidence gaps that materially
affect proposal readiness: baseline table, adapter/repo fragility, fallback
share, source-supply status, and predictive-validity motivation.

M4: Validation protocol V2 hardening. Freeze the true-future versus
pseudo-future boundary, candidate fallback wording, joint success gate,
support thresholds, and baseline envelope before any paid-validation question.

M5: Proposal report V1. Convert this skeleton and consolidated evidence into a
readable proposal-facing report and technical appendix.

M6: Proposal presentation or memo. Convert the report into the approval format
needed by target reviewers.

The proposal should not skip from M1 to paid validation. The current safe next
action is no-paid review triage or proposal evidence consolidation.

[NEEDS DECISION: M2-first versus M3-first handoff after M1.]

## Draft Conclusion

Barcarolle's Phase 1 result is not a validated predictive benchmark compiler.
It is also not merely an artifact-hygiene exercise. The phase produced a
cleanly interpretable negative result for naive weighting, a conservative
mainline correction, repaired source-quality evidence for the three-repo story,
adapter-stratified reporting discipline, a frozen outcome-blind candidate
policy, and weak retrospective route-finding signal. Those results justify a
proposal focused on the predictive-validity north star, provided the proposal
keeps current evidence in its proper lane and routes missing evidence to the
next no-paid milestones.
