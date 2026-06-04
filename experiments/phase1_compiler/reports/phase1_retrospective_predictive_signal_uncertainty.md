# Retrospective Predictive-Signal Uncertainty

What happened: assigned qualitative uncertainty labels instead of formal intervals.

Why it matters: the analysis is retrospective and has sparse true rolling-origin support.

Action suggested next: use the result to choose action categories, not to claim predictive validity.

Labels:
- overall: `directional_only`
- sample_size: `too_sparse_for_formal_predictive_validity`
- claim_strength: `traction_evidence_only`

Driver checks:
```json
{
  "best_baseline": "temporal_recent_baseline",
  "best_candidate": "coverage_constrained_unweighted",
  "delta_MAE_by_adapter": {
    "codex_workspace": 0.0253,
    "kilo_workspace": -0.037
  },
  "delta_MAE_by_repo": {
    "attrs": -0.0871,
    "boltons": 0.0139,
    "click": 0.0556
  }
}
```
