# Agent Selection Boltons Small Expansion Runbook 2026-06-15

Status: execution runbook for the next Codex agent session.

This runbook is for the presentation-oriented Agent Selection Demo. It
intentionally stays on `mahmoud/boltons`; do not fall back to `attrs`, `click`,
or a larger repository in this run. Earlier target-selection and Agent Tuning
capacity reports remain useful context, but this run optimizes for a compact,
credible boltons demo, not for a stronger multi-repository proof.

## Goal

Expand the existing boltons Agent-selection demo just enough that the main PPT
story no longer rests on `10`-task pass-rate steps.

The final package should show:

- a time-ordered boltons Selection set and later-check/Holdout set;
- more paid cells entering the displayed Selection/Holdout matrices;
- the same four candidate Agents as the current demo;
- a final recommendation that can be checked against later tasks;
- strict chronological rolling-origin-style diagnostics computed from the
  expanded boltons data;
- regenerated PPT-ready charts in `~/playground/barcarolle_ppt_assets`.

This is still a demo. Do not claim full predictive validity, global Agent
ranking, cross-repository generalization, or selector optimality.

## Starting State

Current boltons demo data:

- Selection: `20` tasks x `4` Agents = `80` paid cells.
- Holdout: `10` tasks x `4` Agents = `40` paid cells.
- Doubled-timeout top-2 repeat: `10` holdout tasks x `2` Agents = `20` paid
  cells.
- Current Selection task times: 2015-04-19 through 2022-01-16.
- Current Holdout task times: 2022-12-07 through 2023-10-31.
- Current unused/smoke later tasks exist in 2024-2026, but are not part of the
  four-Agent displayed matrix.

Useful context from Agent Tuning capacity work:

- Current boltons release/selectable tasks: `35`.
- Conservative projected boltons release tasks after bounded no-paid expansion:
  `57`.
- Optimistic small-repair projection: `64`.
- Dominant bottleneck: non-leaky source context and certification, not raw
  candidate availability.

## Candidate Agents

Keep the existing four-Agent matrix:

| ID | Display name | Harness/runtime | Model |
| --- | --- | --- | --- |
| A | Codex + GPT mainline | Codex CLI workspace adapter | `gpt-5.4` |
| B | Kilo + GPT mainline | Kilo workspace adapter | `gpt-5.4` |
| C | Kilo + GPT low-cost | Kilo workspace adapter | `gpt-5.4-mini` |
| D | Kilo + Claude | Kilo workspace adapter | `claude-sonnet-4-6` |

Use `LLM_BASE_URL` and `LLM_API_KEY` for all paid calls. Do not use fallback
provider variables or local subscription auth.

Use the active post-blocker timeout policy unless the repository config has a
newer explicit value:

- adapter timeout: `1800s`;
- cleanup grace: `60s`;
- outer workspace timeout: `1860s`;
- verifier timeout: `360s`;
- endpoint/proxy upstream timeout: `3600s`.

## Target Scale

Preferred final scale:

- Selection: `28-30` tasks x `4` Agents.
- Later check / Holdout: `20-24` tasks x `4` Agents.

Minimum acceptable scale:

- Selection: `24` tasks x `4` Agents.
- Later check / Holdout: `18` tasks x `4` Agents.

If boltons cannot reach the preferred scale without risky source-context repair,
stop at the minimum acceptable scale and report why. Do not switch repositories.

## Paid-Cell Budget

Use existing committed scoreable rows whenever they match the frozen task,
Agent, endpoint, and policy requirements. New paid cells are for missing cells,
newly promoted tasks, and consistency repairs.

Expected new paid cells:

- `40-56` cells for new Selection tasks;
- `40-56` cells for new later-check tasks;
- optional `0-24` cells to repair timeout-policy consistency or non-scoreable
  gaps on the displayed later-check matrix.

Hard cap: `140` new paid cells. If reaching the cap before the minimum
acceptable scale, write a blocker closeout with the exact missing cells.

## Package 1: Preflight And Inventory

Acceptance:

- Verify `LLM_BASE_URL` and `LLM_API_KEY`; source `~/.zshrc` once if missing.
- Recheck `/models` and confirm all four models are available through the
  OpenAI-compatible upstream interface.
- Run scoped adapter/workspace tests used by the current demo.
- Audit current boltons task inventory and classify tasks as:
  - already displayed Selection;
  - already displayed Holdout;
  - doubled-timeout repeated top-2;
  - unused/smoke but release-ready;
  - newly promotable after no-paid certification;
  - rejected, with reason.
- Write `experiments/agent_selection_demo/reports/boltons_small_expansion_inventory_zh.md`.

## Package 2: No-Paid Task Expansion Gate

Use existing task generator/certification assets and the Agent Tuning boltons
capacity audit outputs. Do not read raw transcripts or workspaces.

Acceptance:

- Materialize a candidate list sufficient for the target scale, ordered by
  `task_time`.
- Preserve strict time order: Selection tasks must be earlier than later-check
  tasks, except for explicitly labeled internal rolling-origin diagnostics.
- Prefer tasks with:
  - non-leaky issue/PR context;
  - changed-test oracle extraction;
  - local certification pass;
  - clear module coverage;
  - no known flakiness or environment risk.
- Freeze a task manifest before any new paid cells:
  `experiments/agent_selection_demo/results/boltons_small_expansion_task_manifest.json`.
- Write `experiments/agent_selection_demo/reports/boltons_small_expansion_task_gate_zh.md`.

## Package 3: Expanded Paid Matrix

Run only the frozen missing cells needed for the expanded boltons matrix.

Acceptance:

