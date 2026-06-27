# 1. Executive recommendation

Barcarolle should first learn a **calibrated, constrained coreset**, not an unconstrained per-task “value” score.

The recommended first learned selector has two components:

1. A small convex mixture over strong rule-based selectors—recency, module/task-type stratification, coverage, certification quality, and historical disagreement when legitimately available.
2. A regularized weighting layer that adjusts the selected tasks toward the predicted distribution of the next repository-work window, subject to diversity, cost, provenance, maximum-weight, and effective-sample-size constraints.

It should output **one common task set and one common weight vector for every Agent in the comparison**. Pair-specific task sets would destroy score comparability.

Use two explicitly separate tracks:

* **Metadata-only selector:** the primary, most portable track. It sees task and repository metadata but no candidate-Agent outcomes when choosing tasks.
* **Outcome-aware selector:** a challenger that may use historical Agent results only when those exact cells were available before the origin, or under a clearly labeled counterfactual-prepaid protocol.

Optimize absolute future pass-rate prediction first. Add pairwise pass-rate-gap error and recommendation regret as auxiliary objectives. Do not begin with rank-only learning: a selector can rank Agents correctly while remaining badly miscalibrated.

The adaptive controller should be conservative. Until learned performance has a clear out-of-origin advantage, it should shrink the learned weights toward a strong stratified/temporal rule selector or fall back entirely.

This ordering matches the evidence in the repository. Barcarolle already has the correct asset separation and requires exact cache identity. But the retained retrospective has only five windows across three repositories, with a (0.005889) MAE advantage over the best simple baseline and no catastrophic-miss improvement. A previous promising selector was also correctly downgraded after it was discovered that its variant and final story had been chosen using the same holdout.

The immediate research sequence should therefore be:

**cache and leakage correctness → strong baseline envelope → learned mixture and calibrated weighting → supply-ceiling diagnostics → pairwise/hierarchical models → adaptive controller → fresh validation.**

---

# 2. Formal selector formulation

## Estimand

For repository (r) and origin (o=(r,t)), define:

* (H_o): tasks known and eligible before (t);
* (F_o): future real-work tasks after (t);
* (A_o): complete Agent configurations frozen at (t);
* (Y_{ai}\in{0,1,\varnothing}): outcome of Agent (a) on task (i).

Use:

* (Y_{ai}=1) for verified pass;
* (Y_{ai}=0) for verified fail and Agent-attributable invalids such as timeout, no meaningful patch, or exhausted budget;
* (Y_{ai}=\varnothing) only for benchmark-infrastructure or verifier failures.

A persistent task-level infrastructure failure should remove that task from every Agent’s denominator, rather than creating Agent-specific denominators. Missing cached cells are not outcomes; they must be filled or the benchmark must abstain.

The selector is:

[
\pi_\theta(H_o,Z_o,Y^{\mathrm{available}}_o,A_o,B)
\rightarrow (S_o,w_o,u_o)
]

where:

* (Z_o) contains frozen, leakage-safe features;
* (B) is a count, cost, or latency budget;
* (S_o\subseteq H_o) is the selected common task set;
* (w_{io}\ge 0), (\sum_{i\in S_o} w_{io}=1);
* (u_o) is the selector’s uncertainty and support assessment.

The selected-benchmark estimate for Agent (a) is:

[
\widehat p_{ao}=\sum_{i\in S_o}w_{io}Y_{ai}.
]

The initial future target is the equally weighted future pass rate:

[
p^F_{ao}=\frac{1}{|F_o|}\sum_{j\in F_o}Y_{aj}.
]

Later, (F_o) may carry production-importance weights, but equal weighting is the cleanest initial estimand.

For an Agent pair ((a,b)):

[
\widehat d_{ab,o}=\widehat p_{ao}-\widehat p_{bo},\qquad
d^F_{ab,o}=p^F_{ao}-p^F_{bo}.
]

## Eligibility times

Every task needs several timestamps:

* `source_resolved_at`: when the issue, PR, release, or requirement became historical fact;
* `task_material_available_at`: when all solver-visible material existed;
* `check_material_available_at`: when the oracle material existed;
* `certified_at`: when Barcarolle certified the task;
* `result_available_at`: when an Agent result became available.

Strict history eligibility is:

[
\operatorname{known_at}_i=
\max(
\text{task material available},
\text{check material available},
\text{certified at}
)
\le t.
]

A retrospective reconstruction that assumes today’s generator existed in the past must be labeled `counterfactual_replay`, not strict rolling origin.

## Inputs, outputs, and training labels

| Element            | Contents                                                                                                                                                           |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Selector inputs    | Pre-origin task features, repository state, certification/provenance, exact candidate-Agent identities, budget, permitted historical outcomes, expected task costs |
| Selector output    | Common task IDs, nonnegative weights, expected uncertainty, support warnings, expected cache misses, selector/feature version and reason summary                   |
| Primary label      | Future pass-rate vector ((p^F_{ao})_{a\in A_o})                                                                                                                    |
| Auxiliary labels   | Future Agent-pair gaps, future top tier, recommendation regret, future task-stratum proportions                                                                    |
| Operational labels | Infrastructure-invalid rate, Agent-invalid rate, runtime and cost                                                                                                  |
| Not a valid label  | “This task was selected by the previous best selector”                                                                                                             |

Do not create thousands of apparently independent task labels and pretend that the sample size is the number of tasks. The independent statistical unit is primarily the **repository–origin episode**. Task-level pseudo-labels may be used internally, but rows from the same origin must share a group weight and remain together in validation.

## Budget and weight constraints

