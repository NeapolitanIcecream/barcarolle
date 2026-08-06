# SWE-bench Full development replay

This directory holds the outcome-open H5/H10 direct pass-rate MAE experiment
and its post-result failure-localization diagnostic.

The development portfolio hides the target Agent's complete outcome column
from Selection. The diagnostic Oracles deliberately open future outcomes and
are not candidate Selectors.

Run from the repository root:

```bash
uv run \
  --with numpy==2.5.1 \
  --with scipy==1.16.3 \
  --with pyarrow==25.0.0 \
  python examples/swe_bench_full_development/study.py validate

uv run \
  --with numpy==2.5.1 \
  --with scipy==1.16.3 \
  --with pyarrow==25.0.0 \
  python examples/swe_bench_full_development/diagnostic.py validate
```

Raw memberships and run results remain under ignored `outputs/`. The committed
evidence contains compact direct-MAE summaries, repository and target-Agent
directions, reproduction digests, and the explicit claim boundary.
