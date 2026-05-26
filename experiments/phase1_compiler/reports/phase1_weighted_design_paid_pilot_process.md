# Weighted Design Paid Pilot Process

Run ID: `phase1_weighted_design_paid_pilot_20260526`.
Updated: `2026-05-26T03:36:22Z`.

## Work Queue

- Step 0: `completed` - Preflight And Approval Record; commit target `Record weighted design paid pilot preflight`.
- Step 1: `completed` - Build Frozen Pilot Matrix And Package Inspection; commit target `Build weighted design paid pilot matrix`.
- Step 2: `completed` - Tooling, Endpoint, And Entry Gate; commit target `Record weighted design paid pilot entry gate`.
- Step 3: `completed` - Run Paid Smoke Batch; commit target `Run weighted design paid pilot smoke batch`.
- Step 4: `completed` - Run Remaining Attrs Paid Cells; commit target `Run weighted design paid pilot attrs cells`.
- Step 5: `completed` - Run Remaining Boltons Paid Cells; commit target `Run weighted design paid pilot boltons cells`.
- Step 6: `pending` - Integrity Audit And Score Import; commit target `Audit weighted design paid pilot score tables`.
- Step 7: `pending` - Compute Weighted And Baseline Metrics; commit target `Compute weighted design paid pilot metrics`.
- Step 8: `pending` - Baseline Comparison And Error Analysis; commit target `Compare weighted design paid pilot baselines`.
- Step 9: `pending` - Final Decision And Closeout; commit target `Record weighted design paid pilot decision`.

## Boundary Records

- Paid pilot approval is granted by the runbook.
- Paid endpoint rule is `LLM_BASE_URL` plus `LLM_API_KEY`; values are never recorded.
- Historical reference remains historical-only and is not rerun.
- Follow-up runbook written by worker: `false`.

## Smoke Batch

- Tasks: `attrs__hist__009`, `boltons__hist__006`.
- Cells completed: `4`.
- Scoreable cells: `4`.
- Terminal statuses: `verified_pass=2`, `verified_fail=2`.
- Observed-or-conservative cost: `USD 2.0`.
- Stop-gate result: `continue_to_remaining_attrs`.

## Attrs Batch

- Attrs cells completed including smoke: `20`.
- Total cells completed after attrs batch: `22`.
- Scoreable cells after attrs batch: `22`.
- Terminal statuses after attrs batch: `verified_pass=12`, `verified_fail=10`.
- Observed-or-conservative cost after attrs batch: `USD 11.0`.
- Stop-gate result: `continue_to_boltons`.

## Boltons Batch

- Total cells completed after boltons batch: `44`.
- Scoreable cells after boltons batch: `44`.
- Terminal statuses after boltons batch: `verified_pass=29`, `verified_fail=15`.
- Observed-or-conservative cost after boltons batch: `USD 22.0`.
- Cost hard cap: `USD 25.0`.
- Stop-gate result: `paid_cells_complete`.
