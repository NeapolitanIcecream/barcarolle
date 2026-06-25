# Prompt For GPT-5.5-Pro: Learned Selector Roadmap

Use this prompt with GPT-5.5-Pro or another external reviewer. The model should
not assume access to the local workspace. It should reason from the context
below and produce an implementation-oriented research roadmap.

```text
You are reviewing Barcarolle, a target-repository benchmark compiler for coding
Agents. Please design a research roadmap for its learned task selector.

Context
-------

Barcarolle's goal is to compile repository-specific benchmarks that predict how
complete coding Agents will perform on later real work in the same repository.

An Agent means the full tested setup:

- model;
- harness;
- prompt or repository instructions;
- tools;
- retrieval or skills;
- runtime policy and budget.

Barcarolle does not implement the Agent harness. It prepares a clean solver
workspace, invokes the Agent, captures the diff, replays the diff in a fresh
verifier workspace, runs hidden checks, and records result rows.

The planned v2 system has only a few core objects:

- Task: problem statement plus repository/base/time metadata.
- Check: verifier or oracle for the task. It may be tests, scripts, GUI
  screenshot evaluation, LLM/human judgment, or user-provided regression logic.
- Workspace: isolated solver/verifier execution.
- Result: one Agent on one Task, with pass/fail/invalid, cost, latency, and
  failure labels.
- Selector: chooses a benchmark from historical tasks under a budget.
- Rolling origin: at origin time t, select from tasks before t and compare
  selected-benchmark performance with future tasks after t.

Three assets are intentionally decoupled:

- Task Pool: generated or imported tasks, checks, metadata, and certification
  records.
- Benchmark Selection: selector version, origin, history pool, selected task
  IDs, weights, and budget.
- Agent Results: cached outcomes for Agent x Task x environment, with cost and
  verifier status.

This decoupling is important. Sometimes Barcarolle will first select a benchmark
and then run only the missing paid Agent-task cells. But for selector research,
the more important mode is often a prepaid or cached task pool: after a set of
Agent x Task cells has been paid for once, many selector candidates should be
evaluated virtually against the cached result table without paying again. The
selector roadmap should assume result caching is a first-class design
constraint.

Task supply should reuse and adapt related-work task-generator patterns rather
than inventing a similar method from scratch. Relevant families include:

- SWE-bench-style issue/PR tasks with fail-to-pass and pass-to-pass tests;
- SWE-bench Verified-style quality filtering for clarity, correct tests, and
  solvability;
- SWE-bench Live-style continuous refresh and origin-aware freezing;
- SWE-Bench Pro-style harder long-horizon or enterprise-like task scope;
- SWE-Bench++ / SWE-Bench Atlas-style automated large-scale task generation;
- SWE-smith-style task/environment generation for large task supply;
- SWE-Future-style forecast-conditioned future-oriented task synthesis;
- SWE-EVO-style release or software-evolution tasks when single issue repair is
  too narrow;
- user-provided task pools and custom checks.

For selector research, task generator provenance and certification quality are
features and possible sources of bias. Please account for them.

Current empirical lessons
-------------------------

1. Task supply limits prediction quality. In the Agent Selection Demo, even a
   selector that beat most random samples still appeared to have material
   systematic bias because available tasks did not fully represent future work.

2. Paid Agent results are reusable assets. In the demos, many selector variants
   were tested against cached Agent x Task outcomes. A practical system must
   support this mode; rolling-origin selector development should not repeatedly
   pay for the same cells.

3. Rule-based selectors can be useful. Simple recency/coverage/stratified
   selectors are understandable and can serve as fallbacks.

4. Learned selectors are the main research opportunity. They should learn from
   historical rolling-origin evidence and adapt as new outcomes arrive.

5. Goodhart's Law is a central risk. Benchmark predictive validity must be kept
   separate from tuning utility:
   - predictive validity asks whether a benchmark generated at time t predicts
     future performance of Agents available at time t;
   - tuning utility asks whether benchmark feedback can modify an Agent
     artifact and improve later performance.

6. Paid coding-Agent cells are expensive. The roadmap should be data-efficient,
   make maximal use of existing paid result tables, and define when new paid
   cells are actually worth running.

Objective
---------

Design the learned Selector research roadmap.

The north-star metric is future pass-rate prediction error, initially MAE
between selected-benchmark pass rate and future-holdout pass rate for each
Agent or Agent pair.

Supporting metrics include:

- top-rank agreement;
- top-tier agreement;
- recommendation regret;
- calibration bias;
- catastrophic miss rate;
- robustness across rolling origins, repositories, Agent subsets, and budgets;
- scoreable/invalid rate;
- task diversity;
- cost and latency.

The goal is to greatly reduce prediction error while keeping robustness and
operational metrics from degrading too much.

Questions to answer
-------------------

1. Formal problem
   - How should the learned selector problem be formulated?
   - What exactly are the inputs, outputs, labels, and loss functions?
   - Should the first learned objective predict absolute pass rate, relative
     Agent ranking, pairwise regret, calibrated task weights, or a mixture?

2. Feature design
   - What task features are likely useful and leakage-safe?
   - Which features can come from repository metadata, changed files, tests,
     problem statements, task generator provenance, historical Agent outcomes,
     failure labels, cost, and recency?
   - Which features should be banned because they leak future information or
     oracle details?

3. Algorithm families
   - Propose several concrete learned selector designs, ordered from simple and
     data-efficient to more ambitious.
   - Include rule-based selector mixtures, pairwise/ranking models, calibrated
     weighting models, bandit or online-update ideas, uncertainty-aware
     selection, and drift-aware adaptation if appropriate.
   - For each design, explain what data it needs, how it is trained, how it
     selects tasks, how it avoids overfitting, and how it fails.

4. Adaptive controller
   - How should the system decide whether to trust a learned selector, a
     rule-based selector, or a mixture?
   - How can it detect that a selector has become stale as future task
     distribution drifts?
   - How should recent rolling-origin performance influence selector choice
     without creating an uncontrolled Goodhart loop?

5. Rolling-origin validation
   - Specify the exact rolling-origin evaluation protocol.
   - How should history pool, selected benchmark, and future holdout be defined?
   - How should the protocol prevent future-outcome leakage?
   - Which metrics should be preregistered?
   - What should count as a convincing win over random, temporal, and simple
     stratified baselines?

6. Low-budget experiment plan
   - Given limited paid Agent cells, what experiments should be run first?
   - How can existing paid result tables be reused without fooling ourselves?
   - How should the system decide between prepaid-pool evaluation,
     select-then-run evaluation, and incremental cache fill?
   - What cache identity fields are required before a result can be reused?
   - When should we stop, expand task supply, or pay for more Agent outcomes?
   - What is the smallest experiment that can show a meaningful directional
     signal?

7. Task supply interaction
   - How should selector research use information about task generator family
     and certification quality?
   - How can the selector diagnose that task supply, rather than selection
     algorithm, is limiting predictive validity?
   - How should synthetic or LLM-generated tasks be treated differently, if at
     all?
   - Which related-work generator families should be replicated first, and
     what evidence would show that a replicated generator actually improves
     prediction rather than only increasing task count?

8. Implementation roadmap
   - Give a staged roadmap that a local Codex Agent could implement.
   - Each stage should have inputs, code artifacts, experiments, success
     criteria, and stop conditions.
   - Prefer a roadmap that starts with a clean v2 skeleton and avoids importing
     unnecessary old experiment abstractions.

9. Risks and red flags
   - Identify the most likely ways this research could fool us.
   - Include Goodhart risks, data leakage, overfitting to a repository, task
     supply bias, unstable Agents, small-sample noise, and paid-cost traps.
   - Give practical safeguards for each.

Requested output format
-----------------------

Please write the answer in clear sections:

1. Executive recommendation.
2. Formal selector formulation.
3. Feature and leakage policy.
4. Algorithm candidates, with a compact comparison table.
5. Adaptive/drift strategy.
6. Rolling-origin validation protocol.
7. Low-budget experimental plan.
8. Implementation roadmap for Codex.
9. Key risks and safeguards.
10. What not to do yet.

Keep the answer concrete. Avoid inventing new product names or unnecessary
terminology. If a method is speculative, label it as speculative. If a claim
would require more paid data, say exactly what data is needed.
```
