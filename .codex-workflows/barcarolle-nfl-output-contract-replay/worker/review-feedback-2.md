# Review To Worker

status: issues_found

## Summary
Continuation 3 is consistent on the main expansion contract: Gate 1 and budget controls stayed strict, the Click 004-008 run used only the four core ACUTs with `anchored-search-replace-json-v3`, exactly 20 primary live cells were run, the artifact and ledger counts match, the reported 11 passed / 5 verifier failures / 4 model-output invalid submissions / 0 infra failures / 0 timeouts is consistent across the batch, normalized summary, expansion summary, decision artifact, and report, and the cost totals reconcile to 20 new provider-usage ledger records, USD 2.487485 new provider-usage cost, and USD 4.879213 cumulative ledger/provider-usage estimate with no invoice-backed actual cost.

One report/process wording issue remains: the verifier-replay failures are correctly counted as 5, but they did not all exit with verifier code `1`.

## Findings
1. The report and worker handoff overstate the verifier exit code for all verifier-replay failures. The report says the 5 verifier replay failures had "Verifier exit code `1`" (`experiments/core_narrative/reports/2026-05-08_codex_nfl_output_contract_replay_repair_report.md:139`), and the worker process repeats that all 5 "exited verifier `1`" (`.codex-workflows/barcarolle-nfl-output-contract-replay/worker/process.md:83`). The normalized artifacts show the failure classification count is right, but the exact exit-code detail is not: three Click 005 failed replays have `verification.exit_code: 4` (`cheap-generic-swe`, `frontier-generic-swe`, and `frontier-click-specialist`), while the two Click 008 failed replays exit `1`.

## Required Closure
Update the report and worker handoff wording to avoid the incorrect all-`1` exit-code claim. Suggested replacement: "5 verifier-replay failures had nonzero verifier exits after a patch was generated and clean-replayed; exit-code distribution was 3 with code `4` and 2 with code `1`."
