# Independent Audit Of The Regime Route

Date: 2026-07-30.

Status: complete; independently reproduced and adversarially audited. This
audit is based on repository evidence only. It makes no paid call, opens no
sealed Agent outcome, changes no Selector, and develops no Generator.

## Decision

**Revise.** The arithmetic is reproducible, and the practical decision not to
nominate a Selector from the current Multi-SWE panel is sound. The evidence
does not support the broader causal wording that the combined H5/H10 panel is
one sparse-outcome failure region.

H5 is a measured trivial-dominated frame under the frozen
equal-repository estimand. At H10, full history has a lower
source-time-counterfactual point estimate under that estimand, but the
advantage is sensitive to aggregation, repository influence, and Origin
anchoring. The audit recommends calling H10 an aggregation-sensitive sparse
stress frame, not a separately established failure region. This is a
recommendation under unresolved suitability thresholds, not a frozen regime
classification. Candidate reversal across H5/H10 remains a
candidate-robustness failure; it is not proof that H10 itself is uninformative.

## Research Contract

The target is a reproducible `accept`, `revise`, or `reject` decision for the
Multi-SWE failure-region interpretation and the proposed no-paid atlas. Success
requires reproducing the central arithmetic; separating sparsity from panel,
time, aggregation, denominator, missing-result, and preprocessing
explanations; comparing the required controls under their real contracts; and
answering all six handoff questions with audited next actions.

A recomputed aggregate, favorable special case, taxonomy without a decision,
or algorithm recommendation without an independent mechanism, information
contract, and falsification test does not count. Runtime remains one
repository, Task Pool, and Selection; repositories are offline evidence units.
No paid calls, sealed Agent outcomes, rescue tuning, canonical-contract or
schema edits, or concrete Generator work are allowed. Refutation and bounded
inconclusive findings remain valid terminal states.

## Initial Model Before Backlog Review

This model was frozen before reading the backlog's proposed stages. The
`failure region` appeared to combine two claims: H5 was zero-dominated, while
H10's full-history point estimate was lower under equal-repository aggregation.
Sparsity was a measured condition, not a cause; Agent mix, repository mix,
projected time, aggregation, and support could produce the same pattern.
Hindsight could show capacity, not pre-Origin identifiability.

The initial best experiment was therefore an outcome-frozen reproduction and
decomposition by Agent, repository, aggregation, horizon, and time/order.
Zero and climatology would diagnose the estimator, full history and random
would match the no-Selection and budgeted actions more closely, and an atlas
would proceed only if it selected a development panel or sized an acquisition.

## Reproduction And Robustness

All published Multi-SWE quantities reproduce from the committed Task, time,
panel, and sparse-positive artifacts:

| Quantity | H5 | H10 |
| --- | ---: | ---: |
| Repositories / Origins | `13 / 221` | `11 / 107` |
| Agent-Origin blocks | `7,956` | `3,852` |
| Pooled all-zero blocks | `6,652` (`83.61%`) | `2,771` (`71.94%`) |
| Always-zero equal-repository MAE | `0.059870` | `0.060395` |
| Full-history equal-repository MAE | `0.067348` | `0.052807` |
| Exact budget-ten hindsight MAE | `0.034709` | `0.027191` |
| Hindsight reduction from full history | `48.46%` | `48.51%` |

The 1,632 Tasks, 39 repositories, 36 configurations, 58,752 scheduled
Agent-Task cells, 2,913 positives, and `4.9581%` global density also reproduce.
All 328 hindsight solves are certified optimal and the H5/H10 membership
digests match the committed summary.

The decisive robustness results are:

- The table mixes pooled Agent-Origin shares with equal-repository MAE. Under
  pooled-Origin weighting, zero beats full history at both H5
  (`0.039844` versus `0.057512`) and H10 (`0.039979` versus `0.044757`).
- At H10, full history beats zero for 22 of 36 configurations but only five of
  eleven repositories. The equal-repository zero-minus-full difference is
  `+0.007589`; omitting two-Origin `fasterxml/jackson-databind` reverses the
  aggregate sign. The point estimate is therefore repository-sensitive.
- H5 remains zero-dominated on the eleven repositories common to H10:
  `0.059645` versus `0.067051`. The H5 result is therefore not caused by the
  two extra repositories.
