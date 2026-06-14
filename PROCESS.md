# Barcarolle Process Notes

This file records repository-wide process decisions that future coding-agent
sessions should know before planning or executing Barcarolle work.

Last updated: 2026-06-14.

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

- `experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md`
- `experiments/agent_selection_demo/reports/target_repo_coding_agent_selection_demo_report_zh.md`
- `experiments/agent_selection_demo/results/closeout_summary.json`
- `experiments/agent_selection_demo/results/holdout_check.json`

Completed predictive-validity completion pass:

- `docs/research/agent-selection-demo-predictive-validity-completion-runbook-2026-06-13.md`

Completed demo-evidence runbook:

- `docs/research/agent-selection-demo-random-baseline-evidence-runbook-2026-06-14.md`

This runbook completed the simpler demo claim: Barcarolle is a practical
target-repo predictive Agent evaluation facility whose main quantitative
warrant is lower future-pass-rate MAE than same-budget random task sampling,
plus an Agent-selection matrix over real Agents. It doubled Agent-side timeout
policy from 900s to 1800s, with 60s adapter cleanup grace, 1860s outer
workspace timeout, 360s verifier timeout, and 3600s endpoint/proxy upstream
timeout.

Main demo-evidence results:

- random-baseline predictive signal passed the demo gate:
  `coverage_constrained_unweighted` MAE `0.209011` versus same-budget random
  MAE `0.252499`, absolute improvement `0.043488`, relative improvement
  `17.22%`; 1000-seed context shows the candidate beating/tying `93.4%` of
  random samples;
- Kilo + GPT mainline passed the doubled-timeout reliability gate with one
  new smoke/debug paid cell;
- doubled-timeout top-2 repeat completed `20/20` scoreable cells: Codex + GPT
  mainline `6/10`, Kilo + GPT mainline `9/10`;
- total new paid cells for the runbook were `21`, under the `42` cell cap;
- old best-simple-baseline and catastrophic-miss results are limitations, not
  the main demo gate.

Canonical random-baseline demo artifacts:

- `experiments/agent_selection_demo/reports/demo_predictive_facility_story_zh.md`
- `experiments/agent_selection_demo/reports/random_baseline_predictive_signal_zh.md`
- `experiments/agent_selection_demo/results/random_baseline_predictive_signal.json`
- `experiments/agent_selection_demo/reports/demo_agent_selection_evidence_zh.md`
- `experiments/agent_selection_demo/results/demo_agent_selection_evidence.json`
- `experiments/agent_selection_demo/reports/doubled_timeout_policy_zh.md`
- `experiments/agent_selection_demo/reports/doubled_timeout_agent_reliability_gate_zh.md`
- `experiments/agent_selection_demo/results/doubled_timeout_agent_reliability_gate.json`
- `experiments/agent_selection_demo/results/doubled_timeout_top2_repeat_metrics.json`
- `experiments/agent_selection_demo/results/closeout_summary.json`

Predictive-validity demo artifacts:

- `experiments/agent_selection_demo/reports/predictive_validity_state_audit_zh.md`
- `experiments/agent_selection_demo/reports/predictive_validity_protocol_zh.md`
- `experiments/agent_selection_demo/reports/predictive_validity_feasibility_zh.md`
- `experiments/agent_selection_demo/reports/rolling_origin_eval_zh.md`
- `experiments/agent_selection_demo/reports/predictive_validity_retrospective_result_zh.md`
- `experiments/agent_selection_demo/reports/predictive_validity_paid_pilot_decision_zh.md`
- `experiments/agent_selection_demo/reports/predictive_validity_demo_story_zh.md`
- `experiments/agent_selection_demo/results/predictive_validity_evidence_ledger.json`
- `experiments/agent_selection_demo/results/predictive_validity_protocol.json`
- `experiments/agent_selection_demo/results/predictive_validity_window_inventory.json`
- `experiments/agent_selection_demo/results/rolling_origin_eval.json`
- `experiments/agent_selection_demo/results/rolling_origin_eval_slices.csv`
- `experiments/agent_selection_demo/results/predictive_validity_paid_pilot_plan.json`

The random-baseline demo run is now the preferred reader-facing story for this
demo. It supports a practical facility claim and target-repo Agent-selection
evidence, not full predictive-validity proof.