Start with count-matched evaluation. Add cost only after cost observations are comparable across harnesses.

Recommended constraints are:

[
|S_o|\le k,\qquad
\sum_{i\in S_o} c_i \le B,
]

[
0\le w_{io}\le w_{\max},\qquad
\operatorname{ESS}(w_o)=\frac{1}{\sum_i w_{io}^2}\ge \eta k.
]

Reasonable initial policy values are:

* (w_{\max}=2/k);
* (\eta=0.6);
* no generator family supplies more than 40% of the benchmark;
* at least half the initial benchmark comes from real historical or user-provided work.

These are starting guardrails, not universal statistical constants.

## Loss functions

The primary evaluation loss is origin- and repository-macro-averaged MAE:

[
L_{\mathrm{MAE}}
================

\frac{1}{|R|}
\sum_r
\frac{1}{|O_r|}
\sum_{o\in O_r}
\frac{1}{|A_o|}
\sum_{a\in A_o}
|\widehat p_{ao}-p^F_{ao}|.
]

Train with a smooth Huber approximation if convenient, but always report exact MAE.

Useful auxiliary losses are:

[
L_{\mathrm{gap}}
================

\operatorname{mean}*{o,a<b}
\left|
\widehat d*{ab,o}-d^F_{ab,o}
\right|,
]

[
L_{\mathrm{regret}}
===================

\operatorname{mean}*o
\left[
\max_a p^F*{ao}
---------------

p^F_{\arg\max_a \widehat p_{ao},o}
\right].
]

A practical initial training objective is:

[
L_{\mathrm{train}}
==================

L_{\mathrm{Huber\ pass}}
+
\lambda_{\mathrm{pair}}L_{\mathrm{Huber\ gap}}
+
\lambda_{\mathrm{reg}}R(\theta),
]

with (\lambda_{\mathrm{pair}}\in{0,0.1,0.25}) selected only in inner rolling-origin validation. Invalid rate, cost, latency, diversity, weight concentration, and catastrophic misses should initially be **constraints or promotion gates**, not freely traded terms in one opaque scalar loss.

Because small future holdouts produce noisy observed pass rates, also report task-level binomial log loss or Brier score as a secondary calibration diagnostic. Raw future MAE remains the north star.

## Which learned objective first?

Use this order:

1. **Absolute pass-rate calibration.**
2. **Agent-pair pass-rate-gap prediction.**
3. **Recommendation regret and top-tier agreement.**
4. **Direct rank-only objectives only as diagnostics.**

A rank-only selector is unsuitable as the first claim because it can correctly select the winner while predicting, for example, 90% versus 80% when future performance is 40% versus 30%.

Predictive-validity Agents must remain frozen and distinct from Agents modified using the benchmark. Otherwise the experiment measures benchmark plus tuning process plus tuned artifact, not selector validity alone.

---

# 3. Feature and leakage policy

Every feature column should carry:

```text
feature_name
feature_version
observed_at
source_artifact_digest
origin_snapshot_digest
leakage_class
```

Suggested leakage classes are:

```text
intrinsic_pre_origin
certification_aggregate
historical_outcome
agent_specific_historical_outcome
execution_constraint_only
forbidden
```

The current repository already distinguishes metadata-only, historical-outcome, development-only, and forbidden outcome fields. That policy should become a core v2 invariant rather than an experiment-specific manifest.

## Recommended feature groups

| Group                     | Useful leakage-safe features                                                                                                                           | Restrictions                                                                                           |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| Repository and time       | Task age at origin, recent module activity, release cadence, historical path churn, language, dependency area, contributor/ownership entropy           | Compute from the base commit or an origin-frozen repository snapshot                                   |
| Task statement            | Length, issue/feature/refactor class, presence of reproduction steps, stack trace, acceptance criteria, ambiguity flags, lexical TF-IDF                | Fit vocabulary on training origins only; avoid external LLM embeddings in v1                           |
| Scope and changed files   | File-count bucket, top-level component, language mix, code/test/docs ratio, patch-size bucket, dependency fan-out                                      | Tag as reference-derived; exclude raw diff, literals, symbols, and exact leaf paths in v1              |
| Check and tests           | Check type, fail-to-pass/pass-to-pass counts, runtime, repeat stability, test-framework class, oracle breadth score, base-fails/reference-passes flags | Never expose test text, assertion text, expected values, hidden filenames, or failure messages         |
| Generator provenance      | Generator family/version, real/synthetic/user source, issue/PR/release origin, LLM involvement, statement source, oracle-construction method           | Use hierarchical shrinkage and source caps; do not assume one source is intrinsically better           |
| Certification             | Clarity score, ambiguity score, reproducibility, reviewer count/disagreement, flakiness, certification gate versions, rejection reason class           | Preserve rejected-candidate records to measure certification coverage and selection bias               |
| Historical Agent outcomes | Pre-origin task difficulty, outcome entropy, pairwise disagreement, failure-mode rates, invalid rates, replicate variance                              | Strict as-of joins; candidate-Agent-specific features require a separately labeled outcome-aware track |
| Cost and latency          | Verifier runtime, actual billed cost, latency quantiles, timeout risk                                                                                  | Use only when units and coverage are comparable; otherwise treat as constraints                        |
| Agent descriptors         | Exact Agent digest, prior pass rate, frozen budget, latent ability estimates, tool-category indicators                                                 | Avoid learning semantic meaning from model/provider names; new Agents need anchor cells                |

The Agent Selection Demo found that a recommendation tie-break depended on cost fields that were observed for one harness but conservatively imputed for another. It also found that the selected set was much older and differently sourced than the future holdout. Cost coverage and provenance therefore need to be explicit features and guardrails, not silently trusted numbers.

