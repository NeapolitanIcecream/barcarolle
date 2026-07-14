# Implementation Status

Status: current implementation boundary, 2026-07-14.

Barcarolle is an alpha library. The design documents define the intended
benchmark boundary; this page records which parts the current Python
implementation enforces. A design statement is not evidence that the runtime
enforces it.

## Current Capability Matrix

| Module | Implemented | Partial or not yet enforced |
| --- | --- | --- |
| Records | Dataclass records, canonical digests, JSON/JSONL conversion, boundary validation, and a latest-schema-only core. A one-off script migrates the pre-2026-07 Result cache without adding runtime compatibility branches. | Future schema changes should add another small migration only when valuable paid results require it. |
| Task Pool | Candidate import/generation, record construction, rejection summaries, and frozen pool records. | Task validation currently checks supplied evidence; it does not yet execute the base check, apply a reference patch, or measure repeatability itself. |
| Verification | Hidden material is injected only after diff capture; check outcomes are normalized and time-bounded. | The built-in subprocess path enforces timeouts. Stronger process, network, filesystem, or resource limits belong in an optional execution adapter. |
| Workspace | Fresh solver/verifier checkouts, solver-visible task material, diff capture/replay, optional artifacts, and cleanup after high-level runs. | The built-in harness shares the caller's host privileges and does not byte-bound output. Use a host-isolation adapter when the Agent is adversarial or concurrent same-user runs require isolation. |
| Result Store | Exact cache identity, append-only JSONL records, missing-cell queries, and result matrices. | JSONL is a single-writer format without locking, crash-tail recovery, or a persistent index. |
| Selection | Random, chronological-recency, coverage, and rule-mixture baselines; rolling-origin inputs; frozen selections; leakage checks; prediction metrics; and a mean-MAE meta-controller over complete prior-origin comparison rows. MAE is the current primary target. | Learned selectors and drift-aware Adaptive methods remain planned. Their data and fitted-parameter contracts will be designed with a concrete algorithm rather than added as a generic framework. |
| Reporting | Markdown/JSON summaries, source digests, claim boundaries, and local-path sanitization. | Report strength depends on the supplied task-validation, identity, cost, and denominator evidence. Hand-constructed non-canonical records should be rejected before reporting. |
| Runner | End-to-end orchestration, cache reuse, lazy execution, selection freezing, scoring, and report writing. | There is no stable CLI. `SelectorEvaluationConfig.origin_ids` is currently overloaded: Runner expects ISO origin times while Selection expects built origin IDs. |

## Evidence Requirements

For benchmark or research evidence:

- the paid-call harness uses `LLM_BASE_URL` and `LLM_API_KEY` as required by
  `AGENTS.md`;
- solver-visible material excludes hidden checks, which are added only after
  diff capture in a fresh verifier workspace;
- execution-based task validation supports the claimed task set;
- Agent identity changes when behavior-changing harness inputs change if
  results will be reused across runs;
- usage coverage, cost, result identity, denominators, and artifact privacy are
  represented accurately.

These requirements assume a cooperative Agent. Add host-level isolation when
the deployment treats the Agent as adversarial or runs mutually untrusted jobs.

Repository-maintenance tests and deterministic offline demos do not cross this
paid evidence boundary.

## One-Off Result Migration

The current core does not load the pre-2026-07 Result cache schema. Preserve
those paid executions in a new file with:

```bash
uv run python scripts/migrate_pre_2026_07_results.py \
  --results path/to/records/results.jsonl \
  --checks path/to/records/checks.jsonl \
  --output path/to/records/results.latest.jsonl
```

The script refuses to overwrite either source or an existing output. It
migrates reusable Result records only. Rebuild downstream cell sets, matrices,
and metrics from the migrated cache rather than maintaining old-schema support.
It also normalizes two legacy states rejected by the current contract:
the known legacy `agent_failed` error becomes Agent-invalid, and an empty usage
map previously marked `reported` or `complete` becomes `unreported` with
unknown total cost. Other error, timeout, invalid, or contradictory state
combinations are rejected for manual ownership review instead of being made
reusable automatically.

## Near-Term Engineering Order

1. Make Task Pool execute the base check, validate a supplied reference patch,
   and persist sanitized repeatability evidence when repeated runs are needed.
2. Complete usage and cost capture without treating unknown cost as zero.
3. Harden JSONL storage when concurrent writers or crash recovery become an
   actual deployment requirement.
4. Develop the next learned or Adaptive algorithm against MAE, adding only the
   data and parameter contract that algorithm needs.