Completed selector-evolution runbook, corrected interpretation:

- `docs/research/agent-selection-selector-evolution-runbook-2026-06-14.md`

The selector-evolution run produced useful assets and a plausible
hypothesis-generating boltons slice, but it should not be treated as independent
selector validation. The final `hrd_70_30`, `k=10` slice recommends
`Kilo + GPT mainline`: Selection Kilo `9/10` versus Codex `7/10`, later Holdout
Kilo `9/10` versus Codex `5/10`, and doubled-timeout top-2 repeat Kilo `9/10`
versus Codex `6/10`. Recommendation regret is `0.0`, and MAE is `0.100000`
versus strong stratified-random k=10 mean MAE `0.151700`.

However, the same boltons Selection/Holdout evidence was used during selector
variant selection and final story construction, and the HRD "disagreement" arm
used metadata fallback rather than leakage-safe historical Agent-disagreement
signals. Treat this result as development evidence and an illustrative slice,
not proof that the selector generalizes.

Canonical selector-evolution artifacts:

- `experiments/agent_selection_demo/reports/selector_agent_selection_demo_story_zh.md`
- `experiments/agent_selection_demo/reports/selector_evolution_closeout_zh.md`
- `experiments/agent_selection_demo/results/selector_evolution_closeout.json`
- `experiments/agent_selection_demo/results/selector_final_eval.json`
- `experiments/agent_selection_demo/results/selector_decision_eval.json`

Claim boundary: this supports an illustrative boltons demo-level
Agent-selection slice and reusable selector/decision tooling, not independent
selector validation, full predictive validity, cross-repository selector
superiority, future unseen validation, or a global Agent/model ranking.

Active selector-validation correction runbook:

- `docs/research/agent-selection-selector-validation-correction-runbook-2026-06-14.md`

This is the next step for the stricter Agent-selection claim. It must relabel
the previous selector result as hypothesis-generating, freeze a corrected
selector protocol, and validate on an independent rolling-origin/fresh final
slice or report a hard negative result.

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

The previous boltons `hrd_70_30` selector story is now explicitly relabeled as
`hypothesis_generating_selector_development_result`. It must not be cited as
independent validation.

The correction runbook froze `hrd_v2_70_30`, `k=6` per repo, before joining
final Phase 1 outcomes, then replayed the no-paid independent
`blocked_split_heldout` block across attrs, boltons, and click. The result is an
accepted negative terminal state: Selection favored `kilo_workspace` (`11/18`
versus Codex `6/18`) and later/Holdout also favored Kilo (`16/30` versus Codex
`7/30`), but the shared decision wrapper returned `need_more_evidence` because
the paired selected comparison had one discordant Kilo loss. Selector MAE was
`0.088889` versus strongest stratified-random MAE mean `0.090146`, below the
required `0.02` absolute or `10%` relative improvement threshold.

Canonical correction artifacts:

- `experiments/agent_selection_demo/results/selector_validation_correction_audit.json`
- `experiments/agent_selection_demo/results/selector_independent_validation_inventory.json`
- `experiments/agent_selection_demo/results/selector_corrected_protocol.json`
- `experiments/agent_selection_demo/results/selector_no_paid_independent_eval.json`
- `experiments/agent_selection_demo/results/selector_corrected_validation_closeout.json`
- `experiments/agent_selection_demo/reports/selector_corrected_validation_story_zh.md`
- `experiments/agent_selection_demo/reports/selector_corrected_validation_closeout_zh.md`

Current claim boundary: the corrected validation supports only that the frozen
selector plus conservative decision wrapper should request more evidence on this
independent pseudo-future block. It does not support the user-facing claim that
Selection recommends an Agent and later/Holdout validates that recommendation.
If that story is still required, the next work is a new development-only
selector/decision design followed by a preregistered independent final slice;
do not spend paid cells merely to retune on the failed final block.

## Product Direction

Agent Tuning is the nearer product direction: Barcarolle can provide benchmark
releases, feedback labels, cost summaries, and before/after tuning reports.

Agent License remains a possible downstream product, but it is not the current
research proof or active architecture. Historical license/admission material is
archived under `archive/2026-05-agent-license-reset/`.
