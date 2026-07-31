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

The unchanged Selector portability replay is separate:

```bash
uv run \
  --with numpy==2.5.1 \
  --with scipy==1.16.3 \
  --with pyarrow==25.0.0 \
  python examples/modern_agent_panel/portability.py run \
  --output outputs/research/2026-07-31-modern-agent-portability/result-a.json
```

Repeat to `result-b.json`, then run `portability.py summarize` and
`portability.py validate`:

```bash
uv run \
  --with numpy==2.5.1 \
  --with scipy==1.16.3 \
  --with pyarrow==25.0.0 \
  python examples/modern_agent_panel/portability.py summarize

uv run \
  --with numpy==2.5.1 \
  --with scipy==1.16.3 \
  --with pyarrow==25.0.0 \
  python examples/modern_agent_panel/portability.py validate
```

The compact evidence retires all four unchanged methods. See
[`2026-07-31-modern-agent-selector-portability.md`](../../docs/experiments/2026-07-31-modern-agent-selector-portability.md).

The outcome-open consensus-rate candidate is evaluated separately. Its primary
run reads only the fixed-Harness lane:

```bash
uv run \
  --with numpy==2.5.1 \
  --with pyarrow==25.0.0 \
  python examples/modern_agent_panel/consensus_rate.py run \
  --output outputs/research/2026-07-31-consensus-rate-selector/result-a.json

uv run \
  --with numpy==2.5.1 \
  --with pyarrow==25.0.0 \
  python examples/modern_agent_panel/consensus_rate.py run \
  --output outputs/research/2026-07-31-consensus-rate-selector/result-b.json

uv run \
  --with numpy==2.5.1 \
  --with pyarrow==25.0.0 \
  python examples/modern_agent_panel/consensus_rate.py summarize \
  --output examples/modern_agent_panel/evidence/consensus-rate-summary.json

uv run \
  --with numpy==2.5.1 \
  --with pyarrow==25.0.0 \
  python examples/modern_agent_panel/consensus_rate.py validate \
  --summary examples/modern_agent_panel/evidence/consensus-rate-summary.json
```

See
[`2026-07-31-consensus-rate-selector.md`](../../docs/experiments/2026-07-31-consensus-rate-selector.md)
for the algorithm, multi-route search disclosure, sensitivity reversals, and
opened cross-system failure diagnostics.
