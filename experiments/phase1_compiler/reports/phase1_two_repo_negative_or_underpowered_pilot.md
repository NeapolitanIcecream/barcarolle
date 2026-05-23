# Phase 1 Two-Repo Negative Or Underpowered Pilot

Generated: `2026-05-23T11:34:31+00:00`.

## Question

Does the Barcarolle repo-specific benchmark signal predict held-out future target-repo work?

## Design

- Repos: `boltons, attrs`.
- Adapters: `codex_workspace, kilo_workspace`.
- Planned cells: `32`.
- Scoreable cells: `31`.
- H_future scoreable cells: `15`.
- Policy violations: `1`.

## Observed Result

- Boltons B_eval pass rate: `0.875`.
- Boltons H_future pass rate: `0.875`.
- Attrs B_eval pass rate: `0.875`.
- Attrs H_future pass rate: `0.142857`.
- Pooled B_eval to pooled H_future absolute error: `0.341667`.
- Preserved preregistered pooled MAE: `0.479167`.

## Why Predictive Validity Was Not Established

- The preregistered acceptance gate has one confirmed policy violation.
- Attrs H_future collapsed to 1/7 scoreable pass rate despite attrs B_eval at 7/8.
- Baseline errors are too large to support the predictive-validity claim.
- The two-repo sample and 15 scoreable H_future cells leave wide uncertainty intervals.

## What The Attrs H_future Result Means

The attrs H_future collapse is broad across the four planned tasks, not a one-task artifact.

## What The Policy Violation Means

The confirmed policy violation is a benchmark boundary failure for one cell, but the scoreable collapse remains after excluding it.

## Uncertainty And Limits

- Point estimates are negative for predictive validity because B_eval materially overpredicts pooled H_future and attrs H_future.
- The sample is underpowered: only two repos and 15 H_future scoreable cells, with Wilson intervals that remain wide.
- The confirmed policy violation prevents a clean positive validation claim and remains non-scoreable.

## Next Recommended Experiment

Prepare a local-only weighted/stratified compiler analysis runbook before deciding whether third-repo supply or future paid holdout validation is worth the cost.

## Narrow Claim

This Phase 1 pilot did not establish predictive validity. It did demonstrate that Barcarolle can build and execute a clean two-repo validation and can report when evidence is insufficient.
