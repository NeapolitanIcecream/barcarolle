# Multi-SWE Budget-Ten Capacity Diagnostic

Date: 2026-07-28

## Decision

Budget ten has substantial representational capacity for the opened Multi-SWE
36-configuration pass-rate estimand. The current failure is pre-Origin
identification, not an inability of ten historical Tasks to represent the
future response vector.

This is a hindsight support result. It is not a predictive algorithm, does not
nominate a Selector, and does not show that usable pre-Origin signals exist.

## Why this diagnostic was run

ALG-012 was better than most equal-budget random subsets but nearly tied full
history at H5 and worsened H10. That left two explanations:

1. ten Tasks cannot carry enough response information; or
2. suitable ten-Task subsets exist, but the observable semantic rule cannot
   identify them before future outcomes exist.

The diagnostic plan was committed after the ALG-012 result but before the
hindsight computation. Its digest is
`47f1c375f6d16c72c8c0b7f5f1f2dd3f5c6dc3b4e9392d99a52cfede63de4b13`.

## Exact method

For each frozen H5 and H10 Origin:

1. group eligible historical Tasks by their exact 36-bit public outcome
   vector;
2. create one bounded integer count for each observed response pattern;
3. require the counts to select exactly ten Tasks;
4. minimize mean absolute error between the selected and actual future
   36-configuration pass rates.

This is a mixed-integer linear program, not a greedy search. SciPy 1.16.3
called HiGHS with presolve enabled, no time limit, and zero requested relative
MIP gap. All 328 solves returned certified optimal status and zero reported
MIP gap. Recomputed subset losses agreed with solver objectives within
`3.93e-15`. A complete second run was byte-identical.

Grouping identical response vectors reduces computation without changing the
objective. H5 histories contained 3–81 response patterns with median 27; H10
contained 3–80 with median 27.

## Results

Negative difference favors Selection.

| Horizon | Full-history MAE | Exact budget-ten MAE | Difference | Relative loss reduction | Favorable repositories | Deep difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| H5 | `0.06735` | `0.03471` | `-0.03264` | 48.46% | 13/13 | `-0.03423` |
| H10 | `0.05281` | `0.02719` | `-0.02562` | 48.51% | 11/11 | `-0.02459` |

Every frozen deep repository is also favorable: 8/8 at H5 and 5/5 at H10.
All predeclared capacity requirements pass.

The sampling landscape separates the mechanisms:

| Route | H5 difference | H10 difference |
| --- | ---: | ---: |
| Mean equal-budget random | `+0.00182` | `+0.00506` |
| ALG-012 semantic rule | `-0.00027` | `+0.00241` |
| Unchanged ALG-007 | `-0.00225` | `+0.00216` |
| Exact hindsight support | `-0.03264` | `-0.02562` |

Random calibration shows ALG-012 uses some Task Pool structure. The exact
hindsight result shows much more useful structure is representable. The gap
between `-0.00027` and `-0.03264`, not the ten-Task budget, is the central
algorithmic problem.

## Claim boundary

The optimizer directly reads future Agent outcomes. Its memberships are
therefore leakage by design and must never be used as a runtime Selector,
training label, nomination, or confirmation result.

The result is conditional on:

- the opened 36-configuration Multi-SWE panel;
- projected GitHub PR times;
- the current H5/H10 Origin construction;
- pass-rate MAE as the estimand.

It does not remove possible Generator or source-frame bias and does not prove
that future natural work is predictable. It only rejects the explanation that
budget ten lacks response-representation capacity on this panel.

## Research consequence

Do not tune the budget from this result. A new candidate must explain how it
predicts useful response structure using only information available before the
target Origin. The next credible route should:

1. keep each runtime Selection within one repository;
2. learn only from source-time-eligible Origins in other research
   repositories;
3. hold out the complete target repository;
4. use observable task-side features or pre-Origin Agent evidence, never the
   hindsight memberships;
5. freeze the mechanism and gate before target-outcome replay.

A direct partial-pooling model remains possible, but repository identity alone
is not a mechanism: it must predict a response-relevant quantity and beat
macro averaging under held-out-repository evaluation. Do not add a generic
trainer or model registry before such a concrete candidate exists.

## Adversarial audit

A read-only audit confirmed the MILP and aggregation, and identified two
evidence-validation gaps: an incorrect coverage predicate and a summary that
was not mechanically rebuilt from raw results. Both were fixed. The final
validator now recomputes source dimensions, cohorts, memberships, solver
status and gap, objective checks, repository aggregates, the capacity
decision, nomination, and resource boundaries from two raw artifacts. Final
recheck found no actionable issue.

## Evidence identity and resources

The ignored full artifact digest is
`7ccd3153720ce12c98c1781df2fbf654b65ceacad93eb8916c1843baf86cdb4f`.
The committed compact summary digest is
`cf6bee9578773068440c4ba73514488f7d8adccfb9157714a4077a2291f5d7d6`.

The diagnostic made zero paid API calls, zero embedding API calls, and opened
zero sealed SWE-bench holdout Agents.
