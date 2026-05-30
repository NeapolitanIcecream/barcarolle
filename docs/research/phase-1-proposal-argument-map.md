# Phase 1 Proposal Argument Map

Status: Draft M1 artifact, 2026-05-30.

This map is proposal scaffolding, not a final report and not a paid-validation
authorization. It keeps predictive validity as the long-term north star while
limiting the short-term proposal claim to Phase 1 traction evidence and a
credible validation path.

## Reader Frame

Target readers are project/proposal reviewers, coding-agent evaluation
researchers, and agent developers who need target-repository evaluation and
tuning feedback. They will not accept a predictive-validity claim from
retrospective or underpowered evidence alone. They may accept that Phase 1
exposes a real benchmark-construction problem if the evidence is reproducible,
negative evidence is treated honestly, and the next validation path is specific
enough to audit.

The proposal must therefore answer five reader questions:

1. Why is repo-specific predictive validity a meaningful research target?
2. Why is Barcarolle not just another SWE task generator?
3. What did Phase 1 support, and what did it not support?
4. Why is the next phase justified before predictive validity has been proved?
5. Which missing evidence matters for proposal readiness?

## Research Problem

Public/general SWE benchmarks and scalable task generators do not directly
answer how to predict future work in one target repository.

The unresolved condition is target-repository shift: a team evaluating an ACUT
cares about future work in its own codebase, but a general benchmark score,
generic task factory, or uncalibrated same-repo task pool is not automatically a
future-work estimator. If this remains unresolved, readers risk choosing,
tuning, or trusting coding agents from evidence that is auditable in general
but not predictive for the repository where the agent will actually operate.

## North-Star Question

Can a Barcarolle-compiled repo-specific benchmark predict future target-repo
ACUT performance?

The estimand is future target-repo ACUT success rate. The benchmark score is a
candidate predictor of that future success rate. This is the long-term research
target, not a Phase 1 result.

## Claim Layers

### Main Long-Term Claim

Draft long-term claim:

```text
Barcarolle should be evaluated as a target-repository benchmark compiler whose
central success criterion is predictive validity: whether a small, audited,
repo-specific benchmark release predicts later ACUT performance on real work in
the same repository better than naive or generic alternatives.
```

Qualifier: Phase 1 does not establish this claim. It defines the research
object and identifies measurable routes toward testing it.

### Short-Term Proposal Claim

Draft proposal claim:

```text
Phase 1 does not prove predictive validity, but it establishes that the problem
is real, measurable, and technically tractable. Benchmark construction choices
materially affect repo-specific estimates; naive weighted target-profile
matching failed in a diagnosable way; adapter-stratified reporting, source
quality repair, and outcome-blind policy freezing improved research governance;
and a no-paid retrospective pseudo-future analysis found weak, underpowered
directional signal that can guide the next validation phase.
```

This claim is stronger than "Barcarolle produced clean artifacts" because it
says Phase 1 generated evidence about the benchmark-construction problem. It is
weaker than "Barcarolle is validated" because it explicitly treats predictive
validity as unproved.

### Allowed Phase 1 Claims

- Barcarolle is a target-repository benchmark compiler, not an ACUT harness,
  general task factory, agent-license product, or public leaderboard. Evidence:
  `AGENTS.md`, `docs/architecture/system-design.md`.
- The old weighted target-profile pilot completed cleanly but failed its
  threshold; no predictive-validity claim follows from it. Evidence:
  `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`.
- Local bakeoff evidence supports keeping simple stratified designs as the
  conservative mainline while treating weighted variants as research
  candidates. Evidence:
  `experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md`.
- The three-repo paid pilot was endpoint- and policy-clean enough for
  exploratory pilot evidence, but predictive validity was not established.
  Evidence:
  `experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md`.
- Adapter differences are valid ACUT-configuration evidence when endpoint,
  model, workspace, verifier, and policy checks are clean enough; they are not
  model-only superiority claims. Evidence:
  `experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md`.
- Click source-quality repair removed the visible title-only/minor-risk caveat
  for the source-quality part of the three-repo story without rerunning paid
  outcomes. Evidence:
  `experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md`.
- Retrospective pseudo-future analysis found directional, underpowered signal
  for `coverage_constrained_unweighted` over simple baselines. Evidence:
  `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md`.
- `coverage_constrained_unweighted_v1` is a deterministic, outcome-blind
  candidate policy ready for adversarial review, not a validated compiler.
  Evidence:
  `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_decision.md`,
  `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_outcome_blindness_audit.md`.
- Task Supply v2 work supports Layer 1 candidate supply; it is not the project
  core. Evidence:
  `experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md`.

### Prohibited Claims

- Barcarolle is already a validated predictive benchmark compiler.
- Phase 1 proves predictive validity.
- `coverage_constrained_unweighted_v1` predicts future target-repo work better
  than simple baselines in the formal sense.
- The current evidence authorizes a paid validation run.
- Pooled improvement can rescue adapter-level failure.
- Codex/Kilo differences prove model-only superiority.
- The completed blocked split supplement is primary predictive-validity
  evidence.
