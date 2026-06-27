# Agent Selection Selector Validation Correction Runbook 2026-06-14

Status: mandatory correction runbook for validating the Agent-selection selector
without reusing the same Holdout as both development signal and proof.

The previous selector-evolution pass produced useful code and a plausible
illustrative slice:

- RSQ, HRD-style selectors, strong random baselines, and a shared decision
  wrapper now exist.
- `hrd_70_30`, `k=10` selects a subset where Selection recommends
  `Kilo + GPT mainline`, and the existing boltons Holdout/repeat also favor
  Kilo.

But that result must be treated as hypothesis-generating until corrected. The
selector variant and final slice were chosen after seeing the same boltons
Selection/Holdout evidence used for the claim. The HRD "disagreement" arm used
metadata fallback rather than a leakage-safe historical Agent-disagreement
signal. The resulting story is useful for diagnosis, not sufficient validation.

This runbook's job is to produce a clean final answer:

1. either validate a frozen decision-aware selector on an independent
   rolling-origin/fresh final slice; or
2. report a hard negative result explaining why the current task supply or
   outcome grid cannot yet support the Agent-selection story.

Do not stop after downgrading the previous result. Use it as development signal,
freeze a corrected selector/protocol, then run the strongest feasible final
validation inside the boundary below.

## Target Demo Story

Preferred final story:

> Before seeing final later/Holdout outcomes, Barcarolle freezes a selector and
> decision rule. The frozen Selection benchmark recommends an Agent. On
> independent later/Holdout tasks, the same Agent is best or has low regret. The
> result beats strong same-budget random baselines on MAE and decision quality.

Minimum acceptable story:

> The corrected validation shows that the current selector should abstain or
> request more evidence. This is reported honestly with the exact bottleneck and
> the smallest next experiment needed.

## Non-goals

- Do not claim full predictive validity.
- Do not claim global Agent/model ranking.
- Do not present the existing `hrd_70_30` boltons subset as independently
  validated.
- Do not retune on final later/Holdout outcomes.
- Do not run a broad model matrix.
- Do not ask for manual intervention; choose the conservative fallback inside
  this runbook.

## Required Reading

Read these before making changes:

- `AGENTS.md`
- `PROCESS.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0614-0.md` if present
- `docs/research/agent-selection-selector-evolution-runbook-2026-06-14.md` if present
- `experiments/agent_selection_demo/reports/selector_evolution_closeout_zh.md`
- `experiments/agent_selection_demo/reports/selector_agent_selection_demo_story_zh.md`
- `experiments/agent_selection_demo/results/selector_final_eval.json`
- `experiments/agent_selection_demo/results/selector_final_preregistration.json`
- `experiments/agent_selection_demo/results/selector_hrd_eval.json`
- `experiments/agent_selection_demo/results/selector_decision_eval.json`
- `experiments/agent_selection_demo/tools/agent_selection_demo.py`
- `experiments/agent_selection_demo/results/selection_score_table.csv`
- `experiments/agent_selection_demo/results/holdout_score_table.csv`
- `experiments/agent_selection_demo/results/doubled_timeout_top2_repeat_score_table.csv`
- `experiments/agent_selection_demo/results/rolling_origin_eval_slices.csv`
- relevant phase1 task-supply and future-holdout artifacts if the no-paid
  final validation needs additional repositories or tasks.

## Interpretation Boundary

The previous selector-evolution output must be reclassified as:

```text
hypothesis_generating_selector_development_result
```

It may be used for:

- designing candidate selectors;
- choosing a small, fixed set of selector families to evaluate;
- motivating HRD-style representative/discriminative selection;
- explaining why the original full Selection set was not enough.

It must not be used as:

- final proof that HRD generalizes;
- final proof that `Kilo + GPT mainline` is generally best;
- evidence from an independent Holdout after selector design;
- a reason to tune thresholds or task IDs on the final validation slice.

## Terminal States

