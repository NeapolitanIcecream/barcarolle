# Statement-Hardened Calibration Options

Before any more paid validation, preregister a quantitative threshold and rebuild the release with time-stratified and difficulty-balanced B_eval matching.

All ranked options are benchmark-compiler changes; none reimplements file search, editing, retry, or reasoning internals of the ACUT harness.

## Ranked Options

| Rank | Option | Expected benefit | Cost | Overfit risk | Requires paid validation |
| --- | --- | --- | --- | --- | --- |
| 1 | time_stratified_b_eval_matching | Reduces the observed B_eval/H_future time-window mismatch before paid validation. | local analysis plus possible remanifesting | medium | False |
| 2 | difficulty_balanced_b_eval_selection | Keeps B_eval from being easier than H_future by balancing implementation/test surface and module family. | local scoring and selection work | medium | False |
| 3 | expanded_holdout_with_minimum_scoreable_cells | Improves uncertainty enough for a preregistered threshold to mean something. | more local supply and later paid validation if approved | low | True |
| 4 | module_task_family_weighting | Addresses boltons H_future family shift and attrs next_gen/setattr concentration. | local weighting design and preregistration | high | False |
| 5 | adapter_disagreement_weighting | Could downweight unstable adapter-specific cells. | low local analysis | medium | False |
| 6 | statement_quality_confidence_weighting | Separates residual statement risk from task difficulty. | review rubric and possibly another local review pass | medium | False |
| 7 | negative_evidence_reporting_without_further_paid_runs | Honest paper/prototype result: clean scoreable evidence but no predictive-validity claim. | report writing | low | False |
| 8 | per_repo_calibration_using_local_historical_dry_run_metadata | May improve expected future pass-rate estimates. | local calibration design | high | False |
