# Phase 1 MVP Compiler

This workspace builds the Barcarolle Phase 1 MVP compiler artifacts from
committed Phase 0 evidence. It does not run ACUT harnesses and does not claim
predictive validation.

Run tests:

```bash
uv run --project experiments/phase1_compiler pytest -q
```

Build the MVP artifact set:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  build-mvp \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

Validate generated outputs:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

The main outputs are written to:

```text
experiments/phase1_compiler/results/
experiments/phase1_compiler/reports/
```

Key closeout report:

```text
experiments/phase1_compiler/reports/phase1_mvp_closeout.md
```

## Evidence Boundary

The MVP compiler imports:

- Toolz as the primary target repo;
- humanize as the second target repo;
- Click only as a generic comparator;
- repaired Codex/Kilo workspace score tables;
- Phase 0 certification and cost summaries.

The current evidence supports compiler infrastructure only. These claims remain
explicitly disallowed:

- `predictive_validity_established`
- `pure_harness_effect`
- `production_benchmark_ranking`

The Phase 1 source-certification hardening artifacts are sidecar evidence under
`experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json`
and
`experiments/phase1_compiler/results/phase1_certification_hardening_decision.json`.
They do not change the historical MVP scorecards or establish predictive
validity.
