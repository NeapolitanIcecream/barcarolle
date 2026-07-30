# SWE-bench Full estimand audit

This outcome-open diagnostic asks what the current rolling-origin direct-MAE
headline measures. It does not test a new Selector.

It reports:

- Agent-by-repository pass-rate prevalence;
- always-zero, Full-history, and previous-block direct MAE;
- Agent-by-repository paired losses for every frozen candidate;
- an orthogonal future-block variance decomposition;
- H5, H10, H20, and H40 reliability diagnostics;
- lagged versus same-future cross-Agent response association;
- the Agent-by-repository Oracle cells omitted by the earlier summary.

Run:

```bash
uv run --python 3.14.0 \
  --with numpy==2.5.1 \
  --with scipy==1.16.3 \
  --with pyarrow==25.0.0 \
  python examples/swe_bench_full_estimand_audit/audit.py run
```

Validate the committed summary without requiring ignored raw inputs:

```bash
uv run python examples/swe_bench_full_estimand_audit/audit.py validate
```

Add `--verify-inputs` to validate every pinned local input. The run uses no paid
calls, new Agent outcomes, sealed outcomes, or algorithm changes.

The v2 plan records the post-output contract amendments, pins the runtime, and
binds all repository Python execution sources plus dependency declarations.
The committed evidence is [`evidence/summary.json`](evidence/summary.json).
Two complete executions were byte-identical with SHA-256
`f114bf2fd8aaf77e57410f25c7c2962bb9082635b94d675deefb02cffc02a69a`.