- Splitting the exact H10 future cohorts into two sequential five-Task targets,
  with the first five Tasks added to history before predicting the second,
  changes zero-minus-full from `+0.007589` to `-0.006229`. This is compatible
  with horizon averaging and expanding-history effects; the H10 sign is not by
  itself evidence that Task content is predictable.
- The frozen builder end-aligns blocks using the final repository size. A
  start-aligned, still outcome-free schedule gives H5 zero/full
  `0.054684 / 0.067472`, but H10 `0.056810 / 0.055998`; the H10 advantage
  shrinks from `0.007589` to `0.000812`.
- All-one future-block share is zero at both horizons. Always-one MAE is about
  `0.940130` at H5 and `0.939605` at H10. The feasible budget-ten rate grid has
  zero scalar lower-bound error at both horizons, so discrete rate support
  alone does not explain the observed loss.

A post-result source-time-counterfactual diagnostic used the expanding median
of each repository-configuration's earlier future-block rates, with zero as
the first Origin fallback. It obtains `0.059599` at H5 and `0.055580` at H10.
This strengthens the H5 trivial-dominance result and leaves full history best
at H10. It is not an authoritative baseline because its pooling, cold-start,
and availability rules were not frozen before the outcomes were inspected,
and the panel does not prove actual historical Result availability.

The historical values are correct but incomparable as one trend:

- Boltons `0.136111` scoreable and `0.137500` scheduled MAE use one frozen
  20-history-to-H10 split and four configurations, not repository-macro rolling
  Origins.
- The approximately `0.20` result is an 18-slice mixed retrospective aggregate
  (`0.209011` candidate, `0.214900` temporal baseline), not Boltons full
  history.
- SymPy `0.193290` is one repository, two configurations, twelve H5 Origins,
  initial history 15, and macro-Origin aggregation.

They establish that horizon size alone does not determine absolute MAE. They do
not estimate a common regime effect.

## Causal And Contract Audit

Sparsity is descriptive, not a demonstrated root cause.

- The scheduled denominator is complete, but 16,381 cells (`27.88%`) are
  `empty_error_patch` and are deliberately scored as failures; there are no
  `incomplete` cells. Empty-patch share ranges from `7.54%` to `61.03%` across
  configurations. This makes Agent/harness behavior a plausible contributor,
  not missing-cell arithmetic.
- Full history beats zero for only 7 of 36 configurations at H5 and 22 of 36
  at H10. Post-outcome higher-pass-rate subpanels can even reverse H5. Those
  cuts are inadmissible as suitability gates, but they establish sensitivity
  to Agent-panel aggregation. They do not identify a causal mechanism.
- The committed evidence retains positive cells and per-configuration terminal
  totals, but not cell-level terminal state. Repository/time sensitivity to
  empty patches cannot be reproduced from the committed artifacts.
- Global density is `4.9581%`; pooled future density is `3.9844%` at H5 and
  `3.9979%` at H10; equal-repository future density is the reported zero loss,
  `5.9870%` and `6.0395%`. These denominators must not share an unlabeled
  `density` field.
- Pull-request `createdAt` is projected Task ordering, not Result availability
  or certification time. Cutoff-to-future-end spans range from `1.69` to
  `1,161.90` days at H5 and `5.65` to `909.25` days at H10. Task-count H5/H10
  cannot stand in for one runtime `TimeRange`.
- The result contract asserts experiments revision `6a7d5566…`, but
  `normalize_public_panel` hashes supplied files without verifying the checkout
  HEAD. The digest binds the observed bytes, not their claimed Git revision.
  This is a provenance defect, not a loss-reproduction failure.

Zero and a fully specified availability-safe climatology are appropriate
estimator controls. The present expanding climatology is only a
source-time-counterfactual approximation. Neither control selects an executable
budgeted benchmark, so neither replaces full eligible history as the primary
no-Selection baseline or equal-budget random as the action-matched calibration.
Hindsight measures capacity only. A candidate validity claim should beat full
history and the strongest frozen trivial estimator, while reporting the
different action and cost contracts.

