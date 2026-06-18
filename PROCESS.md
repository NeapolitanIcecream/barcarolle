# Barcarolle Process Notes

This file records repository-wide process decisions that future coding-agent
sessions should know before planning or executing Barcarolle work.

Last updated: 2026-06-17.

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

## Experiment Scope Discipline

Keep experiments on the main demo story. Prefer the simplest protocol that can
answer the current decision question. Exploring new algorithms, mechanisms, or
diagnostics is allowed when the opportunity is concrete and the result can
change the next decision.

The thing to avoid is predesigning an elaborate scenario, overbuilding
infrastructure around it, and then letting that path become the project by
inertia. Do not add window policies, plots, selector/tuner variants, repository
probes, or verifier machinery only because they are technically interesting or
make a figure prettier.

Label exploratory figures and diagnostics as such. Do not let exploratory
details become new claim requirements without a separate decision.

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

Boltons small expansion demo update on 2026-06-15:

- Expanded only `mahmoud/boltons` to a strict `task_time`-ordered presentation
  matrix with `30` Selection tasks and `20` later-check tasks.
- Paid expansion added `88/140` allowed fresh cells, reusing `112` committed
  cells for a complete `200`-cell matrix. Selection recommends Kilo + GPT
  mainline (`20/30`, `0.666667`), while later-check top is Kilo + Claude
  Sonnet (`17/19`, `0.894737`); Selection-regret on later-check is `0.094737`.
- Strict rolling-origin diagnostics use real `task_time` only, not ordinary
  split labels: `4` origins, MAE mean `0.213418`, top-rank agreement `0.5`,
  mean/max regret `0.033742` / `0.094737`. Treat this as directional
  historical pseudo-future evidence, not predictive-validity proof.
- Canonical outputs:
  `experiments/agent_selection_demo/reports/boltons_small_expansion_demo_report_zh.md`,
  `experiments/agent_selection_demo/results/boltons_small_expansion_summary.json`,
  `experiments/agent_selection_demo/results/boltons_strict_rolling_origin_summary.json`,
  `experiments/agent_selection_demo/results/boltons_small_expansion_task_manifest.json`.

Selector-aware correction on 2026-06-16 supersedes the fixed-window chart as
the live presentation evidence:

- No new paid Agent cells were run. The analysis reuses the committed
  `50 x 4` expanded boltons matrix and counts timeout, harness error,
  invalid output, and no meaningful change as failed user-visible attempts.
- At each origin, selectors choose only from historical task metadata before
  outcomes are joined. The old fixed-window rolling-origin outputs remain
  drift diagnostics only; do not present
  `boltons_strict_rolling_origin_summary.json` or the old PPT timeline as
  selector-selected benchmark evidence.
- All implemented selectors were evaluated with no diagnostic-only exclusions.
  The final presentation selector remains HRD v3 `70/30`, `k=10`, under the
  selector-aware choice rule.
- Latest-origin user story (`origin_40`): HRD chooses 10 tasks from the first
  40 historical tasks. Selection recommends Kilo + Claude Sonnet at `9/10`;
  later/future has Kilo + Claude Sonnet and Kilo + GPT mainline tied at `9/10`,
  so recommendation regret is `0`.
- Selector-aware primary rolling-origin metrics for HRD v3 `70/30`, `k=10`:
  MAE mean `0.194444`, top-rank agreement `1.0`, top-tier agreement `1.0`,
  mean/max regret `0.0` / `0.0`. Latest-origin MAE is `0.225`.
- Latest-origin same-budget strongest random baseline is
  `source_recency_stratified_random` with MAE mean `0.292125`; HRD improves
  MAE by `0.067125` and regret by `0.0059`.
- Canonical selector-aware outputs:
  `experiments/agent_selection_demo/results/boltons_selector_aware_winner.json`,
  `experiments/agent_selection_demo/reports/boltons_selector_aware_winner_zh.md`,
  `experiments/agent_selection_demo/results/boltons_selector_aware_eval.json`,
  `experiments/agent_selection_demo/results/boltons_selector_aware_random_baselines.json`,
  `experiments/agent_selection_demo/reports/boltons_selector_aware_reanalysis_closeout_zh.md`.

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

