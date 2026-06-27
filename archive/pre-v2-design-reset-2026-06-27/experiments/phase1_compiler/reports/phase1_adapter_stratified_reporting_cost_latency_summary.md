# Adapter-Stratified Cost And Latency Summary

Status: `complete`.

What happened: cost and latency are now reported per adapter from committed cost summaries and the committed usage ledger.
Why it matters: score, cost, and latency move together in the paid pilot, but they are different claims and must not be collapsed into one headline.
Action suggested next: future paid reports should state the cost basis and provider-bill availability beside each adapter result.

## Cost Basis

- Cost basis: token-estimated from observed usage.
- Actual provider-billed exact cost available: `false`.
- `actual_provider_billed_cost_usd`: `null`.
- Usage observed rate: `1.0` for both adapters.

Token-estimated cost is not a provider bill. Because `actual_provider_billed_cost_usd` is null in the committed cost summaries, this report cannot claim an exact provider-billed total.

## Adapter Cost

| Adapter | Cells | Observed token-estimated USD | Conservative token-estimated USD | Cost/cell | Provider-billed status |
| --- | ---: | ---: | ---: | ---: | --- |
| `codex_workspace` | 60 | 32.22309 | 30.000000 | 0.53705 | unavailable |
| `kilo_workspace` | 60 | 19.044243 | 30.000000 | 0.31740 | unavailable |
| Total | 120 | 51.267333 | 60.000000 |  | unavailable |

What happened: Codex has the higher observed token-estimated cost, by USD 13.178847 total and about USD 0.21965 per cell.
Why it matters: adapter differences affect budget planning, not just pass rate.
Action suggested next: future runbooks should forecast and report cost by adapter before showing any pooled cost.

## Adapter Latency

| Adapter | Latency observations | Median latency |
| --- | ---: | ---: |
| `codex_workspace` | 60 | 115.059s |
| `kilo_workspace` | 60 | 52.5495s |

What happened: Kilo's median latency was lower by 62.5095 seconds.
Why it matters: the adapter can change turnaround time enough to affect paid-run planning and throughput.
Action suggested next: keep median latency adapter-stratified in future cross-harness reports.

## Hygiene

- Raw usage artifact references were not copied into this report.
- Raw prompts, completions, solver workspaces, verifier workspaces, target diffs, and raw logs were not committed.
- The completed paid pilot decision remains unchanged.