- Use the four-Agent matrix and active timeout policy.
- Capture scoreable status, verified pass/fail, failure category, latency, usage
  source, cost observation kind, estimated cost, and billed cost if available.
- Do not commit raw prompts, raw completions, transcripts, solver workspaces, or
  verifier workspaces.
- Stop early only for endpoint/model unavailability, secret isolation failure,
  or hard paid-cell cap. Infrastructure problems should be diagnosed and fixed
  where feasible rather than used as a reason to abandon the run.
- Produce:
  - `experiments/agent_selection_demo/results/boltons_small_expansion_score_table.csv`;
  - `experiments/agent_selection_demo/results/boltons_small_expansion_cost_ledger.jsonl`;
  - `experiments/agent_selection_demo/reports/boltons_small_expansion_paid_matrix_zh.md`.

## Package 4: Final Selection/Holdout Analysis

Combine existing and new score rows into a single current demo view.

Acceptance:

- Build an expanded final matrix with one row per `(task_id, Agent)`.
- Use the doubled-timeout result for a task/Agent only when it supersedes an
  older score row under the active policy; record the replacement rule.
- Report Selection and later-check pass rates, pass-rate gaps, ranking,
  scoreable coverage, cost, latency, and failure labels.
- The displayed main chart should use the merged active matrix, not a separate
  top-2 repeat chart.
- If the Selection winner and later-check winner disagree, do not hide it:
  explain the decision-quality implication and whether the demo still supports
  the story.
- Produce:
  - `experiments/agent_selection_demo/results/boltons_small_expansion_final_matrix.csv`;
  - `experiments/agent_selection_demo/results/boltons_small_expansion_summary.json`;
  - `experiments/agent_selection_demo/reports/boltons_small_expansion_final_analysis_zh.md`.

## Package 5: Strict Chronological Rolling-Origin Diagnostics

Compute rolling-origin-style diagnostics from the expanded boltons data only.
This is a historical pseudo-future check, not proof of real future performance.

Acceptance:

- Use actual `task_time`, not heldout split labels, to form origins.
- Prefer at least `3` chronological origins.
- Each origin should have enough scoreable cells to be interpretable. Preferred
  minimum: at least `8` Selection tasks and `8` future tasks after scoreable
  filtering; if not possible, use the largest defensible windows and mark them
  sparse.
- For each origin, compute:
  - Selection pass rate by Agent;
  - future pass rate by Agent;
  - MAE by Agent and overall;
  - top-rank agreement;
  - recommendation regret;
  - pass-rate gap direction.
- Compare against same-budget random task samples where feasible. The comparison
  can be directional; do not require statistical significance for this demo.
- Produce:
  - `experiments/agent_selection_demo/results/boltons_strict_rolling_origin_slices.csv`;
  - `experiments/agent_selection_demo/results/boltons_strict_rolling_origin_summary.json`;
  - `experiments/agent_selection_demo/reports/boltons_strict_rolling_origin_zh.md`.

## Package 6: Regenerate PPT Charts

Update the chart script in:

```text
/Users/chenmohan/playground/barcarolle_ppt_assets/make_agent_selection_demo_charts.py
```

Keep the current clean PPT style: white background, black and deep blue,
minimal text, weak grid, no decorative gradients, no separate top-2 repeat
figure.

Required charts:

- `agent_selection_selection_vs_holdout.png`: expanded Selection vs later-check
  matrix, legend in the lower-right outside the plotting area, not overlapping
  title or labels.
- `boltons_strict_rolling_origin_timeline.png`: x-axis uses real time or
  concrete time ranges, y-axis is pass rate, showing Selection/Future pass
  rates and per-origin MAE/gap.
- `rolling_origin_mae_comparison.png`: recomputed from strict chronological
  boltons diagnostics.
- `rolling_origin_decision_metrics.png`: recomputed top-rank agreement, mean
  regret, and max regret.
- Optional: `rolling_origin_catastrophic_miss.png` only if it helps the slide;
  omit it if it distracts from the main story.

Acceptance:

- Render the PNGs.
- Visually inspect them with image viewing tools.
- Fix text overlap, title/legend collisions, label crowding, and misleading
  wording.
- Do not put process language such as "not proof" or runbook labels directly
  into the figure unless the chart would otherwise overclaim. Put caveats in
  slide speaker notes or report prose.

## Package 7: Final Report And Handoff

Acceptance:

- Write a compact Chinese final report:
  `experiments/agent_selection_demo/reports/boltons_small_expansion_demo_report_zh.md`.
- Include:
  - what changed from the previous demo;
  - final task/cell counts;
  - final Selection and later-check matrix;
  - strict rolling-origin diagnostic summary;
  - cost and usage caveats;
  - what the PPT can claim;
  - what it must not claim.
- Update `PROCESS.md` with a short entry and links to canonical outputs.
- Run scoped tests and hygiene checks:
  - demo tests;
  - relevant adapter/workspace tests if paid calls or adapter behavior changed;
  - `git diff --check`;
  - tracked artifact scan for raw/workspace/transcript/secret paths.
- Make focused commits after each package or tightly related group.

## Final Claim Boundary

Allowed if the data supports it:

> On boltons, the expanded target-repo benchmark can compare complete Agents on
> a larger time-ordered Selection/Holdout matrix, make an auditable
> recommendation, and evaluate how that recommendation behaves on later tasks.
> Strict chronological historical checks provide directional evidence that this
> is a measurable and optimizable predictive-evaluation problem.

Not allowed:

- predictive validity is proven;
- the selected Agent is globally best;
- boltons results generalize to all repositories;
- the selector is statistically superior or optimal unless the data truly shows
  that under preregistered criteria;
- raw cost estimates are actual billing when usage coverage is incomplete.