### Preferred Terminal State: Independent Decision Validation

All must be true:

1. A corrected selector protocol is frozen before final outcome join or paid
   final cells.
2. The final validation slice is independent of the previous boltons
   selector-development slice:
   - either a true rolling-origin final block not used for selector/threshold
     selection;
   - or a fresh task slice with no current-Agent outcomes used before
     preregistration;
   - or a second target repo final slice after a no-paid readiness gate.
3. The selector has a fixed config chosen using development evidence only.
4. The final Selection benchmark produces `recommend`, not only abstention.
5. Later/Holdout validates the recommendation:
   - recommended Agent is later top; or
   - recommendation regret is `<= 5pp`.
6. The recommended Agent's top-pair direction agrees from Selection to
   later/Holdout.
7. Final MAE beats the strongest same-budget random baseline by at least
   `0.02` absolute or `10%` relative.
8. Decision quality beats same-budget random on regret or false recommendation
   rate.
9. The final report clearly says this is demo-level evidence, not full
   predictive-validity proof.

### Accepted Negative Terminal State

Allowed only if the preferred terminal state cannot be achieved after the
packages below are genuinely attempted.

The negative closeout must state which blocker applies:

- `insufficient_independent_task_supply`;
- `missing_final_outcome_grid`;
- `selector_does_not_recommend`;
- `selector_recommends_wrong_agent`;
- `strong_random_not_beaten`;
- `adapter_or_paid_run_reliability_blocker`;
- `oracle_or_task_quality_blocker`.

It must also specify the smallest next experiment that would unblock the story.

## Paid-call Boundary

Default: no new paid cells until no-paid independent validation is exhausted.

Paid calls are approved only for one frozen final validation after the
preregistration artifact is written.

Hard cap: `90` new paid cells.

Priority order:

1. Top-2 final Selection grid:
   `selected tasks x {Codex + GPT mainline, Kilo + GPT mainline}`.
2. Top-2 final later/Holdout grid for the same frozen slice.
3. One top-2 same-budget strong-random control Selection grid if needed for
   decision-baseline comparison.
4. Optional expansion to the existing four demo Agents only if the top-2 story
   already succeeds and enough budget remains.

Recommended minimum paid design if no independent no-paid validation exists:

- `k_selection = 10`;
- `k_later = 10`;
- top-2 Agents only;
- total primary cells: `40`;
- optional random-control Selection cells: `20`;
- smoke/gate cells as needed before scoreable cells.

All paid calls must use `LLM_BASE_URL` and `LLM_API_KEY`. If either is missing,
source `~/.zshrc` and check again. If the endpoint cannot be proven, stop paid
execution and complete a negative closeout rather than using fallback auth.

## Blocker Standard

Do not ask the user what to do. If a choice is needed, choose the conservative
option that preserves validity:

- use top-2 instead of all four Agents;
- reduce `k` before changing the claim;
- choose fresh task supply before reusing seen Holdout as proof;
- report abstention before forcing a recommendation;
- report a negative result before retuning on final outcomes.

Blocked means:

- exact blocking artifact/command/code path is identified;
- a local fix was attempted if the blocker is in repo code;
- focused tests were added or updated where feasible;
- independent packages continued where possible;
- paid boundary, artifact hygiene, or endpoint rule prevents further progress.

## Package 1: Correction Audit And Claim Downgrade

Produce:

```text
experiments/agent_selection_demo/reports/selector_validation_correction_audit_zh.md
experiments/agent_selection_demo/results/selector_validation_correction_audit.json
```

Required content:

- why the previous `hrd_70_30` result is hypothesis-generating;
- whether the HRD disagreement arm used leakage-safe Agent-disagreement data or
  metadata fallback;
- whether final variant choice used the same slice later used for validation;
- which artifacts must be reinterpreted;
- what remains reusable: code, datasets, baselines, decision wrapper;
- what cannot be claimed from the previous result.

