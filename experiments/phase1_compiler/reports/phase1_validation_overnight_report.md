# Phase 1 Overnight Validation Report

Generated: `2026-05-21T16:27:00Z`.

Decision: `phase1_operational_validation_pilot_complete`.

Predictive validity established: `false`.

## New Evidence

The overnight run produced a healthy Humanize operational validation pilot:

| Prefix | Cells | Scoreable | Terminal statuses | Policy violations | Usage observed |
| --- | ---: | ---: | --- | ---: | ---: |
| `phase1_validation_humanize_holdout_smoke` | 4 | 4 | `verified_fail=4` | 0 | 1.0 |
| `phase1_validation_humanize_holdout` | 12 | 12 | `verified_pass=7`, `verified_fail=5` | 0 | 1.0 |
| `phase1_validation_humanize_holdout_stability` | 16 | 16 | `verified_pass=5`, `verified_fail=11` | 0 | 1.0 |

The Humanize cells are `internal_unseen_acut_holdout_not_future_holdout`: they
were certified before this overnight run, but had not previously been solved by
Codex or Kilo.

## Source Provenance

Source provenance was audited but not hardened.

- Toolz: `6/6` certified tasks have issue/PR-derived usable context.
- Humanize: `12/12` certified tasks remain commit-message fallback only.
- GitHub commit-to-PR lookup was attempted for the 12 Humanize certified target
  commits and found `0` PR metadata matches.

Humanize remains suitable for an operational pilot, not validation-grade claims.

## Stability

The Humanize stability repeat ran and passed scoreability and policy gates. It
is repeat reliability evidence, not independent validation evidence.

## Third Repo

A local-only `itsdangerous` third-repo certification pilot ran. It produced:

- certified tasks: `1`;
- near-certified tasks: `10`;
- release status: `diagnostic_only`;
- B/W split: `B_real=0`, `W_real=1`.

No paid third-repo ACUT cells were run. The stop reason is
`phase1_third_repo_certification_blocker`: certification stayed below the pilot
threshold and did not have balanced B/W coverage.

## Cost

Cumulative workspace cost reconciliation after the overnight run:

- calls: `109`;
- usage observed rate: `0.945`;
- observed-or-conservative estimated spend: `31.026435` USD;
- provider-billed cost: unavailable.

## Remaining Work

Before validation-grade claims:

- harden Humanize source provenance beyond commit-message fallback;
- repair or replace the third-repo certification path;
- pre-register a true future-holdout validation design;
- keep `predictive_validity_established`, `future_holdout_predictive_validity`,
  `pure_harness_effect`, and `production_benchmark_ranking` out of scope until
  that design runs.

Recommended next runbook: Phase 1 future-holdout validation design with
Humanize source-adapter hardening and third-repo certification repair.
