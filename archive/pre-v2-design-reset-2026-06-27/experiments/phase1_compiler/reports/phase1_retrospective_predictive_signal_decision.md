# Retrospective Predictive-Signal Decision

Decision label: `retrospective_signal_positive_directional`.

What happened: ran a no-paid retrospective pseudo-future signal analysis over repaired attrs, boltons, and click supply, with a sparse time-cutoff diagnostic.

Why it matters: the result tests whether Barcarolle-style selections have retrospective signal beyond simple baselines without adding new paid outcomes.

Action suggested next: keep paid ACUT cells blocked by default and require a future preregistered rolling-origin validation before any predictive-validity claim.

- Analysis mode: `mixed` with primary `retrospective_pseudo_future`.
- Repos included: `attrs, boltons, click`.
- Adapters included: `codex_workspace, kilo_workspace`.
- Windows: `3`.
- Designs evaluated: `8`.
- Best simple baseline: `temporal_recent_baseline` MAE `0.2149`.
- Best Barcarolle candidate: `coverage_constrained_unweighted` MAE `0.209`.
- Candidate beats baseline: `True`.
- Support level: `directional_retrospective_underpowered`.
- Paid ACUT cells: `0`.
- Paid LLM calls: `0`.
- Predictive validity established: `False`.
- PROCESS.md updated: `True`.

## Boundary

- Claim boundary label: `retrospective_signal_positive_directional`.
- The completed blocked split supplement remains diagnostic and post-hoc exploratory.
- Adapter differences are ACUT configuration evidence, not model-only superiority.
- No follow-up runbook was drafted or created.

## Verification

- Focused tests: `uv run pytest tests/test_phase1_retrospective_predictive_signal.py` passed, 6 tests.
- Relevant suite: retrospective predictive-signal focused tests.
- git diff --check: passed.
