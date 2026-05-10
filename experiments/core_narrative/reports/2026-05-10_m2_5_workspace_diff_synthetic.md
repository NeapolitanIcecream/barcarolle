# M2.5 Workspace-Diff-v1 Scoreability Recovery

Date: 2026-05-10

## Scope

This artifact evaluates `workspace-diff-v1`: the ACUT edits an isolated prepared task workspace, the runner extracts `git diff --binary`, and the clean-room verifier consumes that diff through the existing replay path.

Mode: `synthetic`. Fixed denominator: `6` cells (`2 ACUT x 3 RWork` for the live path unless blocked).

## Results

- Status counts: `{'failed': 6}`
- Failure owners: `{'candidate_patch': 6}`
- Failure classes: `{'none': 6}`
- Attemptability score: `1.0`
- Invalid submission rate: `0.0`
- Clean replay disagreements: `0`
- Gate status: `passed`

## Claim Boundary

This is measurement recovery evidence only. It does not claim task-solving improvement, capability uplift, ranking reversal, G_score predictivity, license, admission, or authorization.

## Reproduction

Exact delivered command:

```bash
PYTHONPATH=experiments/core_narrative/tools \
  python3 \
  experiments/core_narrative/tools/m2_5_workspace_diff_runner.py \
  --mode \
  synthetic \
  --run-prefix \
  m2_5_workspace_diff_synthetic_20260510 \
  --output \
  experiments/core_narrative/results/m2_5_workspace_diff_synthetic_20260510.json \
  --report \
  experiments/core_narrative/reports/2026-05-10_m2_5_workspace_diff_synthetic.md \
  --force
```