## Features to ban

The selector must not see:

* future task outcomes, future Agent results, future failure labels, or future costs;
* post-origin PR discussion, later issue edits, future release notes, or later repository state;
* raw reference patches or embeddings of them;
* hidden test source, hidden test names, expected outputs, assertion text, or verifier logs;
* candidate patch contents, final diff features, Agent transcripts, rationales, or tool traces;
* `verified_pass`, `terminal_status`, or scoreability from the same task selection being evaluated;
* global normalization statistics computed using validation or future origins;
* task IDs, split names, source IDs, or stable cluster IDs as predictive categorical features;
* outcome-derived “difficulty” computed using the held-out Agent or future window;
* mutable online embeddings or LLM-derived labels without a frozen model/version and origin-safe input;
* features from current repository HEAD when replaying an earlier origin.

Exact task IDs and cluster IDs remain useful for joins and grouping, but should not enter a model matrix.

## Text and embedding policy

For v1, use lexical features and simple statement-shape indicators. A current embedding model used on an old origin may itself contain post-origin repository knowledge.

A later embedding experiment should require:

* a frozen local encoder and digest;
* no hidden-oracle inputs;
* a training-origin-only dimensionality reduction;
* an ablation excluding embeddings;
* explicit labeling as retrospective if the encoder did not exist at the replayed origin.

## Outcome-aware selector policy

Historical outcomes are allowed only when all of these are true:

1. The exact result cache identity matches.
2. The result is associated with a task in (H_o).
3. It is available before selection in strict mode, or the experiment is labeled counterfactual-prepaid.
4. No outcome from (F_o) contributed to the feature.
5. The same outcome feature construction is possible in the intended operational mode.

Do not compare metadata-only and outcome-aware selectors as though they have identical data-acquisition costs.

---

# 4. Algorithm candidates

The following data gates are practical starting points. Final sample requirements should come from block-bootstrap power simulations over repository–origin episodes.

| Order | Candidate                                        | Data and training                                                                                                   | Selection mechanism                                                                                                                     | Main failure mode                                                        |
| ----: | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
|     1 | Learned mixture of rule selectors                | Prior out-of-origin losses for random, recency, coverage, stratified, provenance-capped, and disagreement selectors | Learn simplex weights with ridge shrinkage; blend expert task scores and solve one constrained selection                                | All experts share the same task-supply bias                              |
|     2 | Calibrated exponential task weighting            | Coarse task features and cached outcomes from prior origins                                                         | (w_i\propto r_i\exp(\beta^\top z_i)), followed by capped, diversity-constrained coreset selection                                       | Concentrated weights, unstable coefficients, absent future strata        |
|     3 | Future-stratum prediction and matching           | Task metadata alone; labels are next-window module/type/provenance proportions                                      | Forecast next-window stratum mass, then select tasks minimizing feature-moment discrepancy                                              | Future work contains genuinely novel strata                              |
|     4 | Regularized task-utility GLM                     | At least several origins, three or more Agents, and complete task columns                                           | Predict task representativeness or contribution to future pass/gap error; select with coverage constraints                              | Pseudo-replication and task-level overfitting                            |
|     5 | Pairwise gap/ranking model                       | Preferably four or more Agents and enough close Agent pairs                                                         | Predict which tasks reliably expose future Agent differences; select one common set maximizing pair information and coverage            | Correct ranking but poor absolute calibration; overfit to current Agents |
|     6 | Hierarchical IRT or latent-factor model          | Preferably five or more Agents, 100+ tasks, structured overlap, and multiple origins                                | Model Agent ability, task difficulty, Agent-task interactions and time drift; choose tasks minimizing posterior future-rate uncertainty | Latent structure changes with new Agents or repository evolution         |
|     7 | Delayed online expert controller                 | Ten or more sequential origin outcomes                                                                              | Exponential weighting or conservative Thompson sampling over registered selectors                                                       | Delayed sparse feedback and rapid drift                                  |
|     8 | Deep set/graph subset selector — **speculative** | Many repositories and dozens to hundreds of independent origins                                                     | End-to-end set encoding and differentiable or stochastic subset selection                                                               | Enormous overfitting risk with current episode count                     |

## Recommended first learned design

Implement candidates 1–3 together, but keep each ablatable.

For each origin:

1. Base rule selectors produce task scores or candidate sets.
2. A simplex-constrained model combines them:
   [
   r_i=\sum_m \alpha_m r_{im},\qquad \alpha_m\ge0,\quad\sum_m\alpha_m=1.
   ]
3. A low-dimensional exponential tilt adjusts for predicted future strata:
   [
   \widetilde w_i\propto r_i\exp(\beta^\top z_i).
   ]
4. A deterministic greedy or integer selection chooses (k) tasks while enforcing:

   * component and task-type coverage;
   * provenance caps;
   * real-history minimum share;
   * maximum task weight and ESS;
   * expected runtime and invalid-risk limits.
5. The output records uncertainty across origin-block bootstrap fits.

Keep (\alpha) and (\beta) small. A reasonable first model has fewer than ten learned coefficients. Shrink toward the strongest rule baseline.

## Task-utility model

If the first design shows signal, fit an elastic-net GLM to a task utility such as:

[
u_{io}
======

-\frac{1}{|A_o|}
\sum_a |Y_{ai}-p^F_{ao}|.
]

This is a training-only pseudo-label. It must never be treated as an independent observation across tasks. Every origin should contribute equal total weight, and all tasks from an origin stay in the same split.

