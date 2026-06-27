# Benchmark Compiler Prototype

This directory contains the current Barcarolle compiler prototype, selected
proposal-stage evidence, schemas, configs, and tests.

It does not prove predictive validity. It is the working prototype for task
selection, candidate certification, release construction, validation-policy
hardening, and future-holdout experiments.

Run tests from the repository root:

```bash
uv run --project experiments/phase1_compiler pytest -q
```

Key retained areas:

```text
configs/        # frozen and exploratory experiment configs
schemas/        # normalized task, release, and scorecard schemas
tools/          # compiler and analysis scripts
tests/          # executable regression/spec coverage
reports/        # selected sanitized reports
results/        # small JSON/CSV summaries referenced by reports/tests
```

Current evidence boundaries:

- predictive validity is not established;
- the old weighted target-profile selector is diagnostic only;
- repo-stratified/simple baselines remain the conservative mainline;
- candidate selectors need preregistered future holdout or rolling-origin
  validation before paid promotion;
- paid Agent calls require `LLM_BASE_URL` plus `LLM_API_KEY`.

See `docs/research/project-state-after-proposal.md` for the full project
handoff.
