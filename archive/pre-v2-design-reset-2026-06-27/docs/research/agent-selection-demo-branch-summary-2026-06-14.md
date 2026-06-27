# Agent Selection Demo Branch Summary 2026-06-14

Branch: `codex/agent-selection-demo-2026-06-12`

This branch builds and closes the first target-repository Agent-selection demo
for Barcarolle. The demo asks a narrow question:

> Given one target repository and several complete Coding Agents, can
> Barcarolle compile a Selection benchmark that recommends an Agent, then check
> whether later Holdout tasks validate that recommendation?

The answer on the frozen `mahmoud/boltons` demo slice is yes at demo scale.
This is not a proof of full predictive validity.

## What Changed

- Added an end-to-end Agent-selection demo under
  `experiments/agent_selection_demo/`.
- Added sanitized score tables, verifier summaries, cost ledgers, selector
  outputs, and Chinese reports for the demo runs.
- Added workspace-adapter and endpoint-proxy hardening in
  `experiments/phase0_headroom/tools/`, including Kilo timeout cleanup and
  usage parsing improvements.
- Added selector tooling for task selection, random baselines, rolling-origin
  retrospective checks, algorithm bakeoff, and user-facing recommendation
  policy.
- Updated `PROCESS.md` with the current demo state and claim boundary.
- Added runbooks and prompts that document the execution path from initial AB
  demo proposal through selector correction, algorithm bakeoff, and final
  HRD-centered closeout.

## Final Demo State

The reader-facing mainline selector is `HRD v3 70/30`, `k=10`. HRD is not the
final research algorithm. It is the current simple, auditable selector that is
good enough to support the demo story.

COD-lite remains in the algorithm bakeoff table as an ordinary candidate. It is
not the final demo mainline and should not be presented as a co-mainline.

Final HRD Selection result:

| Agent | Selection pass |
| --- | ---: |
| Kilo + GPT mainline | `9/10` |
| Codex + GPT mainline | `7/10` |
| Kilo + Claude Sonnet | `7/10` |
| Kilo + GPT low-cost | `7/10` |

Final Holdout result:

| Agent | Holdout pass |
| --- | ---: |
| Kilo + GPT mainline | `9/10` |
| Kilo + Claude Sonnet | `8/10` |
| Kilo + GPT low-cost | `6/10` |
| Codex + GPT mainline | `5/10` |

Doubled-timeout top-2 repeat:

| Agent | Repeat pass |
| --- | ---: |
| Kilo + GPT mainline | `9/10` |
| Codex + GPT mainline | `6/10` |

The final reporting policy outputs:

- an Agent ranking;
- a selection recommendation;
- an evidence table;
- `top_tier` when Agents are close;
- `insufficient_data` only when scoreable/common-valid data is insufficient,
  outcome rows are missing, or infrastructure failures block comparison.

Paired wins/losses and bootstrap-style metrics are evidence fields, not default
recommendation vetoes.

## Supported Claim

On the frozen `mahmoud/boltons` demo slice, Barcarolle can produce an auditable
Agent ranking and Selection recommendation. HRD v3 70/30 recommends
`Kilo + GPT mainline`, and later Holdout plus doubled-timeout top-2 repeat show
the same Agent ahead.

This supports the demo story that a user can use Barcarolle Selection evidence
to choose an Agent and then check the choice against later tasks.

## Unsupported Claims

Do not claim:

- full predictive validity has been proven;
- HRD strictly beats all strong random baselines;
- the result generalizes across repositories or model families;
- `Kilo + GPT mainline` is globally best;
- COD-lite is the final demo algorithm;
- Agent tuning improvement has been demonstrated.

## Canonical Artifacts

- Final demo report:
  `experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md`
- Final demo closeout:
  `experiments/agent_selection_demo/reports/selector_final_demo_closeout_zh.md`
- Final HRD eval:
  `experiments/agent_selection_demo/reports/selector_final_eval_zh.md`
  and `experiments/agent_selection_demo/results/selector_final_eval.json`
- Algorithm bakeoff:
  `experiments/agent_selection_demo/reports/selector_algorithm_bakeoff_eval_zh.md`
  and `experiments/agent_selection_demo/results/selector_algorithm_bakeoff_eval.json`
- Corrected-validation context:
  `experiments/agent_selection_demo/reports/selector_corrected_validation_closeout_zh.md`
  and
  `experiments/agent_selection_demo/results/selector_corrected_validation_closeout.json`
- Demo proposal:
  `docs/research/agent-selection-demo-execution-proposal-2026-06-12.md`

## Verification

The branch was validated with:

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_retrospective_predictive_signal.py -q
git diff --check
```

At final closeout, these reported:

- `43 passed` for agent-selection demo tests;
- `6 passed` for Phase 1 retrospective signal tests;
- clean whitespace check;
- no prohibited tracked demo artifacts in the scoped hygiene scan.

## Next Work

- Run the same frozen protocol on another target repository.
- Add more independent rolling-origin or future slices.
- Improve selector features only with leakage-safe historical signals.
- Add real observed billing/latency fields before using cost as a production
  tiebreaker.
- Feed failure labels and unstable task clusters into an Agent-tuning backlog,
  while keeping tuning improvement as a future claim.