The committed random calibration uses 20,000 NumPy PCG64 random-key uniform
budget-ten subsets. Its base seed is `20260728`; the outcome calibration adds
`100 + horizon`, giving effective seeds `20260833` at H5 and `20260838` at
H10. Mean MAE is `0.069163` and `0.057869`, respectively `+0.001815` and
`+0.005062` versus full history. It calibrates the Selection action; it does
not repair zero's different action contract.

When target-Agent history is visible, an executable control that chooses the
ten historical Tasks with the fewest successes realizes an all-zero selected
vector in 220 of 221 H5 Origins and all 107 H10 Origins, scoring `0.059901` and
`0.060395`. The cached-target finite-horizon method also beats zero and full
history at both horizons. Neither control is valid for the shared unseen-target
contract. A failure label must therefore name the Selection unit and
information contract, not only the Task Pool, Agent panel, horizon, and
aggregation.

## Answers To The Handoff Questions

1. **H10:** its equal-repository full-history advantage is real arithmetic but
   not robust enough to make H10 a separately established failure or success
   region. The combined label should be revised.
2. **Cause:** sparsity has not been isolated from Agent/harness mix, horizon
   averaging, repository weighting, scheduled denominators, projected time,
   Origin anchoring, or preprocessing.
3. **Controls:** zero and an availability-safe climatology are necessary
   estimator diagnostics, but only a source-time counterfactual is currently
   available. Full history and equal-budget random are closer to the user's
   no-Selection and budgeted-Selection decisions; executable controls must be
   matched to the candidate's information contract.
4. **Atlas:** a narrow, predeclared atlas is the recommended next step because
   current controls are incomplete and it can change the panel-versus-
   acquisition decision at zero new-outcome cost. This is not a proved
   information-gain maximizer while acceptance thresholds remain unfrozen. An
   open-ended atlas would delay prediction and permit post-outcome regime
   selection.
5. **Over-closure:** no algorithm family was clearly closed globally from one
   panel. The overreach is the combined H5/H10 and generic-Selection failure
   label. Separately, SWE-bench Full was selected as a secondary development
   source and then omitted from FR-003 without a recorded normalization gate.
6. **Practical main region:** freeze workload relevance before outcomes, then
   apply a separate candidate-independent identifiability screen. A panel must
   clear both axes; favorable candidate loss cannot define either one.

## Suitability Atlas

The strongest evidence for the atlas is that applying even its unfinished
diagnostics changed the interpretation: aggregation, denominator, H5/H10
anchoring, trivial controls, and oracle headroom are not interchangeable. It
uses no new Agent outcomes and can prevent another candidate from being judged
inside a mechanically easy frame.

The strongest evidence against the current FR-003 wording is that it can
produce a taxonomy without improving prediction. No workload-derived
suitability threshold or complete climatology contract is frozen, and the
named Boltons, SymPy, Verified, and Multi-SWE views differ in Agent panel,
denominator, provenance, horizon, and aggregation. Outcome-based choice among
them cannot by itself define the practical main region.

FR-003 should be revised as a bounded compatibility and identifiability audit.
Before computing another panel, it must freeze candidate-independent thresholds
for `failure`, `stress`, and `usable`; until then those names remain audit
recommendations rather than acceptance decisions.

1. Freeze repository/Agent pooling, block construction, cold-start,
   availability, weighting, always-one, random, and oracle meanings before
   computing another panel.
2. Keep workload relevance and statistical identifiability as two axes.
   Workload identity comes from the intended use before outcomes; outcome
   density and headroom can reject an uninformative panel but cannot make it
   representative.
3. Distinguish the Verified three-Agent and opened eleven-Agent views.
4. Add SWE-bench Full as `normalization-gated`, not silently omit it. It has
   2,294 Tasks, 408 H5 Origins and 201 H10 Origins across ten repositories, 22
   complete public vectors, and eleven checked vectors. Its public outcomes are
   open but no exact result allowlist or normalized panel digest is committed.
5. Exit by choosing a statistically usable *exploratory* panel, or by
   specifying the smallest workload-matched acquisition. Do not infer a
   reusable universal main region from the opened atlas.

## Ranked Next Routes