Avoid tree ensembles until there are enough independent origins for stable grouped validation. A dataset with hundreds of task rows but only five origins is still a five-episode dataset for generalization purposes.

## Pairwise model

A pairwise model is useful when the operational question is choosing between close Agents. Train it to predict the **future gap**, not merely a binary winner.

One common task set should jointly minimize error over all Agent pairs. Do not produce a special task set for every pair except as an offline diagnostic.

Promotion requires:

* absolute MAE does not materially regress;
* pairwise-gap MAE improves;
* recommendation regret improves;
* performance remains stable when one Agent is removed from the candidate set.

## Hierarchical model

A useful later model is:

[
\operatorname{logit}P(Y_{ai}=1)
===============================

\alpha_a-\beta_i+u_a^\top v_i
+\gamma^\top z_i+\delta^\top \text{time}_{io}.
]

It can estimate task difficulty, Agent-specific strengths, and uncertainty in sparse caches. Start with scalar difficulty, then add low-rank interactions only if posterior predictive checks show systematic Agent-task specialization.

For new Agents, run a small set of common anchor tasks before trusting the latent estimate.

## Uncertainty-aware selection

For candidates 2–6:

1. Bootstrap whole repository–origin blocks.
2. Refit the selector in each bootstrap draw.
3. Score candidate sets across draws.
4. Select the set minimizing:
   [
   \mathbb E[L]+\kappa\operatorname{SD}(L)
   ]
   or a prespecified upper quantile of predicted loss.
5. Abstain or fall back if selected sets are unstable or predicted future mass lies outside historical support.

The selector should expose uncertainty and support failure, not merely output a task list.

---

# 5. Adaptive/drift strategy

The controller should operate over a small registry of frozen selectors. It is itself evaluated by rolling origin.

## Trust calculation

For selector (j), compute using only completed prior origins:

[
R_j(o)
======

\operatorname{EWMA}(\text{outer-origin MAE}_j)
+
\kappa,\operatorname{SE}_j
+
\lambda D_j(o),
]

where (D_j(o)) is a pre-outcome drift/support penalty.

No single origin should contribute more than 25% of the effective weight. Use a frozen half-life, such as four origins, rather than manually changing recency after seeing results.

Use three trust states:

| State                | Starting gate                                                                                                                      | Action                                                                  |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Rule fallback        | Fewer than 8 prior origins, severe drift, missing required features, or learned upper confidence bound is not better than baseline | Use preregistered stratified/temporal fallback                          |
| Conservative mixture | Learned mean MAE is better but uncertainty overlaps the baseline                                                                   | Blend learned and rule task scores, with learned share capped at 25–50% |
| Learned champion     | Upper one-sided confidence bound on paired MAE difference is below (-0.02), with guardrails passing                                | Use learned selector, retaining shadow rule evaluation                  |

The (0.02) margin is a proposed practical threshold and must be preregistered.

## Pre-outcome drift checks

Before selecting, measure:

* categorical Jensen–Shannon divergence for module, task type, generator, and certification buckets;
* standardized Wasserstein distance for numeric scope and time features;
* share of current task mass in unseen strata;
* a regularized classifier’s cross-validated AUC for distinguishing recent tasks from selector-training tasks;
* new Agent distance from previously evaluated Agents, using anchor-task outcomes when available;
* generator or certification version changes.

Starting warnings could be:

* more than 10% predicted future mass in unsupported strata;
* drift-classifier AUC above 0.75;
* new generator version supplying over 25% of the eligible pool;
* an Agent with no anchor outcomes and no close historical analogue.

## Post-outcome staleness checks

After future outcomes become historical, monitor:

* three-origin EWMA MAE relative to fallback;
* mean signed prediction error;
* 90% interval coverage and width;
* catastrophic miss rate;
* recommendation regret;
* invalid-rate and cost shifts.

A reasonable stale trigger is any two of:

* learned MAE exceeds fallback by at least 0.02 over the recent window;
* absolute signed bias exceeds 0.05;
* nominal 90% interval coverage drops below 80%;
* catastrophic miss rate exceeds fallback by more than five percentage points.

A stale selector is not retuned against the just-seen origin and re-declared valid. It becomes a new selector generation whose claim must be tested on a later origin.

## Controlled adaptation and Goodhart protection

The controller may update automatically after outcomes become historical only when:

* its update rule, decay, thresholds, and candidate selector registry were frozen beforehand;
* its decision for origin (o) uses metrics only through (o-1);
* human changes produce a new version;
* the just-consumed future window becomes development data and cannot remain the final audit holdout;
* benchmark-exposed or tuned Agents are separately labeled.

This turns adaptation into a prequential algorithm rather than an uncontrolled sequence of human reactions.

---

# 6. Rolling-origin validation protocol

## Exact protocol

1. **Freeze the campaign.** Record repository set, Agent digests, selector registry, feature schema, generator/check versions, budgets, invalid policy, metrics, random seeds, hyperparameter grids, and win criteria.

2. **Define task clusters.** Tasks from the same issue, PR chain, release requirement, duplicated statement, or substantially identical check/reference change belong to one cluster. A cluster may not cross history and future.

3. **Define an embargo.** Use a 14-day default between the last history task and first future task. Increase it for release-level or highly related task sequences.

4. **Define history.**
   [
   H_o=
   {i:\operatorname{known_at}_i\le t-\text{embargo}}.
   ]
   Keep certification rejects in a separate table to measure coverage.

5. **Define future.** The primary future window should be the next 15 certified real-history or user-work tasks, capped at 180 days. Require at least 10 usable future tasks for the origin. A fixed 90-day window is a secondary robustness analysis.

