# Phase 1 Boltons Paid ACUT Smoke Decision

Primary decision: `boltons_paid_smoke_complete_ready_for_phase1_validation_design`.

Paid ACUT calls were made through the configured endpoint environment
`LLM_BASE_URL` and `LLM_API_KEY`. No direct paid LLM calls were made outside the
ACUT harnesses.

## Adapter Readiness

Both workspace adapters passed preflight before paid task solving:

- `codex_workspace`: `ready`, endpoint proof `codex_eligible`, fallback auth disabled.
- `kilo_workspace`: `ready`, endpoint proof `kilo_eligible`, fallback auth disabled.

## Paid Cells

Smoke tasks:

- `boltons__hist__007`
- `boltons__hist__017`
- `boltons__hist__024`
- `boltons__hist__026`

Extension tasks:

- `boltons__hist__019`
- `boltons__hist__020`
- `boltons__hist__031`

Results:

| Prefix | Cells | Scoreable | Terminal statuses |
| --- | ---: | ---: | --- |
| `phase1_validation_boltons_paid_smoke` | 8 | 7 | `verified_pass=7`, `invalid_output=1` |
| `phase1_validation_boltons_paid_extension` | 6 | 6 | `verified_pass=4`, `verified_fail=2` |

Combined result: `13` scoreable cells out of `14`.

Policy violations: `0`.

## Cost Boundary

- Usage observed rate: `0.9431`.
- Observed-or-conservative estimated cost: `USD 37.6472432`.
- Incremental observed-or-conservative cost since preflight: `USD 6.6208082`.
- Stop cap: `USD 60.00`.

## Claim Boundary

This run supports operational smoke claims only: the Boltons tasks and both
workspace ACUT harnesses produced scoreable, policy-clean paid cells under the
same endpoint/model setup. It does not establish predictive validity, future
holdout validity, production benchmark ranking, or a pure harness effect.

Next runbook: `write_phase1_validation_design_and_future_holdout_runbook`.
