# Barcarolle Process Notes

This file records repository-wide process decisions that future coding-agent
sessions should know before planning or executing Barcarolle work.

Last updated: 2026-06-15.

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

Agent selection demo final presentation state on 2026-06-14:

- Reader-facing mainline selector: HRD v3 `70/30`, `k=10`, for the
  `mahmoud/boltons` demo slice.
- Selection recommendation: `Kilo + GPT mainline`, with HRD Selection
  `9/10` versus the other three candidate Agents at `7/10`.
- Holdout validation: Kilo remains first on Holdout at `9/10`; doubled-timeout
  top-2 repeat also favors Kilo at `9/10` versus Codex `6/10`.
- COD-lite is downgraded to an ordinary algorithm-bakeoff candidate. Do not
  present COD-lite as the final demo mainline or as a second co-mainline.
- Wrapper/reporting policy is user-facing ranking: output Agent rankings,
  selection recommendation, and evidence table. Use `recommend` for a clear
  top pass-rate advantage, `top_tier` for close Agents with cost/speed/stability
  tiebreak guidance, and `insufficient_data` only when common-valid/scoreable
  support is insufficient, outcome rows are missing, or infrastructure failure
  blocks comparison. Paired and bootstrap metrics are evidence, not vetoes.

Canonical current demo artifacts:

- `experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md`
- `experiments/agent_selection_demo/reports/selector_final_eval_zh.md`
- `experiments/agent_selection_demo/results/selector_final_eval.json`
- `experiments/agent_selection_demo/reports/selector_final_demo_closeout_zh.md`
- `experiments/agent_selection_demo/results/selector_final_demo_closeout.json`
- `experiments/agent_selection_demo/reports/selector_decision_eval_zh.md`
- `experiments/agent_selection_demo/results/selector_decision_eval.json`
- `experiments/agent_selection_demo/reports/selector_algorithm_bakeoff_eval_zh.md`

The predictive-validity completion pass froze the estimand as complete-Agent
future target-repo verified pass-rate prediction accuracy and added no-paid
rolling-origin/pseudo-future tooling. The no-paid retrospective result gives
small directional traction: `coverage_constrained_unweighted` MAE `0.209011`
versus best simple baseline `temporal_recent_baseline` MAE `0.214900`, with
both catastrophic miss rates at `0.555556`. Treat this as directional
retrospective evidence only. Predictive validity is still not established.

No new paid cells were run for predictive-validity completion. A future bounded
pilot plan is preregistered at 40 cells maximum, but it was not executed because
the current demo story already has no-paid numeric support and a paid add-on
would not by itself prove predictive validity.

Historical follow-up plans:

- `docs/research/agent-selection-demo-predictive-validity-completion-runbook-2026-06-13.md`
- `docs/research/agent-selection-demo-strict-completion-runbook-2026-06-13.md` (completed by the strict completion pass)
- `docs/research/agent-selection-demo-completion-plan-2026-06-13.md`
- `docs/research/agent-selection-demo-alignment-note-2026-06-13.md`
- `docs/research/agent-selection-demo-followup-plan-2026-06-13.md`
- `docs/research/agent-selection-top2-repeatability-plan-2026-06-13.md`

Completion package:

- `experiments/agent_selection_demo/reports/demo_completion_closeout_zh.md`
- `experiments/agent_selection_demo/reports/kilo_timeout_usage_root_cause_zh.md`
- `experiments/agent_selection_demo/reports/top2_repeat_completion_zh.md`
- `experiments/agent_selection_demo/reports/second_repo_gate_zh.md`
- `experiments/agent_selection_demo/reports/agent_tuning_feedback_summary_zh.md`

Recommended next work: if the next claim is predictive validity, run a
preregistered future or strict rolling-origin validation with frozen tasks,
Agents, baselines, seeds, score-join rules, and success thresholds. If the next
claim is cross-repo readiness, first repair attrs packaging automation: add an
attrs target profile, remove boltons-specific `repo_id` and fallback statement
assumptions from demo packaging, materialize or reference the 31-task attrs
manifest, and pin the attrs verifier environment. Do not start a second-repo
paid matrix until that no-paid gate passes.

The strict completion runbook has been executed. Do not rerun it as the default
next step; use the completed reports above as the handoff state.

The strict Agent-selection runbook left predictive validity as future work; the
predictive-validity completion pass has now filled that demo layer. Do not rerun
the predictive-validity completion runbook by default. Use the completed
artifacts above as the handoff state. Fresh holdout contradiction alone is still
not a predictive-validity result; the current predictive-validity evidence is
no-paid retrospective and directional.

