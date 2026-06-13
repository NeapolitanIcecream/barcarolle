# Agent Selection Demo Alignment Note 2026-06-13

Status: alignment note after the first demo, post-demo diagnostics, and the
blocked top-2 repeatability check.

Primary inputs:

- `docs/research/agent-selection-demo-execution-proposal-2026-06-12.md`
- `experiments/agent_selection_demo/reports/target_repo_coding_agent_selection_demo_report_zh.md`
- `experiments/agent_selection_demo/reports/post_demo_diagnostics_zh.md`
- `experiments/agent_selection_demo/reports/top2_repeatability_check_zh.md`

## One-sentence Correction

The first demo should be interpreted as an end-to-end target-repo Agent
selection demo that exposed recommendation instability; the blocked top-2
repeat should not reframe the whole demo as a Kilo adapter repair project.

## Original Demo Goal

The 2026-06-12 execution proposal did not ask the demo to prove predictive
validity, a global Agent ranking, or that one harness/model family is generally
better.

It asked for a near-term demo showing that Barcarolle can:

- compare complete Coding Agents on one target repository;
- run the same repo-specific tasks across real Agent configurations;
- capture each Agent's final diff;
- replay that diff in a clean verifier workspace;
- report verified solve rate, cost, latency, and failure reasons;
- lock a selection-task recommendation and check it on fresh holdout tasks.

The core question was:

> For this target repository, which complete Coding Agent setup gives the best
> quality/cost/latency tradeoff, and does that recommendation still look
> reasonable on fresh holdout tasks?

## What Was Completed

The first `mahmoud/boltons` run completed the main demo shape:

- 4 candidate Agents;
- 20 selection tasks;
- 10 holdout tasks;
- 80 selection cells and 40 holdout cells;
- clean verifier replay for scored diffs;
- a locked selection recommendation before holdout;
- a Chinese report summarizing quality, cost, latency, and failure categories.

Selection recommended `Codex + GPT mainline`. Holdout contradicted that
recommendation: `Kilo + GPT mainline` led holdout `9/10` to Codex `5/10`.

This is already a useful demo result. It supports the story that a target-repo
Agent selection system can run end to end and that fresh holdout checks can
surface an unstable selection recommendation.

## What The Follow-up Added

The post-demo diagnostics made the contradiction more understandable:

- selection quality was tied between Codex GPT mainline and Kilo GPT mainline
  at `15/20`;
- the original Codex recommendation depended on a fragile cost tie-breaker;
- Kilo cost/usage coverage was not comparable with Codex because Kilo usage was
  not observed in the sanitized ledgers;
- holdout was much more concentrated in later `canonical_history` tasks;
- existing artifacts could not distinguish stochasticity from stable
  harness/repository behavior differences.

The top-2 repeatability check then tried to answer whether the Kilo holdout lead
was stable. It did not produce a valid ranking result:

- Codex repeated the frozen holdout tasks and moved from `5/10` to `7/10`;
- Kilo hit two consecutive 900-second adapter/CLI timeouts;
- the run stopped at 12/20 cells because the 95% scoreable-cell gate was no
  longer reachable.

This follow-up shows that the Kilo repeat path needs engineering repair before
making stronger claims about Kilo's holdout lead. It does not invalidate the
first demo's main result.

## Where The Story Started To Drift

The useful follow-up question was:

> Was the selection/holdout contradiction stable, noisy, or partly caused by
> cost/task-split artifacts?

After the repeatability blocker, the story risked becoming:

> We cannot move forward until Kilo adapter timeout and usage normalization are
> fully fixed.

That framing is too narrow. Kilo repair is necessary if the next claim is "Kilo
is a stable nearest competitor or winner on this holdout set." It is not
necessary to preserve the original demo claim that the system can run complete
Agents and expose an unstable recommendation.

## Correct Current Interpretation

Use this as the current demo-level claim:

> On `mahmoud/boltons`, Barcarolle ran a complete Agent-selection workflow:
> four real Agent configurations solved the same repo-specific tasks, their
> diffs were replayed in clean verifier workspaces, and the fresh holdout check
> contradicted the selection recommendation. This demonstrates why target-repo
> Agent selection needs holdout checks, uncertainty reporting, and robust
> adapter gates before it becomes a production decision tool.

Do not say:

- Kilo is better than Codex;
- Codex is better than Kilo;
- the Kilo holdout lead is stable;
- the top-2 repeat disproved the original demo;
- predictive validity has been shown;
- this is a cross-repository or model-family ranking.

## Implications For Next Work

Choose the next action by the claim being strengthened.

| Claim to strengthen | Best next action | Notes |
| --- | --- | --- |
| "The demo story is presentation-ready" | Revise the demo-facing report/slides around the completed first run plus diagnostics | Do not center Kilo timeout. Present it as an appendix-level caveat. |
| "Kilo's holdout lead may be real" | Fix Kilo adapter timeout and usage normalization, then rerun the frozen top-2 holdout repeat | This is a narrow engineering/repeatability track. |
| "The system generalizes beyond one repo" | Run a second-repo gate before any paid cells | Do not start a full second-repo matrix until task certification and adapter smoke gates are clean. |
| "The system can support future predictive-validity work" | Prepare a rolling-origin design note with baselines, metrics, windows, and budget | This remains design work before more paid validation. |
| "The system is useful for Agent tuning" | Turn verified failures and pass/fail deltas into a feedback-report prototype | This can reuse the first demo results without waiting for Kilo repair. |

## Recommended Near-term Order

1. Produce a cleaned-up demo interpretation package from the completed first
   run and diagnostics.
2. Decide whether the next paid work is for ranking confidence, generality, or
   product-story evidence.
3. If ranking confidence is the priority, repair Kilo timeout/usage first and
   rerun the same frozen top-2 holdout repeat.
4. If generality is the priority, perform a no-paid second-repo gate before
   planning another matrix run.
5. Keep rolling-origin validation as the path toward predictive validity, not
   as an immediate blocker for the demo.

## Handoff Rule

Future agents should not treat the blocked top-2 repeatability check as the
state of the whole project. It is one failed follow-up attempt on a specific
question. The canonical demo result remains the completed first `boltons`
Agent-selection run plus the post-demo diagnostics.