- Task Supply v2 or an external generator is the central Barcarolle research
  contribution.

## Argument Thickening Map

### Main Claim

Phase 1 justifies a next research phase because it shows, without claiming
predictive validity, that repo-specific benchmark compilation is a real and
auditable research problem with diagnosable failures, measurable baselines, and
a concrete validation path.

Confidence: cautious-to-medium for proposal traction; low for any formal
predictive-validity claim.

Scope: Phase 1 evidence over the current `attrs`, `boltons`, and `click`
artifact set, current ACUT adapters, and current retrospective analyses.

Non-scope: formal future-work validation, broad multi-ACUT generality, public
leaderboard claims, or paid-run authorization.

### Reason 1: The Research Object Is Distinct From Task Generation

Reader question answered: Why is this not just another SWE task generator?

Evidence:

- System design frames the core output as a benchmark release estimating future
  work in a specific repository, with task source adapters as Layer 1 supply:
  `docs/architecture/system-design.md`.
- The 2026-05-19 research plan separates target-repo predictive validity from
  upstream task factory yield:
  `/Users/chenmohan/Downloads/barcarolle-research-0519.md`.
- Task Supply v2 decision reports generator work as source-yield and
  certification infrastructure, not release validation:
  `experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md`.

Warrant: If the central question is which tasks, splits, weights, baselines,
and uncertainty rules estimate future target-repo performance, then task
generation is necessary supply infrastructure but not the research claim.

Possible objection: Stronger task generators might solve the problem by simply
providing more tasks.

Response: More tasks help, but without target-repo calibration, source caps,
split design, adapter reporting, and validation against future work, a larger
pool remains only candidate supply. The proposal should use generator work as
Layer 1 support and reserve the core claim for compilation and validation.

### Reason 2: Phase 1 Shows Benchmark Construction Choices Matter

Reader question answered: What evidence shows the problem is real rather than
speculative?

Evidence:

- Weighted pilot completed `44/44/44` planned/completed/scoreable cells, but
  weighted gaps were `0.3148` for `attrs` and `0.7481` for `boltons`, while
  simple same-budget baselines had much smaller gaps:
  `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`.
- Local bakeoff confirmed the old metadata objective was underidentified and
  recommended keeping `repo_stratified` as the conservative mainline:
  `experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md`.
- The 2026-05-26 design critique argues the failure mode was sparse,
  high-dimensional metadata matching and uncalibrated marginal weights rather
  than an execution-layer paid-run failure:
  `/Users/chenmohan/Downloads/barcarolle-research-0526.md`.

Warrant: A benchmark compiler is worth studying if different construction
rules produce materially different prediction errors and if a failing rule
fails for diagnosable reasons that can inform the next design.

Possible objection: A failed weighted design is merely a negative result, not
traction.

Response: It is traction because the run was clean enough to interpret, the
failure mode exposed underidentified design choices, and the failure redirected
the mainline toward lower-variance stratified and coverage-constrained
candidates.

### Reason 3: Phase 1 Improved Research Governance

Reader question answered: Why should reviewers trust the next phase?

Evidence:

- Three-repo paid pilot recorded `120` planned, completed, and scoreable cells,
  `0` policy violations, endpoint compliance pass, and no predictive-validity
  claim:
  `experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md`.
- Adapter-stratified reporting treats Codex and Kilo as ACUT configurations,
  not model-only evidence:
  `experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md`.
- Click source-context repair upgraded all `30` frozen click tasks with `0`
  paid LLM calls and `0` paid ACUT cells:
  `experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md`.
- Candidate policy validation protocol froze a deterministic, outcome-blind
  policy and explicitly disallowed predictive-validity claims:
  `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_decision.md`.

Warrant: A proposal can justify further work before final validation when it
shows that the project can preserve audit boundaries, record negative evidence,
and freeze future decision rules before spending more paid budget.

Possible objection: Artifact hygiene is engineering quality, not research
evidence.

Response: Artifact hygiene alone would be insufficient. Here it matters because
it makes the negative and directional evidence interpretable at the benchmark
boundary and prevents the next phase from being driven by post-hoc outcome
inspection.

### Reason 4: Retrospective Signal Gives Route-Finding Evidence, Not Proof

Reader question answered: Why is the next phase worth funding despite not
proving the north star?

Evidence:

- Best simple baseline was `temporal_recent_baseline` with MAE `0.2149`;
  best Barcarolle candidate was `coverage_constrained_unweighted` with MAE
  `0.209`, a weak directional edge:
  `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md`.
- Uncertainty labels classify the result as `directional_only`,
  `too_sparse_for_formal_predictive_validity`, and `traction_evidence_only`:
  `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md`.
- Adapter metrics show the candidate worse than `temporal_recent_baseline` on
  Codex but better on Kilo:
  `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md`.