Top-2 repeatability execution attempted on 2026-06-13. Gates passed for
`LLM_BASE_URL`/`LLM_API_KEY`, `gpt-5.4`, adapter unit checks, secret isolation,
reference replay, and ignored raw/workspace paths. Codex + GPT mainline
completed the 10 frozen boltons holdout repeats at `7/10`, but Kilo + GPT
mainline hit three 900-second adapter/CLI timeouts (`0/0` scoreable from 3
completed Kilo cells). The strict completion pass added one fresh Kilo repeat
attempt after smoke/gates passed; it timed out and the `--stop-on-unscoreable`
guard prevented further paid repeat cells. Current repeat accounting is 13/20
completed cells and 10/20 scoreable cells. Treat this as a Kilo adapter/CLI
infrastructure blocker, not as evidence that the Kilo holdout lead is stable or
unstable.

Do not let this blocker reframe the whole demo as a Kilo repair project. The
completed first `boltons` demo remains valid as an end-to-end target-repo Agent
selection demo that exposed an unstable selection recommendation. Kilo repair is
needed only for the narrower follow-up claim that its holdout lead is stable.

The 2026-06-14 doubled-timeout run superseded that blocker for the demo story's
top-2 path: Kilo + GPT mainline completed `10/10` scoreable doubled-timeout
repeat cells at `9/10`, while Codex + GPT mainline completed `10/10` scoreable
cells at `6/10`. Keep the old `900s` timeout rows as historical caveat, not as
the active demo blocker.

Canonical repeatability artifacts:

- `experiments/agent_selection_demo/reports/top2_repeatability_gate.md`
- `experiments/agent_selection_demo/reports/top2_repeatability_check_zh.md`
- `experiments/agent_selection_demo/reports/top2_repeat_completion_zh.md`
- `experiments/agent_selection_demo/results/top2_repeatability_check.json`
- `experiments/agent_selection_demo/results/top2_repeatability_stability_table.csv`

Canonical reports:

- `experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md`

## Selector Validation Correction 2026-06-14

The correction runbook is historical context for why the old conservative
wrapper was replaced. It showed Kilo leading Selection (`11/18` versus Codex
`6/18`) and later/Holdout (`16/30` versus Codex `7/30`), while the old wrapper
returned `need_more_evidence` because it treated one discordant paired loss as a
veto. Current reporting policy should not use that conservative abstain rule as
the demo-facing decision standard.

Canonical correction artifacts:

- `experiments/agent_selection_demo/results/selector_validation_correction_audit.json`
- `experiments/agent_selection_demo/results/selector_independent_validation_inventory.json`
- `experiments/agent_selection_demo/results/selector_corrected_protocol.json`
- `experiments/agent_selection_demo/results/selector_no_paid_independent_eval.json`
- `experiments/agent_selection_demo/results/selector_corrected_validation_closeout.json`
- `experiments/agent_selection_demo/reports/selector_corrected_validation_story_zh.md`
- `experiments/agent_selection_demo/reports/selector_corrected_validation_closeout_zh.md`

Current claim boundary: use the corrected validation artifacts as development
and audit context, not as the reader-facing demo closeout. The current demo
closeout is the HRD v3 `70/30` boltons slice listed above, with COD-lite only as
a bakeoff candidate.

## Product Direction

Agent Tuning is the nearer product direction: Barcarolle can provide benchmark
releases, feedback labels, cost summaries, and before/after tuning reports.

Agent Tuning Phase 1 feasibility completed on 2026-06-14 with state
`ready_for_phase2_with_restrictions`. Real-Agent artifact injection is proven
for Codex/Kilo request paths, with Kilo `AGENTS.md` and Kilo project rules the
most reliable first surfaces. Behavior-change evidence is limited to
artifact-driven request-context differences; action-level command/test behavior
must pass a minimal preflight before any GEPA/Phoenix optimization. Recommended
Phase 2 route: GEPA standalone as a text-artifact proposer for one Kilo
`AGENTS.md` appendix, with Phoenix as backup proposer and a DSPy-native coding
workflow as fallback if real-Agent action behavior cannot be proven. Canonical
closeout:
`experiments/agent_tuning_demo/reports/phase1_feasibility_closeout_zh.md` and
`experiments/agent_tuning_demo/results/phase1_feasibility_closeout.json`.

