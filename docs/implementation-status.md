# Implementation Status

Status: current implementation boundary, 2026-07-14.

Barcarolle is an alpha library. The design documents define the intended
benchmark boundary; this page records which parts the current Python
implementation enforces. A design statement is not evidence that the runtime
enforces it.

## Current Capability Matrix

| Module | Implemented | Partial or not yet enforced |
| --- | --- | --- |
| Records | Dataclass records, canonical digests, JSON/JSONL conversion, boundary validation, directly replayable Task text, exact certification-evidence refs/digests, and a latest-schema-only core. A one-off script migrates the pre-2026-07 Result cache without adding runtime compatibility branches. | Future schema changes should add another small migration only when valuable paid results require it. |
| Task Pool | Candidate import/generation, direct Task/Check construction, executable aggregate-Check base-fail/reference-patch-pass validation, optional repeated patched checks in fresh verifier workspaces, rejection summaries, frozen pool records, and shared validation of persisted Task/Check/certification artifacts. Verifier-workspace, check-launch, and unexpected verification failures stop certification rather than becoming candidate rejections. The fixed Pylint SWE-bench adapter also certifies `FAIL_TO_PASS` and `PASS_TO_PASS` counts separately. Evidence retains normalized outcomes and digests rather than raw patches, workspaces, or Check output. | Separate SWE-bench test-set certification remains an adapter responsibility rather than a generic core behavior. Dependency setup and framework-specific import also remain adapter responsibilities. |
| Verification | Hidden material is injected only after diff capture; check outcomes are normalized and time-bounded; the exact bound command is rechecked before preparation and execution without forcing local paths into semantic Check identity. | The built-in subprocess path enforces timeouts. Stronger process, network, filesystem, or resource limits belong in an optional execution adapter. |
| Workspace | Fresh solver/verifier checkouts containing the base commit and its ancestors but no later source refs, direct Task text in `TASK.md`, validated checkout-local supporting-file refs, diff capture/replay that omits Python runtime caches, semantic Check-manifest binding, optional artifacts, and cleanup after high-level runs. | The built-in harness shares the caller's host privileges and does not byte-bound output. Use a host-isolation adapter when the Agent is adversarial or concurrent same-user runs require isolation. |
| Result Store | Exact execution cache identity, derived scoring identity, append-only repricing from retained usage without rerunning Agents, missing-cell queries, and result matrices. | JSONL is a single-writer format without locking, crash-tail recovery, or a persistent index. |
| Selection | Random, chronological-recency, coverage, and rule-mixture baselines; history-window-bounded rolling-origin inputs; frozen selections; leakage checks; prediction metrics; mean-MAE Selector choice over shared future Result evidence; and fitting the existing rule-mixture weights as one minus each expert's mean paired MAE. Persisted Selector inputs must retain the complete chronological history denominator. The mixture reuses the evaluated experts' ordering rules. MAE is the current primary target. | Calibration and drift-aware methods remain unimplemented. Add their data and fitted parameters only with a concrete algorithm and comparative evidence. |
| Reporting | Markdown/JSON summaries, source digests, claim boundaries, local-path sanitization, and semantic plus digest validation of referenced Task Pool artifacts before supporting coverage. | Report strength depends on the supplied task-validation, identity, cost, and denominator evidence. Hand-constructed non-canonical records should be rejected before reporting. |
| Runner | End-to-end orchestration, cache reuse, lazy execution, selection freezing, scoring, report writing, and an offline `barcarolle report` command. Task-pool builds bind a stable repository ID to a local checkout, bind per-candidate Check material, and write exact Task, Check, and certification-evidence files after freezing. Evaluation config accepts strictly increasing ISO `origin_times`; each future window ends at the next origin, and `origin_id` is created only in `RollingOriginRecord`. | The CLI only rebuilds reports from existing latest-schema JSONL records. Agent execution and benchmark evaluation remain Python APIs while those configurations are changing. |

## Evidence Requirements

For benchmark or research evidence:

- the paid-call harness uses `OPENAI_BASE_URL` and `OPENAI_API_KEY` as required by
  `AGENTS.md`;
- solver-visible material excludes hidden checks, which are added only after
  diff capture in a fresh verifier workspace;
- execution-based task validation supports the claimed task set;
- Agent identity changes when behavior-changing harness inputs change if
  results will be reused across runs;
- usage, unknown versus measured cost, result identity, denominators, and
  artifact privacy are represented accurately.

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
preserves supported paid Result records in the current schema. Preservation is
not proof of exact cache reusability: a changed Agent-visible task format,
repository-history boundary, or other execution identity keeps the old record
as historical evidence rather than relabeling it as equivalent. Rebuild
downstream cell sets, matrices, and metrics from compatible migrated records
rather than maintaining old-schema support.
It also normalizes two legacy states rejected by the current contract:
the known legacy `agent_failed` error becomes Agent-invalid, and an empty usage
map keeps usage unknown with `total_cost=null`. Other error, timeout, invalid,
or contradictory state combinations are rejected for manual ownership review
instead of being made reusable automatically.

## Near-Term Engineering Order

1. Expand the real paired Task history, then compare Selector MAE under
   rolling-origin evaluation when paid benchmark runs are explicitly authorized.
2. Develop the next learned or Adaptive algorithm only when its comparative
   MAE result can be measured against the implemented baselines.
3. Harden JSONL storage when concurrent writers or crash recovery become an
   actual deployment requirement.