Task Generator evolution update on 2026-06-17 supersedes the target-repair
loop's `task_generation_method_needs_revision` state for the current Sphinx and
mypy Agent Tuning candidate repositories:

- Terminal state: `task_generator_evolved_two_repo_ready`.
- No paid Agent cells, paid tuner/proposer calls, paid baseline discovery, or
  paid LLM calls were run.
- `sphinx` and `mypy` each have `100` exact certified tasks and `3` corrected
  rolling-origin windows with `20` selected-from-history slots and `20` future
  holdout tasks per window.
- Final generator path:
  `experiments/agent_tuning_demo/tools/task_generator_evolution.py`.
- Canonical closeout:
  `experiments/agent_tuning_demo/results/task_generator_evolution_closeout.json`
  and
  `experiments/agent_tuning_demo/reports/task_generator_evolution_closeout_zh.md`.
- Next paid work, if pursued, must be a separate preregistered baseline or
  tuning run that freezes selectors, Agents, score-join rules, invalid-cell
  policy, seeds, cost caps, and the no-future-leakage window protocol before
  any paid cells are run.

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

Agent Tuning Demo shared-module extraction completed on 2026-06-15 with terminal
state `demo_shared_module_extraction_complete_no_paid`. The active Phase 2 and
Phase 2b Tuning tools no longer import `agent_selection_demo.py` and no longer
read live Selection Demo config/result files. Selection-derived inputs are now
frozen in `experiments/agent_tuning_demo/config/selection_input_snapshot.json`
with provenance in
`experiments/agent_tuning_demo/results/selection_input_snapshot_manifest.json`;
later Selection result changes do not affect current Tuning behavior unless a
future run deliberately refreshes that snapshot. Shared neutral helper code now
lives under `experiments/demo_common/`. Selection Demo adoption of those helpers
is deferred to avoid conflicting with parallel Selection work. No paid calls,
new Selection experiments, or new Tuning experiments were run. Canonical
closeout:
`experiments/agent_tuning_demo/reports/demo_shared_module_extraction_zh.md` and
`experiments/agent_tuning_demo/results/demo_shared_module_extraction.json`.

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

The Sphinx target-prep gate completed on 2026-06-17 with historical terminal
state `sphinx_ready_for_paid_baseline_preregistration`, but its projected
rolling-origin policy and old cell accounting are superseded by the
protocol/manifest freeze below. No paid Agent cells, paid LLM calls, paid
tuner/proposer calls, baseline discovery, or before/after tuning experiments
were run. The gate added a Sphinx target profile, repaired narrow
version-aware verifier pinning, built a 180-row bounded inventory, and ran a
24-row no-paid certification wave: `16/24` replay/certification passes,
conversion `0.6667`, verifier median `7.78s`, p95 `24.333s`, max `42.758s`.
Canonical target-prep closeout:
`experiments/agent_tuning_demo/reports/sphinx_target_prep_closeout_zh.md` and
`experiments/agent_tuning_demo/results/sphinx_target_prep_closeout.json`.

The next Sphinx rolling-origin protocol must use the benchmark-compiler story
directly: for each origin, all eligible tasks before the origin are the
history pool, the selected benchmark is chosen from that history pool, and the
future holdout is the next time/task window after the origin. Do not use a
three-disjoint-segment interpretation where `selected` is simply the slice
between `train` and `future`; that is a coarse feasibility shorthand, not the
main claim protocol. Future preregistration should name fields like
`history_pool_before_origin`, `selected_benchmark_from_history`,
`future_holdout_after_origin`, and `origin_stride`.