6. **Avoid overlapping primary holdouts.** Future task clusters should appear in only one primary outer origin. More densely spaced overlapping origins may be used for diagnostics but not counted as independent evidence.

7. **Freeze Agents.** Every Agent includes model snapshot or provider revision, harness commit/image, prompts and repository instructions, tools, retrieval, skills, runtime policy, budget, retries, and stochastic settings. A mutable model alias without a stable revision weakens the claim.

8. **Nested training.** At outer origin (o_j), train only on origins (o_1,\ldots,o_{j-1}). Select hyperparameters using an inner rolling-origin loop over those earlier origins. Fit preprocessing only on inner-training origins.

9. **Generate selection before outcome access.** The selection command writes a signed or hashed manifest containing task IDs, weights, features, selector version, and cache misses. A separate evaluation command then loads future results. The selection process should not have filesystem or API access to the future-outcome table.

10. **Run or join outcomes.** For cached evaluation, join exact cache identities. For paid evaluation, run missing selected cells only after selection is frozen. Future tasks are evaluated with the same frozen Agents.

11. **Apply the invalid policy.** Agent-attributable invalids count as zero. Persistent task/check infrastructure failures exclude the task for all Agents and increase the reported benchmark-invalid rate. Do not silently use different task denominators for different Agents.

12. **Compute paired metrics.** All selector comparisons use the same origins, Agents, future tasks, and invalid policy.

## Preregistered metrics

Primary:

* macro MAE over repository, origin, then Agent.

Supporting:

* pairwise-gap MAE;
* top-rank agreement, counting a predicted winner as correct if it lies in the future top tier;
* top-tier exact agreement and Jaccard agreement, with top tier initially defined as within five percentage points of the future best;
* recommendation regret;
* mean signed error;
* catastrophic miss rate, initially (|\widehat p-p^F|\ge0.20);
* interval coverage and width;
* scoreable and invalid rate;
* task diversity and provenance concentration;
* expected and realized cost and latency;
* robustness by repository, origin, Agent subset, and (k\in{5,10,20}).

Report both macro and micro results, but use macro MAE for promotion. Confidence intervals should block-bootstrap repository–origin episodes, not individual tasks.

## Baselines

Every origin and budget should include:

* uniform random, summarized over at least 1,000 cached seeds;
* quality-filtered random;
* temporal-recent;
* module/task-type stratified;
* provenance-capped stratified;
* coverage-maximizing;
* recency-plus-coverage;
* historical-disagreement selection when legitimate data exists.

The baseline champion must be selected using earlier origins. Also report the post-hoc best-simple envelope descriptively.

## Convincing win

A convincing selector result should require all of the following:

* an untouched outer evaluation or genuinely future campaign;
* at least 12 non-overlapping repository–origin episodes across at least three repositories;
* at least three frozen Agents, unless the claim is explicitly pair-specific;
* paired MAE improvement of at least 0.02 absolute or 10% relative over the strongest preregistered deterministic baseline;
* one-sided 95% block-bootstrap upper confidence bound below zero;
* better performance than at least 95% of same-budget random seeds;
* wins on at least 60% of origins and at least two of three repositories;
* no repository-level MAE regression greater than 0.05;
* catastrophic-miss degradation no greater than five percentage points;
* infrastructure-invalid degradation no greater than two percentage points;
* cost and latency remain within the frozen budget;
* similar conclusions at two task budgets.

When fewer episodes are available, call the result **directional evidence**, not a convincing win. The existing (0.005889) retrospective margin, unchanged catastrophic-miss rate, and limited windows are useful traction but do not meet this bar.

Before buying new cells, use the cached paired residuals to simulate statistical power as a function of future-task count and number of origins.

---

# 7. Low-budget experimental plan

## Phase A: zero-paid work

First perform an immutable snapshot and normalization of all existing sanitized results.

The initial experiments should be:

1. Reproduce the existing random, temporal, coverage, and stratified results from normalized rows.
2. Add strict as-of masks and label every origin as strict, metadata-only, or counterfactual-prepaid.
3. Build the rule-selector mixture.
4. Build the future-stratum predictor and calibrated weighting model.
5. Run nested rolling-origin evaluation with no new selector family added after the outer outcomes are examined.
6. Run negative controls:

   * shuffled task times;
   * shuffled future labels within repository;
   * a deliberate forbidden future feature that the leakage linter must reject;
   * task-ID features, which should be rejected;
   * random Agent labels.
7. Compute supply-ceiling diagnostics before adding model complexity.

Do not use the same five windows for unrestricted architecture search. Keep a selector-generation ledger: every materially new model family records which origins were already inspected.

## Choosing an execution mode

| Mode                   | Use when                                                                                                   | Research value                                  | Main warning                                                 |
| ---------------------- | ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------ |
| Prepaid/cached pool    | Candidate-Agent matrix is dense enough for common task columns and many selector variants must be compared | Best mode for selector development and ablation | Easy to oversearch one fixed cache                           |
| Select-then-run        | Selector is already frozen and the goal is an operational benchmark or final pilot                         | Measures realistic cost and cache misses        | Cannot fairly compare many unselected alternatives afterward |
| Incremental cache fill | Missing cells dominate uncertainty or block complete common rectangles                                     | Buys only high-value cells                      | Scattered cells create unusable selection-biased matrices    |

Starting decision rules:

* Use prepaid evaluation when at least 80% of cells are present on the candidate/baseline union and there are at least 30 complete common task columns.
* Use incremental fill when missingness exceeds 20% on that union or one Agent has materially fewer scoreable columns.
* Use select-then-run only after the selector, comparator, task budget, and success rule are frozen.

