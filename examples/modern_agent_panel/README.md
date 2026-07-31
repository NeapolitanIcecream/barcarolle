# Modern Agent panel refresh

This experiment binds two public outcome cohorts before running any Selector:

- thirteen models evaluated with the same mini-SWE-agent v2.0.0 harness on
  SWE-bench Verified;
- three 2025-era complete Agent systems evaluated on SWE-bench Full.

The first lane is the primary outcome-open development population. The second
is a heterogeneous system diagnostic. Raw public result files remain under
ignored `outputs/`.

The study is candidate-free. Its Oracles measure capacity after future outcomes
are opened and are not implementable Selectors.

Run from the repository root:

```bash
uv run \
  --with numpy==2.5.1 \
  --with scipy==1.16.3 \
  --with pyarrow==25.0.0 \
  python examples/modern_agent_panel/study.py fetch

uv run \
  --with numpy==2.5.1 \
  --with scipy==1.16.3 \
  --with pyarrow==25.0.0 \
  python examples/modern_agent_panel/study.py run \
  --output outputs/research/2026-07-31-modern-agent-panel/result-a.json
```

Repeat the run to `result-b.json`, summarize, then validate:

```bash
uv run \
  --with numpy==2.5.1 \
  --with scipy==1.16.3 \
  --with pyarrow==25.0.0 \
  python examples/modern_agent_panel/study.py summarize

uv run \
  --with numpy==2.5.1 \
  --with scipy==1.16.3 \
  --with pyarrow==25.0.0 \
  python examples/modern_agent_panel/study.py validate
```