The Sphinx protocol/manifest freeze completed on 2026-06-17 with terminal
state `sphinx_manifest_needs_bounded_repair`. It corrected the protocol in
`sphinx_rolling_origin_protocol_v2`: selected benchmark tasks must be chosen
from the pre-origin history pool, and future holdout IDs/outcomes are not
selector inputs. Focused no-paid certification expansion reused the 24-row
wave and attempted 30 additional candidates; conversion was `0/30`, dominated
by `reference_target_test_failure`, so the stop condition fired. The exact
certified manifest remains `16` tasks, below the minimum `80` tasks needed for
two corrected origins, and the corrected window manifest therefore has `0`
windows. Paid-cell accounting is now unambiguous: a default supported window
would require `(20 selected + 20 future) * 4 = 160` baseline-discovery cells,
but the current repaired-ready count is `0` cells because no window is
supported. Do not write or execute a paid-baseline-preregistration runbook for
Sphinx until a bounded repair plan can produce a minimum exact certified
manifest. Canonical freeze outputs:
`experiments/agent_tuning_demo/reports/sphinx_protocol_manifest_freeze_closeout_zh.md`,
`experiments/agent_tuning_demo/results/sphinx_protocol_manifest_freeze_closeout.json`,
`experiments/agent_tuning_demo/reports/sphinx_certification_expanded_manifest_zh.md`,
`experiments/agent_tuning_demo/results/sphinx_certification_expanded_manifest.json`,
`experiments/agent_tuning_demo/reports/sphinx_rolling_origin_window_manifest_zh.md`,
`experiments/agent_tuning_demo/results/sphinx_rolling_origin_window_manifest.json`,
`experiments/agent_tuning_demo/reports/sphinx_paid_cell_accounting_zh.md`, and
`experiments/agent_tuning_demo/results/sphinx_paid_cell_accounting.json`.

The target repair/selection loop completed on 2026-06-17 with terminal state
`task_generation_method_needs_revision`. No paid Agent cells, paid LLM calls,
tuner calls, baseline discovery, or before/after tuning were run. Sphinx was
rejected after a bounded diagnosis reproduced `0/30` repair expansion
conversion dominated by target changed-test failures. Mypy current smoke passed,
but exact certification after bounded worktree cleanup repair converted only
`7/24` (`0.2917`), below the stop threshold. The priority list and reused broad
repository search expansion found no target ready for corrected rolling-origin
paid preregistration; the next step is Task Generator repair, not another paid
runbook. Canonical closeout:
`experiments/agent_tuning_demo/reports/target_repair_selection_loop_closeout_zh.md`
and
`experiments/agent_tuning_demo/results/target_repair_selection_loop_closeout.json`.

The Agent Tuning Demo autonomous completion run completed on 2026-06-18 with
terminal state `agent_tuning_demo_complete` and result label
`agent_tuning_demo_complete_regressed`. Barcarolle used certified `mypy` tasks
at `origin_40`, froze the corrected rolling-origin shape
`history_pool_before_origin -> selected_benchmark_from_history ->
future_holdout_after_origin`, exported train-only feedback, froze a deployable
repo-local Kilo `AGENTS.md` appendix artifact before revealing future holdout
IDs, and completed before/after future holdout validation. The chosen artifact
was `agent-tuning-demo-mypy-family-triage-loop`
(`sha256:4cc09bb467d9cf638a619017caa59fe01b84c26c1a12f5b4a9a9be08f1149621`).
Future holdout result: baseline `12/20` scoreable pass, tuned `11/19`
scoreable pass with one invalid output, paired net wins `-1`; this does not
support a positive tuning-improvement claim. Total estimated/observed cost was
`$29.39064915` across `76` paid solver Agent cells; no paid tuner/proposer
calls were used, and actual billed provider cost was unavailable from endpoint
export. Canonical outputs:
`experiments/agent_tuning_demo/reports/agent_tuning_demo_final_report_zh.md`,
`experiments/agent_tuning_demo/reports/agent_tuning_demo_final_closeout_zh.md`,
`experiments/agent_tuning_demo/results/agent_tuning_demo_final_closeout.json`,
`experiments/agent_tuning_demo/results/agent_tuning_demo_future_holdout_summary.json`,
and `experiments/agent_tuning_demo/results/agent_tuning_demo_cost_summary.json`.

Agent License remains a possible downstream product, but it is not the current
research proof or active architecture. Historical license/admission material is
archived under `archive/2026-05-agent-license-reset/`.
