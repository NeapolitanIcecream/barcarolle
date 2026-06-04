# Project State After Proposal

Status: canonical handoff snapshot, 2026-06-04.

This document records the state Barcarolle should have on main after the
proposal-stage work is complete. It is the single starting point for future
development and experiments.

## Project Position

Barcarolle is a target-repository benchmark compiler for coding-agent
evaluation and tuning.

It is not:

- an Agent harness;
- a general SWE task factory;
- a public leaderboard;
- an Agent License product by itself.

The core project is task selection, certification, release construction,
calibration, and feedback for a specific repository and Agent family. Task
generation is supply infrastructure. Agent License and Agent Tuning are
downstream product directions.

## Agent Boundary

An Agent means the full tested configuration:

```text
model + harness + prompt/skills + tools + retrieval + runtime policy + budget
```

Older reports use ACUT (`Agent Configuration Under Test`) for the same idea.

Barcarolle does not implement the Agent's internal harness. It prepares a clean
solver workspace, provides solver-visible task material, invokes the configured
Agent harness, captures the final Git diff, replays that diff in a fresh
verifier workspace, injects private oracle material only there, and records
sanitized status, cost, latency, and failure labels.

## What We Know

The workspace Agent protocol works well enough for pilot evidence:

- the three-repo paid validation ran `120` planned cells, completed `120`, and
  had `120` scoreable cells with endpoint compliance and no policy violations;
- the observed/conservative cost for that pilot was `$51.267333`;
- the primary conservative design was `repo_stratified`, with primary gap `0.1`
  under the preregistered `<= 0.15` pilot threshold.

Task selection matters:

- the old weighted target-profile design failed the paid pilot: `44` scoreable
  cells, gaps `0.3148` for attrs and `0.7481` for boltons, while simple
  baselines were much better;
- this is evidence that a bad selector can mislead, not evidence that a new
  selector is already solved.

There is traction for selection optimization:

- in a 1000-seed retrospective same-budget random comparison, the
  `coverage_constrained_unweighted` candidate beat or tied random samples on
  overall MAE in `93.4%` of samples;
- against the best simple baseline envelope, the same candidate is only
  slightly better overall (`0.209` MAE versus `0.2149`) and loses on several
  adapter, repository, and window slices.

The current evidence supports continued work and proposal traction. It does not
prove predictive validity.

## What We Do Not Claim

Barcarolle has not established that its benchmark releases predict future Agent
performance better than simple baselines.

Do not claim:

- predictive validity is proven;
- the current selector is generally superior;
- public benchmark rank predicts target-repo future work;
- adapter differences are model-only effects;
- task generators alone solve the repo-specific benchmark problem.

## Evidence Map

| Evidence | Path | Supports |
| --- | --- | --- |
| Final proposal report | `docs/research/barcarolle-proposal-report-v5.md` | Reader-facing project claim and product route. |
| Evidence manifest | `experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md` | Audit index for proposal evidence. |
| Weighted pilot | `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md` | Bad selection can mislead; old weighted design is not mainline. |
| Local algorithm bakeoff | `experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md` | Keep simple stratified reporting; local candidate not paid-ready. |
| Three-repo paid validation | `experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md` | Workspace protocol and conservative pilot feasibility. |
| Random baseline distribution | `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md` | Retrospective traction versus random same-budget samples. |
| Baseline envelope | `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md` | Candidate fragility versus best simple baselines. |
| Validation hardening | `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md` | Future claim gates, adapter handling, and candidate policy. |
| Task supply bakeoff | `experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md` | Internal repo-history generator remains useful supply infrastructure. |
| Source-context repair | `experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md` | LLM-assisted statement/source repair can be used under provenance and review controls. |

## Algorithm State

The current conservative reporting mainline is repo-stratified or simple
stratified baselines.

The old metadata-weighted target-profile design is diagnostic only. It should
not be promoted to a primary design.

Candidate selectors remain open research. Useful directions include:

- coverage-constrained unweighted selection;
- blocked and stratified variants;
- temporal recency baselines;
- shrinkage or capped weighting when support is sparse;
- information-aware or active benchmark refinement once supply grows.

The next credible proof step is preregistered rolling-origin or true future
holdout validation against simple baselines. In plain terms: freeze a benchmark
using only what would have been known at an earlier time, predict later Agent
performance, then compare that prediction with the actual later outcomes.

## Task Supply And Oracle Sources

Current task supply mostly comes from repository history: commits, pull
requests, issues, changed tests, and reconstructed base commits. This is supply
infrastructure, not the core claim.

Current oracle sources include:

- changed tests from historical work;
- pass-to-pass guards;
- verifier packages assembled from recovered test material;
- manual review of source context and leakage risk.

Future supply or oracle sources can include external task generators, SWE-style
pipelines, generated tests after review, manual customer regressions, and
canaries. All sources must pass local certification before entering a release.

## Next Development Route

The next project work should move from proposal evidence to compiler
development and stronger validation:

- implement a clearer compiler v1 around normalized candidates, certification,
  release manifests, selector policies, scoring, and uncertainty;
- keep task source adapters source-agnostic so external generators can be used
  when they become useful;
- expand certified supply until each claimed repository has enough eligible
  tasks for meaningful selection experiments;
- implement selection experiments against preregistered random, stratified, and
  temporal baselines;
- run rolling-origin or true future holdout validation before making predictive
  validity claims;
- expose Agent run evidence, failure labels, cost summaries, and reward signals
  for tuning loops.

## Product Directions

Agent Tuning is the nearer product direction. Barcarolle can supply benchmark
releases, failure labels, reward signals, uncertainty, and before/after reports
for optimization loops.

Agent License is a lighter future direction. A license can summarize evidence
about whether an Agent is ready for a repository, but that product should depend
on benchmark validity rather than replace it.

## Repository Layout

Active material:

- `README.md`: repository entry point.
- `AGENTS.md`: agent-session rules and artifact hygiene.
- `PROCESS.md`: durable process decisions.
- `docs/architecture/system-design.md`: active architecture.
- `docs/research/barcarolle-proposal-report-v5.md`: final proposal report.
- `docs/research/project-state-after-proposal.md`: this canonical state doc.
- `experiments/phase1_compiler/`: compiler prototype, schemas, tests, selected
  reports, and small evidence tables.
- Retained `raw_*` task-supply files are mined candidate inventories, not raw
  LLM prompts, completions, or transcripts. They remain because current
  configs, tests, and evidence reports reference them.
- `experiments/phase0_headroom/`: retained historical task-supply and
  workspace-adapter evidence used by the compiler prototype.

Archived material:

- `archive/2026-05-agent-license-reset/`: historical Agent License and
  core-narrative notes retained only for audit or future productization
  reference.

Removed from active mainline:

- old Agent License architecture and decision docs;
- old core-narrative experiment tree;
- `.codex-workflows` process bundles;
- proposal/deck runbooks, PPT outputs, raw transcripts, solver/verifier
  workspaces, local virtual environments, caches, and large raw outputs.