## Cache identity required for reuse

A pass/fail outcome is reusable only if these fields match:

```text
repository identity
base commit and submodule/LFS state
task manifest digest
solver-visible statement/context digest
check manifest and hidden-check bundle digest
scoring-policy version
verifier image and dependency/environment digests
Agent manifest digest
model snapshot/provider revision
harness commit or container digest
prompt and repository-instruction digest
tool/retrieval/skill configuration digests
network policy
runtime, token and monetary budgets
retry and attempt policy
stochastic seed/temperature settings
solver/verifier adapter versions
hardware class when timeouts or latency are relevant
```

Store `pricing_version` separately. A price-table change does not invalidate pass/fail, but it invalidates direct reuse of an old cost estimate.

Also record:

```text
run_started_at
run_finished_at
result_available_at
diff digest
terminal status
failure attribution
actual usage coverage
benchmark-exposure metadata
```

A model alias that may silently change should not be treated as one frozen Agent across dates.

## Incremental cell acquisition

Purchase complete columns or small rectangles, not isolated convenient cells.

Priority order:

1. Missing cells on tasks selected by both the learned candidate and strongest baseline.
2. Missing cells on future-holdout tasks.
3. Tasks in underrepresented feature strata.
4. Tasks with high posterior outcome entropy or high expected discrimination among close Agents.
5. A small repeated-run sentinel set.

A simple acquisition score is:

[
\frac{\text{expected reduction in selector-comparison uncertainty}}
{\text{expected cell cost}}.
]

Recompute after each small batch rather than committing to a large matrix upfront.

Do not use `is_cached` as a predictive task feature. Cache availability is an execution constraint and can otherwise make the selector optimize for historical purchasing decisions.

## Smallest fresh directional experiment

Assuming historical selections for both learned and baseline selectors are already cached:

* one repository;
* two exact frozen Agents;
* at least 30 certified pre-origin tasks;
* benchmark budget (k=8);
* ten genuinely future real tasks;
* two sentinel tasks rerun for both Agents.

This requires:

* 20 new future cells;
* 4 repeat cells;
* **24 new cells total**.

If selected history cells are missing, add:

[
2\times|\text{missing union of learned and baseline selections}|.
]

Stop at 40 total cells. If the missing union would exceed that cap, do not run a compromised comparison; first perform incremental cache fill or reduce the planned union before the protocol is frozen.

With two Agents and ten future tasks, macro-MAE changes occur in approximately 0.05 increments. A meaningful directional signal is therefore:

* learned macro MAE at least 0.05 lower than the baseline;
* correct top-tier recommendation with zero or lower regret;
* no catastrophic-miss or invalid-rate regression;
* at most one disagreement among the four repeated sentinel cells.

One origin cannot support a convincing general claim. It only decides whether a broader campaign is worth funding.

The prior demo used only one run per Agent-task cell and therefore could not separate stochasticity from a true harness/repository interaction; the sentinel allocation directly addresses that weakness.

## Stop, pay, or expand supply

Compute three diagnostic bounds:

1. **Simple baseline error.**
2. **Learned selector error.**
3. **Hindsight pool oracle error**, where an explicitly cheating selector uses future outcomes to choose the best subset or weights.

The hindsight oracle is never promotable. It estimates whether the existing task pool contains enough support.

Starting decision rules:

| Observation                                                           | Interpretation                                       | Action                                  |
| --------------------------------------------------------------------- | ---------------------------------------------------- | --------------------------------------- |
| Baseline MAE minus oracle MAE is less than 0.02                       | Little selection headroom exists in the current pool | Expand task supply                      |
| Oracle has large headroom, learned model is poor, cache is dense      | Algorithm or feature problem                         | Improve selector, not paid cells        |
| Oracle has headroom, learned estimates are unstable, matrix is sparse | Outcome-data problem                                 | Incremental cache fill                  |
| Learned and baseline share the same signed bias by module/type        | Missing future-work strata                           | Expand generator coverage               |
| Repeated Agent cells disagree frequently                              | Agent or runtime instability                         | Stabilize Agent identity or buy repeats |
| Cost fields have poor coverage or incomparable units                  | Accounting problem                                   | Remove cost from selection objective    |
| New generator increases count but not oracle headroom                 | Generator adds redundant tasks                       | Stop that replication                   |

Additional supply diagnostics should include:

* a classifier distinguishing history from future task metadata;
* nearest-neighbor and convex-hull support distances;
* residual MAE by module, task type, scope, and provenance;
* certification acceptance rates by future-work category;
* feature coverage before and after adding each generator.

## Task-supply interaction and replication priority

The selector should treat generator family and certification quality as both features and possible confounders. Certification may preferentially retain clear, easy, testable tasks, changing the target from “future work” to “future work that Barcarolle can certify.” Preserve rejected source events and report:

[
\text{certification coverage}
=============================

\frac{\text{future source events producing certified tasks}}
{\text{all eligible future source events}}.
]

The first replication should combine:

1. **SWE-bench-style issue/PR mining and fail-to-pass/pass-to-pass checks.**
2. **Verified-style clarity, oracle-validity, and solvability review.**
3. **Live-style origin freezing and continuous refresh.**

SWE-bench established the issue/PR task pattern, and the Verified review retained 500 human-validated tasks after finding substantial statement and test-quality problems. SWE-bench Live adds automated, continuously refreshable curation. ([arXiv][1])

Quality certification cannot end with a source badge. Subsequent studies have found inadequate tests and plausible-but-behaviorally-wrong patches in SWE-bench-style evaluations, supporting task-local, versioned oracle audits and optional test augmentation. ([arXiv][2])

