# Phase 0 Budget Plan

The hard LLM API cap is USD 200. The soft stop is USD 160, and USD 180 is the
stop-and-ask threshold. This run uses `uv`-managed deterministic repository
mining and local test execution only; no paid model call is approved by default.

Before any paid batch, the worker must read
`experiments/phase0_headroom/results/cost_ledger.jsonl`, compute cumulative
estimated spend, write the projected batch cost into the process log, and verify
that the cumulative projected spend remains below the applicable threshold.

For this execution, cumulative estimated spend remains USD 0.00 because no
external model call was made.
