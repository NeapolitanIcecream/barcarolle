# Statement-Hardened Next Action Decision

Primary decision: `design_new_predictive_threshold_before_more_paid_validation`.
Confidence: `medium_high`.
Predictive validity established: `False`.

## Research Questions

- RQ1: Yes for scoreable evidence: statement hardening produced clean scoreable 32-cell evidence with no policy violations. It did not by itself produce predictive validity.
- RQ2: No. B_eval did not predict H_future well enough under the current split; observed gaps were 0.25 for attrs and 0.375 for boltons.
- RQ3: The H_future drop is best read as a combination of future-holdout/task-family hardness and small-N uncertainty, with residual statement-source risk in boltons and low adapter variance.
- RQ4: Future preregistrations should use a stratified absolute B_eval-H_future gap rule, primarily <=0.15 with minimum scoreable cells and a confidence/precision rule.
- RQ5: Next, design the quantitative threshold and locally resplit/reweight for time and task family. Enlarge local supply before any paid replication; do not report a production benchmark ranking.

## Main Evidence

- 32 planned cells completed and scoreable
- 21 verified_pass and 11 verified_fail
- policy violations, timeouts, harness errors, and invalid outputs were all zero
- attrs gap 0.25 and boltons gap 0.375 both show H_future lower than B_eval
- adapter disagreement was 1 of 16 tasks

## Main Uncertainty

- no preregistered quantitative predictive-validity threshold
- 4 tasks per repo/split leaves wide intervals
- boltons H_future confounds time window, task family, and statement source

## Recommended Next Action

Do not run more paid validation until a quantitative predictive-validity threshold and a better matched local design are preregistered.

No follow-up runbook was written by this worker.
