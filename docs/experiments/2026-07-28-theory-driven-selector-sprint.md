# Theory-Driven Selector Sprint

Date: 2026-07-28.

Status: completed zero-paid-call development sprint. The current Task Pool
algorithm search is closed. Six outcome-independent Agent results remain
sealed.

Follow-up: the frozen
[budget–horizon sensitivity audit](2026-07-28-budget-horizon-sensitivity.md)
tested budgets 5/10/15 and task-count horizons 3/5/10 on one common cohort. No
cell passed, so scale tuning did not reopen this mechanism.

## Outcome

No Selector supports the project claim yet.

The strongest new result is a cutoff-aware, Agent-invariant difficulty Markov
Selector. Its wide candidate-minus-full-history MAE is `-0.00888`, better than
97.78% of 20,000 equal-budget random Selections. This is evidence that the Task
Pool contains some temporally useful response structure. It is not enough:
only 3/7 repositories improve, the 95% repository-cluster interval is
`[-0.03215, +0.01432]`, and the deep-portfolio effect is harmful at `+0.00920`.

An adaptive prequential choice between Markov and stationary difficulty does
not repair the failure. Its wide effect is `-0.00235`, its temporal-null rate
is `0.194`, and all three deep repositories are still harmed. The frozen stop
rule therefore ends further candidate invention on these opened outcomes.

## Inputs And Boundary

- Task source: 500 Tasks from
  [SWE-bench Verified](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified/tree/main),
  pinned at revision `91aa3ed51b709be6457e12d00300a6a596d4c6a3`.
