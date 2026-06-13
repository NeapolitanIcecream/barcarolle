# Barcarolle Process Notes

This file records repository-wide process decisions that future coding-agent
sessions should know before planning or executing Barcarolle work.

Last updated: 2026-06-12.

## Maintenance Rules

- Read this file after `AGENTS.md` when working on experiments, paid validation,
  Agent adapters, benchmark design, or research interpretation.
- Keep this file short. Link to canonical reports instead of copying evidence.
- Update it when the active research direction, paid-call boundary, mainline
  algorithm, claim boundary, or cross-session handoff state changes.
- Do not use this file as a runbook, lab notebook, prompt archive, raw artifact
  manifest, or deck revision log.

## Active Boundary

Barcarolle is a target-repository benchmark compiler for coding-agent
evaluation and tuning. It is not an Agent harness, a general SWE task factory,
an Agent License product, or a public leaderboard.

The tested Agent owns its own harness: model calls, prompt or skills, tools,
retrieval, file search, editing strategy, retries, public-test policy, and
runtime budget. Barcarolle prepares clean solver workspaces, gives only
solver-visible task material, invokes the configured harness, captures the final
diff, verifies it in a fresh hidden-oracle workspace, and records sanitized
status, cost, latency, and failure labels.

Canonical state document:

- `docs/research/project-state-after-proposal.md`

Current reader-facing narrative:

- `docs/research/current-project-story.md`

## Claim Boundary

Predictive validity is the north star, not an established result. The current
evidence supports project traction and a concrete validation path:

- the workspace Agent protocol can run scoreable paid cells;
- task selection matters, because weak selection can mislead;
- coverage-constrained selection has retrospective traction against random
  same-budget samples;
- the best current candidate is not paid-ready and does not beat simple
  baselines robustly across adapters, repositories, and windows.

Do not claim that Barcarolle has proven predictive validity, a generally
superior task selector, or a production leaderboard ranking.

Frozen proposal and evidence:

- `docs/research/barcarolle-proposal-report-v5.md`
- `experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md`

The V5 proposal report is a frozen proposal-stage artifact. Use it for audit
and evidence context, not as the live source of the current project story.

## Algorithm Mainline

Do not promote the old weighted target-profile design. It failed the paid pilot
and remained underidentified in the local bakeoff.

Use repo-stratified or simple baselines as the conservative reporting mainline
until a candidate selector wins on preregistered future holdout or rolling-origin
tests. Coverage-constrained, blocked, temporal, shrinkage-weighted, and
information-aware variants remain valid research candidates when labeled as
such and compared against simple baselines.

Canonical reports:

- `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`
- `experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md`

## Paid-Run Boundary

Do not run new paid Agent cells by default. Future paid validation needs a
frozen release, preregistered baselines, adapter-stratified analysis, score-join
rules, cost accounting, uncertainty reporting, and explicit success criteria.

All paid LLM or Agent calls must use `LLM_BASE_URL` plus `LLM_API_KEY`; no
fallback endpoint is allowed unless the user updates `AGENTS.md`.

Exception: the Agent selection demo proposal dated 2026-06-12 is an approved
execution plan if its repository gate, candidate smoke tests, frozen conditions,
stop conditions, and artifact-hygiene rules are satisfied. Treat
`docs/research/agent-selection-demo-execution-proposal-2026-06-12.md` as the
source of truth for that demo. Do not let older phase/proposal wording in this
file block the demo when the proposal explicitly authorizes the run.

Agent selection demo execution completed on 2026-06-12 for `mahmoud/boltons`.
The selection set recommended Codex + GPT mainline, but the holdout check
contradicted that recommendation: Kilo + GPT mainline led the holdout. The
demo supports the end-to-end selection workflow and this target-repo/candidate
observation only; do not present it as a cross-repository or model-family
ranking.

Canonical demo artifacts:

- `experiments/agent_selection_demo/reports/target_repo_coding_agent_selection_demo_report_zh.md`
- `experiments/agent_selection_demo/results/closeout_summary.json`
- `experiments/agent_selection_demo/results/holdout_check.json`

Current follow-up plan:

- `docs/research/agent-selection-demo-followup-plan-2026-06-13.md`
- `docs/research/agent-selection-top2-repeatability-plan-2026-06-13.md`

Canonical reports:

- `experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md`

## Product Direction

Agent Tuning is the nearer product direction: Barcarolle can provide benchmark
releases, feedback labels, cost summaries, and before/after tuning reports.

Agent License remains a possible downstream product, but it is not the current
research proof or active architecture. Historical license/admission material is
archived under `archive/2026-05-agent-license-reset/`.