The next supply experiments should be:

* **SWE-Bench++-style scalable real-PR harvesting** when repository/language coverage is inadequate. Adapt sourcing, environment synthesis, oracle extraction, and QA; do not import hint-guided training trajectories into selector research.
* **SWE-smith-style generated breakages** only when the real-history oracle shows insufficient task count or support. Treat these as synthetic and initially cap their selected weight.
* **SWE-Bench Pro or SWE-EVO-style long-horizon tasks** only if future-work audits show that single-issue repair systematically misses multi-file or release-level work.
* **SWE-Future-style synthesis — speculative.** It is especially relevant to forecast-conditioned supply, but it was released on June 17, 2026 and should first be reproduced as a separate generator arm with strict forecast/validation/generation time separation. ([arXiv][3])
* **User-provided tasks and custom checks** whenever their provenance and certification contracts are auditable.

Synthetic or LLM-generated tasks should:

* be visibly tagged;
* use only origin-available repository material;
* pass the same or stronger certification;
* receive hierarchical shrinkage toward zero contribution;
* have an initial benchmark-weight cap, such as 25%;
* be judged only against real future work, never a synthetic future holdout from the same generator.

For every new generator, compare the old pool with `old + new` under the same selector, budget, Agents, and real future holdout. A generator has helped only if it improves MAE, regret, coverage, or oracle headroom without unacceptable invalid-rate or robustness loss.

I found an accessible SWE-bench Atlas evaluation package, but its README is an evaluation guide rather than a sufficient task-construction specification. Replication should wait until the exact method paper or construction document is pinned.

---

# 8. Implementation roadmap for Codex

Keep the implementation small, use direct schemas and `uv`, and treat old experiment code as evidence or one-time import material rather than v2 architecture. That is consistent with the repository’s current engineering rules.

A minimal initial layout is:

```text
barcarolle/
  records.py
  store.py
  cache_key.py
  origins.py
  features.py
  feature_policy.yaml
  metrics.py
  selectors/
    random.py
    recency.py
    stratified.py
    coverage.py
    mixture.py
    calibrated.py
  drift.py
  acquisition.py
  cli.py

tools/
  import_legacy_results.py

tests/
  ...
```

Do not create a broad plugin framework. A selector initially needs only:

```python
def select(context: SelectionContext) -> Selection:
    ...
```

## Staged roadmap

| Stage                                  | Inputs                                                     | Code artifacts                                                                              | Experiment and success criterion                                                                                                                     | Stop condition                                                                  |
| -------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 0. Records and cache identity          | Architecture docs; sanitized task/result tables            | `records.py`, `cache_key.py`, `store.py`, legacy importer, schema tests                     | Import retained rows; every reusable result gets an exact key; mutations to any semantic field change the key; incomplete identities are quarantined | Do not guess missing Agent/check/environment identity                           |
| 1. Rolling-origin engine and baselines | Normalized tasks/results                                   | `origins.py`, baseline selectors, `metrics.py`, selection/evaluation CLI split              | Reproduce retained retrospective metrics from normalized rows; deterministic seeds; future file inaccessible to selection command                    | Any unexplained metric mismatch or future-data access                           |
| 2. Feature builder and leakage linter  | Frozen origin snapshots and provenance                     | `features.py`, `feature_policy.yaml`, feature snapshot manifests                            | Every feature has `observed_at`, digest and leakage class; injected future/outcome columns fail tests; preprocessing is fit within training origins  | Any feature without reconstructable provenance                                  |
| 3. First learned selector              | Baseline outputs and pre-origin features                   | `mixture.py`, `calibrated.py`, constrained coreset optimizer                                | Nested rolling-origin comparison of expert mixture, weighting and stratum matching; coefficients and selected sets stable under block bootstrap      | No directional advantage and hindsight oracle shows less than 0.02 headroom     |
| 4. Supply and cache diagnostics        | Stage-3 residuals and incomplete matrices                  | Supply-support report, hindsight oracle, `acquisition.py`                                   | Produce an explicit algorithm-vs-supply-vs-outcome bottleneck decision; dry-run paid-cell acquisition plan                                           | Do not buy cells without predicted uncertainty reduction                        |
| 5. Outcome-aware and pairwise models   | At least 3–4 Agents, adequate complete columns and origins | Regularized task-utility and pairwise modules                                               | Pairwise-gap and regret improve without material absolute-MAE regression; leave-one-Agent-out stability                                              | Insufficient independent origins, Agent ties, or unstable coefficients          |
| 6. Hierarchical model                  | Preferably 5+ Agents, 100+ tasks and structured overlap    | IRT/latent-factor module, posterior diagnostics                                             | Better held-out calibration and uncertainty coverage than regularized GLM                                                                            | Poor posterior predictive fit or Agent factors unstable across origins          |
| 7. Controller and drift                | Registry of frozen selector versions                       | `drift.py`, adaptive selector, shadow reports                                               | Simulated distribution and Agent drift trigger fallback; controller at origin (o) reads metrics only through (o-1)                                   | Any manual or current-holdout-dependent switching                               |
| 8. Generator adapters                  | Supply-ceiling report                                      | Issue/PR adapter, certification rubric, origin snapshots; later scalable/synthetic adapters | `old` versus `old + generator` paired real-future ablation improves prediction or oracle support                                                     | More task count without prediction or support improvement                       |
| 9. Fresh pilot                         | Frozen protocol, Agents and selections                     | Preregistration manifest, paid-cell plan, sanitized final report                            | Run the 24-cell directional design or power-sized campaign; report negative results and all guardrails                                               | Identity drift, budget overrun, insufficient future tasks, or protocol mutation |

