# Surrogate-Gate Audit

This example replays ALG-013, ALG-014, and THY-002S against the direct
held-out-configuration pass-rate MAE outcome. It preserves each failed parent
decision. It is a post-decision audit on already-open Multi-SWE outcomes, not
independent confirmation.

The ignored task-content, embedding, task-space, and THY-002S raw artifacts
must exist at the paths bound in `plan.json`. The executor loads
`plan-amendment-1.json` and `plan-amendment-2.json`, verifies their chain and
implementation digests, then validates every logical source binding before
Selection.

The accepted post-amendment reproduction used:

```sh
PYTHONDONTWRITEBYTECODE=1 uv run --with 'numpy==2.5.1' \
  python examples/surrogate_gate_audit/study.py \
  --output outputs/research/2026-07-29-surrogate-gate-audit/run-3.json \
  --summary outputs/research/2026-07-29-surrogate-gate-audit/summary-3.json

PYTHONDONTWRITEBYTECODE=1 uv run --with 'numpy==2.5.1' \
  python examples/surrogate_gate_audit/study.py \
  --output outputs/research/2026-07-29-surrogate-gate-audit/run-4.json \
  --summary outputs/research/2026-07-29-surrogate-gate-audit/summary-4.json

cmp outputs/research/2026-07-29-surrogate-gate-audit/run-3.json \
  outputs/research/2026-07-29-surrogate-gate-audit/run-4.json
```

The executor refuses to overwrite artifacts; use new run names for another
reproduction.

Committed results and interpretation:

- `evidence/summary.json`
- `docs/experiments/2026-07-29-surrogate-gate-pass-rate-mae.md`

No command makes a network, paid API, or sealed-holdout call.
