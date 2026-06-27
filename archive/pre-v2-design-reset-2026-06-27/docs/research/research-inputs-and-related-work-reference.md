# Research Inputs And Related Work Reference

Status: post-proposal synthesis, 2026-06-04.

This note condenses still-useful material from the May research inputs and the
external review into a reference for compiler-v1 development. It is not a
replacement for the proposal report or the canonical project state.

Source inputs synthesized:

- 2026-05-19 research outline;
- 2026-05-26 weighted-pilot review;
- 2026-05-26 task-generator/source-adapter plan;
- 2026-05-30 external review.

The Chinese proposal translation is intentionally not part of this repository
state.

## Active Takeaways

Barcarolle is a target-repository benchmark compiler. Its central object is a
versioned benchmark release for one target repository or a narrow repository
family, not a generic pool of SWE tasks.

The tested Agent owns its own harness. In current docs, an Agent means:

```text
model + harness + prompt/skills + tools + retrieval + runtime policy + budget
```

Older reports use ACUT for the same boundary. Barcarolle prepares the task
workspace, invokes the configured Agent harness, captures the final Git diff,
replays that diff in a verifier workspace, injects private oracle material only
there, and records sanitized score/cost/latency/failure evidence.

Predictive validity remains the north star, not a completed claim. The working
question is whether a repo-specific benchmark release can estimate later
same-repo Agent performance better than simple alternatives such as random,
recent-temporal, unweighted same-repo, repo-stratified, generic benchmark, or
external-generator baselines.

Task generation is supply infrastructure. The compiler claim is about choosing,
certifying, splitting, scoring, and interpreting tasks under a target repo,
Agent boundary, budget, and validation objective.

## Related Work Position

Existing SWE systems are useful upstreams and design references. They should not
be treated as the project identity.

| System | Useful reference | Barcarolle gap |
| --- | --- | --- |
| SWE-bench | Repository-level issue-resolution task form, fail-to-pass tests, pass-to-pass guard pattern, Dockerized evaluation. | It is a fixed public benchmark over a finite source distribution, not a target-repo future-work estimator. |
| SWE-bench Verified | Human filtering and feasibility review for task statements, tests, and setup reliability. | It improves a public subset but does not solve target-repo selection, future holdout, or contamination risk for frontier models. |
| SWE-Bench Pro | Private/held-out splits, contamination-resistant design, longer-horizon industrial tasks, human-augmented specs. | It is still a benchmark suite; it does not tell a repo owner which small same-repo release should predict their own future work. |
| SWE-bench Live | Fresh issue sourcing, automated environment construction, monthly/live refresh, broader repo coverage. | Freshness reduces staleness but does not replace frozen repo-specific validation against later target work. |
| SWE-Bench++ | Scalable PR sourcing, environment synthesis, oracle extraction, QA, multilingual metadata, possible upstream adapter. | It is a task-production framework. Barcarolle needs to decide which certified tasks become a target-repo release and how that release is validated. |
| SWE-smith | Synthetic/test-breaking task supply, execution-environment construction, training-data evidence, possible Python reservoir. | Synthetic tasks need source labels, caps, local certification, and predictive-value validation before they can support evaluation claims. |
| SWE-Gym / R2E-Gym | Training environments, executable tasks, verifier training, synthetic or hybrid oracle ideas. | They are closer to training infrastructure than target-repo benchmark compilation. |
| SWE-Bench+ / related quality audits | Leakage, weak-test, setup, and oracle-quality risks. | These strengthen Barcarolle's certification requirements rather than providing a ready selector. |

Public anchors checked on 2026-06-04:

- [SWE-bench](https://www.swebench.com/original.html) describes 2,294 task
  instances from 12 Python repositories with fail-to-pass tests as the primary
  evaluation signal.
- [SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/)
  is a 500-sample human-validated subset of the original SWE-bench test set.
- OpenAI later argued that [SWE-bench Verified no longer measures frontier
  coding capabilities](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)
  because of residual test-quality issues and contamination at frontier-model
  performance levels.
- [SWE-bench Live](https://arxiv.org/abs/2505.23419) reports 1,319 initial
  tasks from 93 repositories and an automated curation pipeline for live updates.
- [SWE-Bench++](https://arxiv.org/abs/2512.17419) describes PR-to-task
  production through programmatic sourcing, environment synthesis, oracle
  extraction, and QA, with 11,133 instances from 3,971 repositories across 11
  languages.
- [SWE-smith](https://openreview.net/forum?id=63iVrXc8cC) reports a synthetic
  training-data pipeline with 50k instances from 128 Python repositories; its
  [repository](https://github.com/SWE-bench/SWE-smith) lists 52k task instances
  and 250+ environments.
- [SWE-Gym](https://github.com/SWE-Gym/SWE-Gym) presents 2.4k real tasks from
  11 Python repositories for training agents and verifiers.
- [R2E-Gym](https://github.com/R2E-Gym/R2E-Gym) reports more than 8.1k problems
  across 13 repositories with executable gym environments, unit tests, and
  natural-language task descriptions.
- [SWE-Bench Pro](https://arxiv.org/abs/2509.16941) reports 1,865 problems
  across 41 actively maintained repositories with public, held-out, and
  commercial subsets.

The positioning sentence to preserve is:

> The bottleneck Barcarolle works on is not producing more SWE tasks. It is
> compiling the right certified tasks into a release that predicts and improves
> performance for a specific repository.

## Task Source Adapter Policy

Barcarolle should stay source-agnostic. The practical design is hybrid:
strengthen the internal repo-history generator, then add external adapters as
additional reservoirs.

Candidate reservoirs should be tracked separately:

- real issue or PR tasks with public context;
- real commits with changed tests;
- real commits without issue context;
- generated or minimized regression tests;
- synthetic mutation or test-breaking tasks;
- manual/customer regressions;
- private canaries;
- imported external tasks.

Each candidate should normalize to a schema that records at least:

- source system, version, license, and provenance;
- source reservoir and dedup key;
- repository, language, base commit, optional target commit, and task time;
- solver-visible statement and statement provenance;
- hidden-oracle references that stay out of solver view;
- fail-to-pass and pass-to-pass oracle metadata;
- environment manifest;
- changed files, task family, and module labels;
- leakage, ambiguity, and source-confidence flags;
- reference-patch digest where available;
- raw artifact paths under ignored storage only.

External tasks are untrusted until locally certified. Upstream QA is useful
evidence, but it does not replace Barcarolle's checkout, environment, no-op
fail, reference pass, pass-to-pass, flakiness, leakage, statement, policy, and
cost checks.

Initial release policy should be conservative:

- require enough certified same-repo supply before paid validation;
- require more than one reservoir for a claimed repo when feasible;
- cap any one reservoir's release share;
- cap synthetic/generated supply until local evidence supports a higher share;
- cap commit-message-only statements unless reviewed;
- label every fallback from the primary selector.

## Certification And Oracle Policy

Certification is part of the compiler boundary. It should expose subgate
failures instead of collapsing everything into "reference pass failed".

Active certification gates:

- checkout/base-commit replayability;
- install, import, collection, and environment subgates;
- no-op or base failure for fail-to-pass tests;
- reference pass after applying the reference change;
- pass-to-pass guard where feasible;
- repeated-run flakiness checks;
- timeout and cost bounds;
- statement clarity and ambiguity review;
- leakage review;
- source-context provenance;
- source reservoir, module, time, task family, change-size, and statement labels.

Current oracle supply mostly comes from repository history and changed tests.
Future oracle supply can include generated/minimized tests, manual regressions,
external task systems, and canaries, but only after local certification and
clear source labels.

Solver-facing statements must be derived from public, non-oracle context:
issues, public docs, module names, and redacted public PR/context snippets. They
must not use gold patches, hidden tests, raw solver transcripts, raw
prompts/completions, or post-solution comments that reveal the implementation.

Endpoint-compliant LLM statement rewriting or review can be useful. Commit only
structured sanitized artifacts such as input references, model/endpoint hash,
clarity ratings, ambiguity flags, leakage flags, decisions, and statement IDs.

## Algorithm Direction

The old metadata-weighted target-profile design is demoted. The paid pilot
showed that sparse metadata matching and marginal weights can produce severe
misleading gaps even when the execution protocol is clean. The lesson is not
that weighting is impossible; it is that small-N, high-dimensional,
provenance-heavy weighting is unsafe without support diagnostics and fallback.

Current conservative mainline:

- repo-unweighted same-budget baseline;
- repo-stratified or simple stratified baseline;
- temporal recent baseline;
- many-seed random same-budget distribution;
- coverage-constrained unweighted selection as a research candidate, not a
  validated compiler.

Useful next algorithms:

- blocked or matched stratified selection;
- seeded block-randomized splits;
- coverage-constrained unweighted selectors with explicit fallback;
- low-dimensional shrinkage weighting with weight caps and effective-sample-size
  checks;
- uncertainty-aware reporting;
- active benchmark refinement only after certified supply grows.

If weighting returns, it should be gated:

- estimate target profile from pre-cutoff target events, not from the candidate
  pool alone;
- use low-dimensional strata and merge rare buckets;
- cap maximum task weights;
- report effective sample size and uncovered target mass;
- shrink to uniform or fall back to unweighted/stratified when support is
  insufficient;
- report uncertainty intervals instead of only point estimates.

## Validation Boundary

Retrospective pseudo-future replay can debug selectors and show early traction.
It cannot prove predictive validity once outcomes, repos, windows, feature
choices, or fallback choices have influenced the study design.

Predictive-validity claims require one of:

- true future holdout: freeze the benchmark release, wait for later target-repo
  work/outcomes, then evaluate the frozen prediction;
- strict preregistered rolling origin: freeze repos, cutoffs, task supply,
  features, seeds, selectors, baselines, invalid-cell policy, adapters, score
  joins, and success thresholds before future outcomes are inspected or joined.

Baselines should be strong enough that a win matters:

- temporal recent same-budget baseline;
- repo-unweighted same-budget baseline;
- repo-stratified baseline;
- many-seed random same-budget distribution with percentile reporting;
- best-simple-baseline envelope;
- coverage-only ablation when a richer compiler candidate is claimed;
- external or generic nearest-neighbor baseline when external supply is used.

Metrics should include MAE/RMSE for pass-rate prediction, signed error,
catastrophic miss rate, adapter- and repo-stratified deltas, invalid-cell
sensitivity, scoreable-cell counts, cost, latency, and uncertainty where
feasible.

The safe claim remains:

> Barcarolle has built auditable repo-specific benchmark-construction machinery,
> found that naive weighting is fragile, and produced weak retrospective signal
> that justifies future validation work. It has not proven predictive validity.

## Product Direction

Agent Tuning is the nearer product direction. Barcarolle can provide certified
dev/eval/canary splits, failure labels, reward-like signals, scorecards,
uncertainty, and before/after Agent comparison reports.

Agent License is a later packaging direction. It can summarize whether an Agent
appears ready for a repository, but it should depend on benchmark evidence
rather than become the core research claim.

## Obsolete Or Demoted Ideas

Do not carry these forward as active claims:

- Agent License as the core project identity;
- public leaderboard packaging as the main deliverable;
- ranking reversal as the central research objective;
- task generation volume as the novelty claim;
- SWE-Bench++ or SWE-smith as competitors to beat at task production;
- old metadata-weighted target-profile selection as primary algorithm;
- candidate-pool metadata distribution as a sufficient future-work profile;
- deterministic small-N metadata matching as a strong estimator;
- pooled Agent metrics without adapter-level reporting;
- pseudo-future replay as predictive-validity proof;
- paid validation authorization based only on weak retrospective edge or random
  baseline wins.

## Implementation Priorities

1. Define normalized schemas for candidates, sources, releases, target profiles,
   score tables, run manifests, and certification reports.
2. Build source adapter v2 with reservoir labels, provenance, license fields,
   raw-artifact references, and dedup keys.
3. Integrate historical environment synthesis and certification subgates.
4. Strengthen oracle handling with changed tests, pass-to-pass guards,
   generated/minimized tests where appropriate, and base/reference triage.
5. Add deterministic statement readiness plus optional endpoint-compliant
   statement review with structured artifacts only.
6. Implement selector policies as named audited objects: unweighted,
   stratified, temporal, many-seed random, coverage-constrained, blocked
   stratified, and shrinkage-weighted research variants.
7. Make fallback explicit in every release manifest and report fallback share.
8. Report target coverage, uncovered mass, sparse strata, effective sample size
   for weighted modes, invalid cells, cost, latency, and uncertainty.
9. Build validation tooling around true future or strict rolling-origin designs,
   with retrospective replay labeled separately.
10. Keep tuning outputs practical: split metadata, failure taxonomy, reward
    schema, scorecards, and before/after Agent configuration comparisons.