Update reader-facing selector story artifacts if needed so they do not overclaim
independent validation. Do not delete useful results; relabel them.

Acceptance:

- no paid calls;
- `PROCESS.md` is updated or scheduled for final update so future sessions do
  not treat the previous selector result as independently validated.

Commit after this package.

## Package 2: Independent Validation Inventory

Find all feasible independent validation sources.

Produce:

```text
experiments/agent_selection_demo/results/selector_independent_validation_inventory.json
experiments/agent_selection_demo/reports/selector_independent_validation_inventory_zh.md
```

Required inventory:

- existing no-paid rolling-origin/final blocks from committed sanitized
  outcomes;
- existing task pools with no current-Agent outcomes that can support fresh
  paid final validation;
- boltons unused or not-yet-scored certified tasks;
- attrs or another repo readiness after no-paid gate, if boltons is exhausted;
- for each candidate source:
  - number of eligible selection tasks;
  - number of eligible later/Holdout tasks;
  - available Agent outcome grid;
  - whether outcomes were already seen during previous selector development;
  - whether source is valid for final proof or only for development.

Acceptance:

- explicitly identifies at least one final-validation path or gives a negative
  reason why none exists;
- no paid calls.

Commit after this package.

## Package 3: Corrected Selector Protocol

Freeze the corrected evaluation design before final outcome join or paid cells.

Produce:

```text
experiments/agent_selection_demo/results/selector_corrected_protocol.json
experiments/agent_selection_demo/reports/selector_corrected_protocol_zh.md
```

Protocol requirements:

- previous boltons `hrd_70_30` slice is development evidence only;
- final validation source is marked as one of:
  - `no_paid_independent_rolling_origin`;
  - `fresh_paid_boltons_slice`;
  - `fresh_paid_second_repo_slice`;
  - `negative_no_valid_final_source`;
- selector families considered are fixed before final evaluation;
- final selector config is chosen from development evidence only;
- final selected task IDs are written before final outcome join when no-paid, or
  before paid calls when paid;
- final later/Holdout task IDs are written before final outcome join or paid
  calls;
- random baselines, seeds, invalid-cell policy, decision thresholds, and success
  criteria are fixed.

Recommended selector configs to freeze:

- `rsq_recency_stratified_quota` as strong metadata baseline;
- `hrd_v2_70_30` as primary;
- optional `hrd_v2_60_40` only as a development comparison, not as a
  post-final fallback.

HRD v2 requirements:

- if leakage-safe historical Agent disagreement exists, use it only from
  development origins;
- if not, call the arm `metadata_informativeness`, not `Agent disagreement`;
- include quality/risk gates and module/source caps;
- do not compute task score from final Selection or final later/Holdout Agent
  outcomes.

Acceptance:

- tests or a machine-readable audit show that final outcomes are not used in
  selector scoring;
- if only metadata proxy is used, the report says so plainly.

Commit after this package.

## Package 4: No-paid Independent Replay

Run the corrected selector on every valid no-paid independent final block.

Produce:

```text
experiments/agent_selection_demo/results/selector_no_paid_independent_eval.json
experiments/agent_selection_demo/reports/selector_no_paid_independent_eval_zh.md
```

Required metrics:

- Selection pass rates;
- later/Holdout pass rates;
- recommendation/abstain/need-more-evidence state;
- top-pair direction agreement;
- top-1 agreement when meaningful;
- recommendation regret;
- MAE;
- strong random baselines:
  - uniform random;
  - quality-filtered random;
  - stratified random;
- random percentile or beats/ties share;
- whether final source was independent of previous selector development.

Acceptance:

- if preferred terminal state is achieved no-paid, do not run paid cells;
- if no-paid fails because of missing outcome grid, proceed to Package 5;
- if no-paid fails because the selector recommends wrongly or does not beat
  baselines, do not retune on that final block; complete negative result unless
  another independent final source remains.

Commit after this package.

