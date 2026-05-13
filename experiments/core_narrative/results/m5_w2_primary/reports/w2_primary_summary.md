# M5-W2 Primary Summary

Status: `w2_primary_complete_gate_failed`
Generated at: `2026-05-13T08:23:48.320788Z`
Primary score ready: `True`

## Scores

| ACUT | W2 score | Ready | Status counts |
|---|---:|---:|---|
| `cheap-generic-swe` | `5` / `10` | `True` | `{"verified_fail": 5, "verified_pass": 5}` |
| `cheap-click-specialist` | `4` / `10` | `True` | `{"no_diff": 1, "verified_fail": 5, "verified_pass": 4}` |
| `cheap-click-deep-specialist-v2` | `5` / `10` | `True` | `{"verified_fail": 5, "verified_pass": 5}` |
| `frontier-generic-swe` | `4` / `10` | `True` | `{"no_diff": 1, "verified_fail": 5, "verified_pass": 4}` |

## Gates

- Gate status: `failed`
- Next action: `stop_and_write_negative_result`
- Context effect: `{"cheap_generic_score": 5, "deep_score": 5, "expression": "cheap-click-deep-specialist-v2 >= cheap-generic-swe + 2 tasks", "margin_tasks": 0, "passed": false}`
- NFL candidate: `{"deep_score": 5, "expression": "cheap-click-deep-specialist-v2 > frontier-generic-swe", "frontier_generic_score": 4, "margin_tasks": 1, "passed": true}`

## Claim Boundary

This report is W2 primary evidence only. It does not claim R2 or ACUT G results.
