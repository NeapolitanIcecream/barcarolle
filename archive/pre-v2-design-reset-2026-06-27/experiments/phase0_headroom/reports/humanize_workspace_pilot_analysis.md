# humanize Workspace Pilot Analysis

Generated: `2026-05-21T12:24:58+00:00`.

## Selected Repo And Release

- Repo: `humanize`.
- Source: `https://github.com/python-humanize/humanize.git`.
- Local head at selection: `bde649fc2927c022dd2a9eedba2a1ed677b97902`.
- Release: `humanize_phase0_pilot`.
- Release status: `pilot_grade`.
- Benchmark grade flag: `true`.
- Claim scope: `second_repo_operational_pilot_not_predictive_validation`.

## Certification Yield

- Candidate anchors scanned: `325`.
- Selected certification attempts: `16`.
- Certified tasks: `12`.
- Near-certified tasks: `4`.
- Certified split: `6` `B_real`, `6` `W_real`.
- Main rejected gates: `no_op_fail` for `3` tasks and `reference_pass` for `1` task.

Certification required hidden test patches to fail on the base implementation,
pass twice on the target implementation, pass source-context review, stay within
bounded runtime, and avoid committing raw patches or source text.

## Source Context

- Source-context rows: `16`.
- Reviewed non-leaky contexts: `16`.
- Context source kind: `commit_message_fallback` for `16`.

GitHub PR back-links were unavailable for these historical commits, so the pilot
used compact commit-message summaries as public problem context. This is weaker
than linked issue/PR context, but it does not expose source diffs, hidden tests,
or oracle patches.

## Task Shape

Certified modules include `time`, `number`, `filesize`, `i18n`, and package
export surfaces. The bounded workspace matrix used four certified tasks:

- `humanize__hist__005` (`B_real`, `number`).
- `humanize__hist__006` (`B_real`, `filesize`).
- `humanize__hist__013` (`W_real`, `time`).
- `humanize__hist__014` (`W_real`, `__init__`, `i18n`, `number`).

## Workspace Matrix

- Result prefix: `humanize_pre_phase1_workspace`.
- Scheduled cells: `8`.
- Scoreable cells: `8`.
- Scoreable rate: `1.0`.
- Terminal statuses: `verified_pass=3`, `verified_fail=5`.

Harness status:

- `codex_workspace`: `4` cells, `4` scoreable, `verified_pass=1`,
  `verified_fail=3`.
- `kilo_workspace`: `4` cells, `4` scoreable, `verified_pass=2`,
  `verified_fail=2`.

This remains a same endpoint model, different CLI harnesses comparison. It does
not isolate a pure harness effect.

## Cost And Usage

- Usage observed: `8/8` cells.
- Conservative cost: `USD 4.00000000`.
- Observed-token estimate: `USD 2.37855060`.
- Observed-or-conservative estimate: `USD 2.37855060`.
- Per-harness observed estimate:
  - `codex_workspace`: `USD 1.35034440`.
  - `kilo_workspace`: `USD 1.02820620`.

Provider-billed dollars remain unavailable, so the priced token estimate remains
the canonical spend record.

## Policy And Isolation

- Test-edit policy violations: `0`.
- Out-of-scope policy violations: `0`.
- Kilo timeout rows: `0`.
- Hidden oracle leakage check: no hidden, oracle, or patch files were present in
  solver workspaces outside `.git` hook samples.

The recurring Toolz export-scope issue did not recur in this humanize matrix.

## Phase 1 Impact

The second-repo pilot strengthens the case for starting Phase 1 MVP
implementation as a multi-repo compiler effort. Reusable evidence includes:

- generic repo-history mining and certification tooling;
- commit-message fallback context labels when PR back-links are missing;
- hidden-test certification with editable-package verifier support;
- second-repo workspace ACUT loading through the same Codex/Kilo adapters;
- observed usage import for the second repo prefix.

## What This Cannot Prove

This pilot still cannot establish predictive validity, stable ranking, or a pure
harness effect. The matrix is small, tasks are clustered in one second repo, and
both harnesses use the same endpoint model. The correct next step is Phase 1 MVP
compiler implementation with explicit anti-predictive-validity guardrails, not a
validation claim.