## Package 5: Fresh Final Slice And Optional Paid Cells

Run this package only if Package 4 cannot achieve preferred terminal state and
the inventory found a valid fresh final source.

Produce preregistration before any paid cells:

```text
experiments/agent_selection_demo/results/selector_fresh_final_preregistration.json
experiments/agent_selection_demo/reports/selector_fresh_final_preregistration_zh.md
```

Preregistration must include:

- final source/repo;
- target task pool;
- selected task IDs;
- later/Holdout task IDs;
- Agent set;
- selector config and code hash or commit hash;
- decision thresholds;
- random baselines and seed list;
- invalid-cell policy;
- paid-cell cap for this package;
- stop conditions.

Then run the minimum paid grid required by the preregistration.

Required outputs after execution:

```text
experiments/agent_selection_demo/results/selector_fresh_final_eval.json
experiments/agent_selection_demo/reports/selector_fresh_final_eval_zh.md
```

Execution rules:

- run adapter smoke/gates before scoreable paid cells;
- use `1800s` Agent timeout, `60s` cleanup grace, `1860s` outer timeout,
  `360s` verifier timeout, and endpoint/proxy timeout above Agent timeout unless
  corrected config says otherwise;
- do not change selected task IDs after seeing any final score;
- do not add a new selector variant after seeing final scores;
- if paid reliability fails, classify the reliability blocker and continue to
  final closeout.

Acceptance:

- final paid result either reaches preferred terminal state or a clear negative
  terminal state;
- raw prompts/completions/transcripts/workspaces remain ignored;
- sanitized cost/usage coverage is reported.

Commit after this package.

## Package 6: Final Story, Closeout, And Process Update

Produce:

```text
experiments/agent_selection_demo/reports/selector_corrected_validation_story_zh.md
experiments/agent_selection_demo/reports/selector_corrected_validation_closeout_zh.md
experiments/agent_selection_demo/results/selector_corrected_validation_closeout.json
```

Final story requirements:

- plainly explain why the previous selector result was not enough;
- state whether the corrected validation used no-paid independent replay or
  fresh paid final cells;
- list final selected tasks and later/Holdout tasks;
- show Selection pass rates and later/Holdout pass rates;
- state the decision output;
- report MAE and decision quality versus strong random baselines;
- report paid cells and estimated cost;
- state exactly what can and cannot be claimed.

Update `PROCESS.md`:

- previous `hrd_70_30` result should be marked as development/hypothesis
  evidence unless Package 4 or 5 independently validates it;
- link corrected validation artifacts;
- record active next step only if the result is negative or incomplete.

Closeout checklist:

1. Was the previous selector result relabeled correctly?
2. What final validation source was used?
3. Was the selector frozen before final outcomes?
4. Which selector config was evaluated?
5. What did Selection recommend?
6. What did later/Holdout show?
7. What was recommendation regret?
8. What was MAE versus the strongest random baseline?
9. Were decision metrics better than random?
10. How many new paid cells and estimated dollars were used?
11. Which tests passed?
12. What exact claim is now supported?
13. What remains unproved?

Commit after this package.

## Required Validation

Run at minimum:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q
```

```text
PYTHONPATH=experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_retrospective_predictive_signal.py -q
```

If adapter/workspace code changes or paid cells are run:

```text
PYTHONPATH=experiments/phase0_headroom/tools uv run --project experiments/phase1_compiler pytest experiments/phase0_headroom/tools/test_cli_workspace_adapters.py experiments/phase0_headroom/tools/test_workspace_acut_run.py experiments/phase0_headroom/tools/test_workspace_usage_import.py -q
```

Always run:

```text
git diff --check
git ls-files experiments/agent_selection_demo | rg '(__pycache__|\.pyc$|raw|transcript|workspace|\.DS_Store|\.pytest_cache|\.venv)'
```

If `rg` exits `1` because there are no prohibited tracked artifacts, record that
as pass.