| Rank and route | Decision-relevant information gain | Data cost | Main failure mode |
| --- | --- | --- | --- |
| 1. Revised FR-003 plus SWE-bench Full compatibility preflight | Freezes the missing thresholds, then either retains an exploratory panel or supplies variance and failure composition needed to size acquisition. It is ranked first because it can eliminate or retain whole source options before new outcomes are authorized. | Zero new outcomes; local normalization and audit work. | Post-outcome panel selection that stops at labels or chooses a favorable opened view. |
| 2. Workload-anchored outcome acquisition if no panel clears | Directly supplies native Task time, historical Result availability, and prospective evidence for the intended workload. Its evidence value may exceed the atlas, but its size and price are presently unidentified. | Authority-gated new outcomes; determine only after freezing workload, Agents, `TimeRange`, target effect, and precision. | Choosing easier Agents or Tasks after seeing pass rates, or acquiring too little independent information. |

Fixed-universe IRT may still be useful for score compression, but it answers a
different estimand and is not a ranked route for temporal Selection.
ALG-016U on Full is also not ranked: Full outcomes were inspected before that
mechanism was proposed, and Full lacks a frozen Result-availability policy.
Such a run would be an outcome-open portability screen, not the independent
algorithm test contemplated by the handoff.

## Next Actions

1. Correct the combined failure-region wording in the failure report, current
   ledger, `PROCESS.md`, and statistical protocol. Record H5 as
   trivial-dominated and H10 as aggregation- and anchoring-sensitive; label
   pooled versus equal-repository quantities and the scheduled denominator.
2. Freeze the revised atlas contract, add Full's normalization preflight, then
   run the atlas once. Do not treat a Full result as independent confirmation.

## Required Document Corrections And Future Blockers

The document correction should declare end-aligned Origins and realized
calendar spans, define climatology completely, add always-one and random
controls, distinguish Verified panels, and label every density and weighting
contract. It should not call H10 generic temporal signal or extend the finding
to other Selection units and information contracts.

Two implementation gaps are future blockers rather than audit corrections. The
Multi-SWE importer must verify the asserted result-checkout revision before
that revision can be treated as proven provenance. A sanitized cell-level
terminal-state sensitivity artifact is needed before attributing sparse
responses to Task difficulty rather than Agent or harness failure.

## Final Approach Registry

| Family | Thesis and decisive test | Current evidence | Exact gap; status; reopen condition |
| --- | --- | --- | --- |
| Numerical reproduction | Interpretation depends on correct pairing and aggregation; rebuild primary quantities. | Counts, losses, memberships, and hindsight certificates reproduce; weighting and anchoring alter interpretation. | Cell states and checkout revision are not independently bound. **Completed.** Reopen if a provenance or terminal-state artifact changes the panel. |
| Causal decomposition | Sparsity may be descriptive; test panel, horizon, repository, and anchoring alternatives. | All four alternatives materially change the comparison. | Opened outcomes cannot identify one cause. **Completed: revise.** Reopen for a predeclared separating control or panel. |
| Route comparison | An atlas is useful only if it changes the panel/data decision; compare its output and cost with alternatives. | A bounded atlas can gate an exploratory panel or size acquisition; Full is normalization-gated. | No availability-safe normalized Full contract. **Completed.** Reopen after the atlas contract and Full preflight freeze. |
| Adversarial audit | Synthesis may hide contract gaps; falsify it requirement by requirement. | Non-independent ALG-016U was removed; corrections and blockers were separated; final numerical re-audit passed. | No outcome-equivalent audit gap. **Passed.** Reopen if the claim, evidence boundary, or route changes. |

## Adversarial Exit Audit

- The verdict maps to reproduced arithmetic and named aggregation, repository,
  panel, anchoring, denominator, time, and provenance counterexamples.
- All six handoff questions are answered under the shared unseen-target
  Selection contract; cached-target counterexamples are not presented as
  evidence for that contract.
- Zero, climatology, full history, random Selection, and hindsight are assigned
  their actual estimator, action, information, and capacity roles.
- Both ranked routes state information gain, data cost, and main failure mode.
  No algorithm route is recommended without an independent mechanism and
  complete information contract.
- The memo makes no paid call, reads no sealed outcome, develops no Generator,
  and changes no algorithm, canonical contract, or core schema.
- The remaining limitations—cell-level terminal-state sensitivity, source
  revision proof, Full normalization, and Result availability—are reported as
  gaps, not treated as routine verification.