Agent Tuning Phase 2 completed on 2026-06-15 with terminal state
`phase2_success_no_holdout_regression`. The hard action-level Kilo
`AGENTS.md` preflight passed with no paid calls: Variant B executed the public
pytest command and wrote the marker while Variant A did not. GEPA standalone
`optimize_anything` was used with a custom local proposer and no reflection LM
to produce one Kilo `AGENTS.md` appendix. Fresh Kilo GPT low-cost before/after
validation was non-regressing but did not improve: Selection-dev baseline/tuned
both `1/4`, Holdout baseline/tuned both `5/6`, paired net wins `0` on both
splits, 20 paid cells total, estimated cost `$1.3267749`. This supports
deployable-artifact injection, feedback export, hash freeze, and held-out
before/after validation mechanics, not tuned improvement, statistical
significance, predictive validity, cross-repo generalization, model
fine-tuning, or full opaque-Agent tuning. Canonical closeout:
`experiments/agent_tuning_demo/reports/phase2_closeout_zh.md` and
`experiments/agent_tuning_demo/results/phase2_closeout.json`.

Agent Tuning Phase 2b completed on 2026-06-15 with terminal state
`phase2b_dev_negative`. Phase 2a was relabeled as a no-improvement pilot, and
the no-paid audit found one usable `mahmoud/boltons` Kilo low-cost
time-ordered window, not enough for a multi-window rolling-origin claim. A real
LLM-driven GEPA-shaped proposer used two `LLM_BASE_URL`/`LLM_API_KEY` calls
including one reflection iteration and produced two train-only Kilo
`AGENTS.md` appendices. Fresh dev evaluation spent 18 Agent cells, estimated
`$0.8974602`, and both candidates were non-regressing but unchanged:
baseline/tuned `4/6 -> 4/6`, paired net wins `0`, invalid cells `0/0`. The
preregistered positive-dev gate failed, so future validation was skipped with
zero future cells and future task IDs remained unrevealed. Supported claims are
limited to Phase 2a reframe, single-window task-supply readiness, and real
LLM-driven train-only artifact proposal; no tuned improvement or rolling-origin
claim is supported. Canonical closeout:
`experiments/agent_tuning_demo/reports/phase2b_closeout_zh.md` and
`experiments/agent_tuning_demo/results/phase2b_closeout.json`.

The boltons task-generator capacity audit completed on 2026-06-15 with
terminal state `return_to_target_repo_selection`. Conservative boltons supply
is 35 current release tasks plus 22 incremental no-paid dry-run release tasks,
for 57 projected release tasks; an optimistic 64-task count depends on source
context repair. Count-only partitioning can make two windows, but current
Kilo-low-cost headroom evidence still supports only one Phase 2b-style window.
Do not run another boltons paid tuning pilot for a stronger rolling-origin
claim. Next no-paid target-prep fallback is `python-attrs/attrs`; keep `click`
as a supply-ready backup if attrs packaging or verifier repair stalls.
Canonical audit:
`experiments/agent_tuning_demo/reports/boltons_capacity_final_recommendation_zh.md`
and
`experiments/agent_tuning_demo/results/boltons_capacity_final_recommendation.json`.

The target repository selection gate completed on 2026-06-15 with terminal
state `target_repo_selected_no_paid`. It screened 13 new Python repositories
plus the required baselines and deep-probed 6 new repositories where feasible.
No new repository beat the practical attrs/click/boltons baseline after
setup/replay risk was included: packaging and marshmallow had strong source
supply but failed prior/fresh no-paid replay samples, urllib3 had strong source
supply but failed visible smoke and replay samples, and pytest was rejected as
too infrastructure-heavy for this gate. Primary fallback remains
`python-attrs/attrs`; `pallets/click` is the backup. Do not start paid tuning
or baseline discovery from this gate; next work is attrs target-profile,
packaging, verifier pinning, bounded no-paid certification, and split/freeze
rehearsal. Canonical gate:
`experiments/agent_tuning_demo/reports/target_repo_selection_gate_zh.md` and
`experiments/agent_tuning_demo/results/target_repo_selection_gate.json`.

The large-repo target selection gate completed on 2026-06-15 with terminal
state `large_repo_target_selected_no_paid`. It screened 15 new repositories
across large/heavy and medium-large fast-evaluation tracks, deep-probed 10 new
repositories where feasible, and ran no paid Agent, LLM, or tuner calls. The
recommended no-paid target-prep repository is `sphinx`; backup is `mypy`, but
`mypy` is speed-unproven and must not be treated as paid-ready. `sphinx` has
fast current targeted shards and projected multi-window capacity, but its
one-sample historical changed-test replay did not pass under the generic
dependency profile, so the next step is target profile, package map,
version-aware verifier pinning, and a 20-30 task no-paid certification wave.
Do not start paid baseline discovery or tuning from this gate alone. Canonical
gate:
`experiments/agent_tuning_demo/reports/large_repo_target_selection_gate_zh.md`
and
`experiments/agent_tuning_demo/results/large_repo_target_selection_gate.json`.

Agent License remains a possible downstream product, but it is not the current
research proof or active architecture. Historical license/admission material is
archived under `archive/2026-05-agent-license-reset/`.