- The 2026-05-30 adversarial review says the packet is credible enough for
  adversarial review and no-paid protocol hardening, but not paid validation:
  `/Users/chenmohan/Downloads/barcarolle-research-0530.md`.

Warrant: Underpowered retrospective signal can justify no-paid proposal and
protocol work when it is labeled as route-finding evidence and not confused
with predictive validity.

Possible objection: The edge over the best baseline is too small to matter.

Response: Correct for validation. The skeleton should not use the edge as a
success claim. It should use it to prioritize evidence gaps: stronger baselines,
adapter-specific support, fallback accounting, and true-future or strictly
preregistered rolling-origin validation.

### Reason 5: The Candidate Path Is Concrete But Must Be Narrowed

Reader question answered: What algorithmic and validation work remains?

Evidence:

- Candidate policy spec freezes `coverage_constrained_unweighted_v1`, budget
  `6` per repo, seed `2026053001`, and forbidden outcome inputs:
  `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_policy_spec.md`.
- Selection manifest records `18` selected tasks and `9` coverage gaps, with
  `boltons` falling back because of insufficient feature support:
  `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md`.
- Validation protocol prefers `true_future_holdout`, uses
  `preregistered_rolling_origin_or_pseudo_future_replay` as fallback, and says
  no paid run is authorized:
  `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_validation_protocol.md`.
- GPT-5.5-Pro review identifies boltons fallback, success criteria, baseline
  strength, and adapter-general claims as must-fix items:
  `/Users/chenmohan/Downloads/barcarolle-research-0530.md`.

Warrant: A candidate policy becomes useful for proposal planning when its
selection rule, fallback behavior, and validation blockers are visible enough
to be challenged before paid validation.

Possible objection: A simple coverage-constrained unweighted selector is not
the Barcarolle compiler.

Response: The proposal should call it a candidate selector with labeled
fallbacks, not the full compiler. Its value is as a frozen, inspectable object
for no-paid hardening and future validation design.

## Strongest Alternative Explanation

The strongest alternative explanation is that Phase 1 primarily demonstrates
clean benchmark artifact engineering, not a substantive path toward predictive
validity. This concern is serious because the retrospective signal is weak, the
current candidate is simple, `boltons` uses fallback behavior, and paid
validation is not authorized.

Best concession: Phase 1 has not shown that Barcarolle can predict future
target-repo work. It has shown that the route to such a claim must pass through
stronger baselines, support thresholds, fallback accounting, and true-future or
strict rolling-origin validation.

How the claim should change: keep the short-term proposal claim at "traction
evidence and credible path" and reserve "predictive-validity established" for a
future outcome-unseen validation result.

Weakest current links:

- evidence: retrospective MAE edge is small and adapter/repo fragile;
- method: pseudo-future replay cannot establish predictive validity;
- candidate definition: `boltons` fallback makes the current policy composite;
- supply: Task Supply v2 is not yet paid-ready.

## GPT-5.5-Pro Recommendation Classification

The 2026-05-30 GPT-5.5-Pro review is strategy input, not controlling scope.
The proposal skeleton uses the review to classify future work without turning
M1 into a paid-validation or scope-expansion runbook.

### Accept Now

- Do not authorize paid validation now.
- Keep predictive validity as the north star but state that it is not proved.
- Split pseudo-future traction from predictive-validity evidence.
- Recast the current candidate as
  `coverage_constrained_unweighted_v1_with_labeled_fallbacks` unless `boltons`
  feature support is repaired.
- Treat adapter-stratified support as primary; pooled improvement cannot rescue
  adapter failure.
- Explain `boltons` fallback explicitly.
- Replace the loose future `margin OR majority` idea with a stricter joint-gate
  issue to be handled in later validation-protocol hardening.

### Consider For No-Paid Proposal Evidence

- Many-seed random baseline and percentile reporting.
- Baseline envelope against the best preregistered simple baseline.
- Stricter temporal baseline with same budget, same eligibility, and frozen
  tie-breaks.
- Quantitative support thresholds for repos, windows, adapter cells, and
  fallback share.
- Power/budget note explaining what a future paid run can detect.

### Defer

- Full Task Supply v2 expansion.
- External generator adapter implementation.
- Hierarchical beta-binomial or complex uncertainty modeling.
- Full multi-ACUT residual predictive-validity study.
- Broad repo replacement or public benchmark packaging.

### Reject As Short-Term Scope Expansion

- Turning Barcarolle into a task generator project.
- Treating external task systems as trusted default supply.
- Requiring every long-term methodological improvement before the proposal
  skeleton can be written.
- Treating GPT-5.5-Pro recommendations as mandatory M1 scope.

## Proposal-Readiness Test

The proposal skeleton is ready for the next milestone only if every major
claim falls into one of three bins:

- supported now by committed Phase 1 evidence;
- explicitly draft with a named `[NEEDS ...]` placeholder or milestone route;
- prohibited and excluded from proposal claims.

No claim in the skeleton should imply that predictive validity is established,
that paid validation is authorized, or that task-supply work is the core
research contribution.