## Essential tests

The first implementation should include tests that:

* reject future outcomes in an as-of join;
* reject hidden-check or reference-diff fields from the selector matrix;
* prevent one task cluster crossing history and future;
* prove selection is deterministic from a manifest and seed;
* verify weight caps and ESS;
* treat Agent-attributable invalid as fail;
* remove persistent task-level infrastructure failures for all Agents;
* reject mismatched cache identities;
* show that selection succeeds without importing workspace or raw transcript code;
* force the adaptive controller to fall back under simulated drift;
* verify that the selection manifest exists before future outcomes are opened.

Existing retrospective numbers can become regression fixtures, but old experiment class names and abstractions should not become public v2 APIs.

---

# 9. Key risks and safeguards

| Risk or red flag                                      | How it fools the research                                                   | Safeguard                                                                                               |
| ----------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Repeated tuning on the same cached origins            | Thousands of virtual experiments overfit a tiny number of episodes          | Selector-generation ledger, nested rolling origin, untouched audit origins, limited holdout access      |
| Holdout reuse                                         | A selector looks validated because it was chosen after seeing its holdout   | Manifest and code hash frozen before outcome join; consumed holdouts become development data            |
| Future leakage through timestamps or repository state | Old tasks receive information that existed only later                       | `observed_at` on every feature; base/origin snapshot computation; strict as-of joins                    |
| Oracle leakage                                        | Hidden tests or reference patches reveal the intended solution distribution | Only coarse certification aggregates; ban raw oracle text, diff embeddings, symbols and expected values |
| Task-row pseudo-replication                           | Hundreds of task rows create falsely narrow confidence intervals            | Group training and bootstrap by repository–origin; report episode count prominently                     |
| Repository overfitting                                | Module names or source IDs memorize three repositories                      | Hierarchical/coarse path features, leave-one-repository-out evaluation, no task/source IDs              |
| Task-supply bias                                      | Every selector shares the same missing future-work categories               | Hindsight oracle, history/future support classifier, rejection coverage, generator ablations            |
| Certification selection bias                          | Only clear/easy/checkable work reaches both benchmark and holdout           | Preserve all attempted source events; report certification coverage and rejection strata                |
| Synthetic-generator artifacts                         | Selector learns generated wording or check patterns rather than future work | Source tags, initial weight caps, leave-generator-out tests, validation only on real future work        |
| Unstable Agents                                       | One run or mutable model alias makes rankings look task-driven              | Exact Agent digest, provider revision, sentinel repeats, run-date analysis, freeze runtime policy       |
| Missing-cell bias                                     | Only convenient or promising Agent-task cells are compared                  | Complete common rectangles; no treating missing cells as failures or dropping them silently             |
| Invalid-rate gaming                                   | A selector avoids difficult checks or excludes failures selectively         | Shared task denominator, Agent-invalid-as-fail, task-level infrastructure exclusion, invalid guardrails |
| Cost trap                                             | Cheap tasks or incomparable accounting dominate selection                   | Count-matched primary analysis; actual usage coverage; pricing-versioned cost; cost as constraint       |
| Pairwise Goodhart                                     | Selector picks artificial “gotcha” tasks that separate two Agents           | Absolute-MAE non-inferiority, common task set, diversity and future-stratum constraints                 |
| Adaptive-controller Goodhart                          | Human switches models after every future result                             | Frozen automatic update rule; controller evaluated in its own outer rolling-origin loop                 |
| Agent tuning contamination                            | Future Agent improvement is attributed to selector validity                 | Exposure ledger; predictive validity and tuning utility evaluated as separate claims                    |
| Overlapping future windows                            | The same future tasks are counted as many independent wins                  | Non-overlapping primary holdouts; clustered uncertainty for diagnostic overlaps                         |
| Hindsight oracle promotion                            | A useful ceiling diagnostic is mistaken for a deployable method             | Separate namespace/report section, unmistakable `future_leaking_diagnostic` label                       |
| Environment/check drift                               | An old cached pass is reused under a changed verifier                       | Check, image, dependency, scoring-policy and adapter digests in cache identity                          |
| Paid-cost escalation                                  | Sparse exploratory cells accumulate without supporting a comparison         | Batch-level value-of-information gate and hard stop after each incremental fill                         |

---

# 10. What not to do yet

* Do not build a deep neural, graph, reinforcement-learning, or LLM-judged selector on the current number of independent origins.
* Do not optimize top-rank agreement alone.
* Do not let each Agent receive a different selected benchmark.
* Do not use raw reference diffs, hidden-test embeddings, Agent transcripts, or generated patch features.
* Do not treat the current five windows or the (0.005889) retrospective margin as independent proof.
* Do not run a large paid matrix before the cache-identity, invalid-policy, baseline, and power-analysis work is complete.
* Do not replicate every generator family. Start with issue/PR history, stronger certification, and live origin freezing.
* Do not use synthetic or forecast-generated tasks as their own validation holdout.
* Do not import old experiment abstractions into v2; port only normalized data, narrow utilities, and regression fixtures.
* Do not build a database, public leaderboard, generalized plugin system, or tuning subsystem before the selector’s basic predictive signal survives fresh rolling-origin validation.

[1]: https://arxiv.org/abs/2310.06770 "https://arxiv.org/abs/2310.06770"
[2]: https://arxiv.org/abs/2506.09289 "https://arxiv.org/abs/2506.09289"
[3]: https://arxiv.org/abs/2512.17419 "https://arxiv.org/abs/2512.17419"
