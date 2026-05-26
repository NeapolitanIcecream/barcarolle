# Weighted Design Paid Pilot Process

Run ID: `phase1_weighted_design_paid_pilot_20260526`.
Updated: `2026-05-26T03:36:22Z`.

## Work Queue

- Step 0: `completed` - Preflight And Approval Record; commit target `Record weighted design paid pilot preflight`.
- Step 1: `pending` - Build Frozen Pilot Matrix And Package Inspection; commit target `Build weighted design paid pilot matrix`.
- Step 2: `pending` - Tooling, Endpoint, And Entry Gate; commit target `Record weighted design paid pilot entry gate`.
- Step 3: `pending` - Run Paid Smoke Batch; commit target `Run weighted design paid pilot smoke batch`.
- Step 4: `pending` - Run Remaining Attrs Paid Cells; commit target `Run weighted design paid pilot attrs cells`.
- Step 5: `pending` - Run Remaining Boltons Paid Cells; commit target `Run weighted design paid pilot boltons cells`.
- Step 6: `pending` - Integrity Audit And Score Import; commit target `Audit weighted design paid pilot score tables`.
- Step 7: `pending` - Compute Weighted And Baseline Metrics; commit target `Compute weighted design paid pilot metrics`.
- Step 8: `pending` - Baseline Comparison And Error Analysis; commit target `Compare weighted design paid pilot baselines`.
- Step 9: `pending` - Final Decision And Closeout; commit target `Record weighted design paid pilot decision`.

## Boundary Records

- Paid pilot approval is granted by the runbook.
- Paid endpoint rule is `LLM_BASE_URL` plus `LLM_API_KEY`; values are never recorded.
- Historical reference remains historical-only and is not rerun.
- Follow-up runbook written by worker: `false`.