- Agent-result source: the official
  [SWE-bench experiments repository](https://github.com/SWE-bench/experiments),
  pinned at commit `2f15350cd32becc4569e0d826361048555b605c0`.
- Geometry: seven wide repositories, three deep repositories, and 68
  repository-local rolling Origins.
- Runtime boundary: every Selection contains only eligible history from one
  target repository. Multiple repositories are fitting and evidence units,
  never one mixed Task Pool.
- Primary baseline: all eligible local history.
- Calibration: uniform ten-Task Selection with 20,000 deterministic draws.
- Cost: zero paid API calls, zero coding-Agent calls, and no new embedding
  calls.

The official pinned revision has 18 submissions satisfying the
outcome-independent metadata rule `checked=true`, `os_system=true`, and one
attempt. Three were already open, one had been inspected during earlier
feasibility work, and 14 remained project-sealed. Mechanism-family-stratified
alternation assigned eight to development and six to holdout before result
contents were read.

Three older development files used an official legacy result schema. A
post-open schema-only amendment binds their exact blob identities and exact
field set. It does not change the endpoint: `resolved` is pass and every other
Task in the exact 500-Task denominator is fail.

## Experiments

Negative differences favor Selection.

| Mechanism | Wide difference | Deep difference | Key audit | Decision |
| --- | ---: | ---: | --- | --- |
| Robust block median | `+0.01284` | `+0.00634` | 1/7 wide repositories favorable | Retire |
| Repository analog | `+0.01402` | `+0.06833` | 3/7 wide favorable | Retire |
| Semantic trend coreset | `+0.02600` | `+0.03333` | 1/7 wide favorable | Retire |
| Joint response Markov, original 3 Agents | `-0.01911` | `-0.00896` | Nominal screen passed | Audit required |
| Joint response Markov, adversarial audit | — | — | temporal null `0.100`; leave-one-Agent macro `-0.00043`, only 1/3 favorable | Retire |
| Joint response Markov, 8-Agent sealed replication | `+0.00031` | `+0.00626` | 4/7 wide favorable; interval `[-0.01037, +0.01225]` | Retire confirmed |
| Cutoff-aware Agent-invariant difficulty Markov | `-0.00888` | `+0.00920` | 97.78th random percentile; null `0.066`; leave-one-Agent macro `-0.00398`, 6/11 favorable | Retire; gate failed |
| Stationary difficulty ablation | `+0.00229` | `+0.00696` | 2/7 wide favorable | Retire |
| Adaptive prequential difficulty | `-0.00235` | `+0.00927` | 90.28th random percentile; null `0.194`; leave-one-Agent macro `-0.00080`, 6/11 favorable | Retire and stop current-pool search |

The first theory screen also reproduced the prior history-match control at
`-0.00637`. When those exact three-Agent history-match memberships are
evaluated on the expanded 11-Agent development panel, their wide effect becomes
`+0.00349`. This is another warning that a favorable response-matrix fit can be
panel-specific.

## What The Audits Changed

### Agent transfer

The original Joint Markov encodes one of eight exact three-Agent response
states. It looked strong on the same Agents used to construct those states,
but did not transfer to eight outcome-independently selected Agents. The
Agent-invariant successor therefore keeps only a Task's solve-rate state and
constructs every leave-one-Agent Selection without the evaluated Agent.

That change improves the audit: the fixed difficulty Markov has a negative
leave-one-Agent macro effect. Direction is still favorable for only 6/11
Agents, below the frozen 8/11 gate.

### Calendar availability

The first Joint Markov held out the target repository but fitted other
repositories using their complete records. Of 19,985 cross-repository training
Task uses, 9,467 (`47.37%`) were created after the target Origin cutoff, and
all 68 Origins were affected. This is valid only as retrospective transfer,
not strict rolling-origin fitting.

The Agent-invariant and adaptive experiments allow only other-repository Tasks
whose `created_at` is no later than the final target-history Task. For the
fixed Markov fit, the number of non-target repositories contributing at least
one eligible Task ranges from two to six. Every Origin has at least one
eligible Task, so none uses the symmetric empty-data fallback.

### Deep-history behavior

The fixed difficulty Markov helps Astropy, Xarray, and scikit-learn, but harms
Django, Sphinx, SymPy, and Matplotlib. All three deep repositories are harmful.
The adaptive model selects Markov at 49/68 Origins and stationary at 19/68,
yet its deep effect remains positive. Prequential fit to historical states is
therefore not a reliable proxy for future benchmark-representation gain.

## Current Data Boundary

A post-result, outcome-free supply audit counts completed other-repository
Origins available by each target cutoff. These are the records that could
train a learned adaptive gate. Across the 68 target Origins:

- the available training-Origin count ranges from 0 to 61, with median 11;
- the available training-repository count has median 2;
- four Origins have no completed training Origin;
- 35/68 Origins have fewer than three training repositories.

This is too thin for a credible learned gate whose claim is cross-repository
generalization. Continuing to search thresholds or features on the same 68
opened Origins would increase selection bias faster than evidence.

The compact audit is stored in
`adaptive-difficulty-results.json` under
`calendar_training_origin_supply`; its per-Origin counts are self-digested.

## Decisions

1. Do not open the six-Agent holdout. No frozen candidate passed every gate.
2. Do not pay for task-solving or validation. The blocker is candidate validity,
   not API access or infrastructure.
3. Close additional temporal-Selector invention on the current opened Task
   Pool. Reopen only for a mechanism derived independently of these results or
   for more source-time-eligible repository-local Origins.
4. Keep full history as the primary baseline and equal-budget random Selection
   as the sampling-landscape calibration.
5. Keep the six-Agent panel sealed for a future prespecified candidate. Public
   availability makes this project-sealed evidence, not private prospective
   evidence.
6. Do not add a core trainer, model registry, multi-repository Runner, or
   embedding service. The direct experiment layer remains sufficient.
7. Treat fixed-universe score reconstruction as a separate estimand. It must
   not be reported as evidence that a Selection predicts future Tasks.

## Reopening Conditions

A next temporal candidate must have a mechanism specified without another
search over these opened outcomes. Before the six-Agent holdout can be opened,
it must meet all current development gates:

- wide difference at most `-0.01`;
- at least five of seven repository directions negative;
- every wide leave-one-repository-out result negative;
- deep direction negative;
- better than at least 75% of random draws;
- better than the relevant frozen controls;
- temporal-null rate below `0.10`;
- leave-one-Agent macro negative and at least 8/11 Agents favorable.

Independent validity still needs the stronger project gate: `0.02` improvement,
a 95% interval wholly below zero, no repository-cluster sign reversal, and a
later source or strict-prospective confirmation.

## Reproduction And Artifacts

All committed plans and results are self-digested under
[`examples/multi_repository_study/`](../../examples/multi_repository_study/).
Raw official result files remain ignored.

The evidence sequence is:

1. `theory-plan.json`, `theory.py`, and `theory-results.json`;
2. `theory-audit-plan.json`, `theory_audit.py`, and
   `theory-audit-results.json`;
3. `agent-panel-extension-plan.json`,
   `agent-panel-schema-amendment.json`, `panel_extension.py`, and
   `agent-panel-replication-results.json`;
4. `agent-invariant-plan.json`,
   `agent-invariant-execution-amendment.json`, `agent_invariant.py`, and
   `agent-invariant-results.json`;
5. `adaptive-difficulty-plan.json`, `adaptive_difficulty.py`, and
   `adaptive-difficulty-results.json`.

Mechanism background was drawn from primary literature on
[categorical time-series Markov modeling](https://projecteuclid.org/journals/bayesian-analysis/volume-5/issue-2/Model-based-clustering-of-categorical-time-series/10.1214/10-BA606.full),
[analog forecasting](https://arxiv.org/abs/2007.14216),
[median-of-means robustness](https://arxiv.org/abs/1711.10306), and
[kernel herding and convex projection](https://www.jmlr.org/papers/v18/16-147.html).
These sources motivate mechanism families; the Barcarolle measurements decide
their status here.
