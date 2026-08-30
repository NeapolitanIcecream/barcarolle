# Implementation Status

Status: current implementation boundary, 2026-08-30.

Barcarolle's first principle is to provide reliable evaluation methods for
self-evolving agents, with repository-level coding agents as the first concrete
domain. A self-evolving agent retains behavior-changing model, harness, prompt,
memory, skill, tool, or other persistent-state updates across tasks.

Barcarolle is an alpha library. The design documents define the intended
evaluation and evidence boundaries; this page records which parts the current
Python implementation enforces. A design statement is not evidence that the
runtime enforces it.

The active research program is broader than the current static,
task-selection-oriented implementation. See
[`research-program.md`](research-program.md).

## Research-Program Readiness

| Capability | Status |
| --- | --- |
| Self-evolving-agent lineage and persistent state | Not implemented as a reusable core evidence path. Exact `Agent` and runtime identities exist, and one experiment layer freezes a paired replicate schedule, but there is no general parent/action lineage, optimizer identity, persistent-state transition, or complete candidate archive across optimization rounds. |
| Pass-rate error on future real-world tasks | Static `future_pass_rate_mae` computation, fitting, summary, and replay paths exist. Predictive validity remains evidence-dependent. |
| Pass-rate-difference error between agents | Aggregate `pairwise_gap_mae` is computed from common result matrices. Difference-aware fitting, pair-population records, summaries across time splits, and equally prominent evidence-backed reporting are missing. |
| Increase in both errors under repeated evaluator-guided optimization | Not implemented. There are no parent links between agent versions, records for agent optimizers, evaluator feedback, queries, rounds, or epochs, or error curves by optimization budget. |
| Independent prospective evidence for a changing subject | A two-phase strict-prospective path exists for a frozen static `Benchmark Selection`. There is no sealed-cohort lifecycle that freezes the evaluation method, agent and evaluator versions, budget checkpoints, and predictions; keeps outcomes unavailable to both agent optimization and optional evaluator updates; scores those checkpoints; and retires opened cohorts from independent-test use. |
| Evaluation and method-selection stages | Not implemented. The code can calculate static losses and comparative summaries, but it has no deployment-derived absolute limits for both errors, no reliability decision that combines those limits with coverage and uncertainty, and no explicit `unresolved` outcome when the design cannot distinguish adequacy. |
| Operational behavior versus elicited capability | Not implemented. Existing `Result` identity and pass/fail evidence do not classify whether a lineage transition is a general capability improvement, evaluator-specific adaptation, an ability-preserving change, or an exploit-only change. |
| Task generation | The `Task Pool` module accepts a strict prepared package and optional generator provenance. No built-in forecast-based or adversarial task generator, repeated task-instantiation method, or generated-to-real response calibration exists. |
| Adversarial stress testing of evaluators and metrics | Not implemented. Current reports have no attack taxonomy, held-out attack family, evaluator candidate, evaluator-selection validation set, or meta-evaluation evidence. |
| Agent–evaluator coevolution | Not implemented. Current prospective continuity requires stable task-generator behavior; a separate protocol for repeated epochs and evaluator selection is needed rather than weakening that check. |
| Adversarial agent execution | The built-in path assumes a cooperative agent and shared host privileges. Deliberate test/scorer/grader/host attacks require a stronger isolation adapter. |

Do not infer a production capability from the research roadmap. Conversely,
do not treat an unimplemented method as out of scope: concrete implementation
should follow the next discriminating experiment rather than the outdated
roadmap centered only on task selection.

The three MAE objectives are the primary empirical outcomes, not the whole
definition of reliability. Evidence validity is a hard prerequisite; absolute
error limits ask whether both errors meet deployment requirements; degradation
under optimization asks how they change from `b=0`; method comparison chooses
among methods. A stable but inaccurate method, or one that only beats an
inaccurate comparator, is not thereby reliable.

## Detailed Implementation Matrix

The table below is an engineering ledger of exact records, validation rules,
and known gaps. New readers can stop after the readiness table above and return
here only when changing a specific module. Capitalized names in this section
refer to implemented records or modules, not additional research terminology.

| Module | Implemented | Partial or not yet enforced |
| --- | --- | --- |
| Records | Dataclass records, canonical digests, strict latest-schema JSONL conversion, boundary validation, one timezone-aware UTC parse/format contract, canonical exact Check-command identity, directly replayable Task text, and exact certification/source-event refs and digests. Loading requires exact keys, recursive field types, canonical representation, and line-numbered failures; lenient migration is not part of the runtime reader. Canonical data recursively maps floating signed zero to positive `0.0`, so typed and nested JSON values cannot fork identity on an equal zero. Public record validation reuses that dataclass schema conversion before domain checks, so malformed scalar, container, and nested-record shapes return validation errors instead of reaching unsafe field operations; valid records perform the conversion only once. WorkspaceConfig and RuntimeConfig reuse the same type contract and add positive-timeout plus null-or-nonempty hardware semantics. Agent identity separates the requested model from a proven immutable snapshot; an unresolved alias requires a bounded campaign scope. Records owns canonical Result IDs and direct Result-cache projections against Agent/Task/Check records so construction, Selection, Runner, and Reporting share one field contract. `SourceEventRecord` retains arrival, label-maturity, disposition, and rejection provenance; direct validation requires tuple-shaped nonempty reasons and never iterates a scalar as a collection. ResultCell payload states require exact nulls or nonempty string Result/exclusion bindings, matching the shape reloaded from JSONL. Selection weights and Metric values require exact finite built-in floats, so public validation cannot approve an integer representation rejected by canonical reload. Metric scopes require exact Agent-ID, two-agent-pair, or aggregate dimensions; optional refs and incomplete-state reasons use nonempty strings when present. `TaskRecord` separates dependency clusters from sampling strata. `RollingOriginRecord` retains mature and censored history/future refs plus the maturity cutoff. `SelectorInput` validation owns unique Agent/ref membership, ordered full Agent-record digests, pre-origin Result alignment, canonical cutoff time, and the exact selection-limit-to-budget-digest binding. Non-string or naive evidence timestamps fail validation rather than being interpreted as UTC. Small one-off scripts preserve supported older Results without adding runtime compatibility branches. | Future schema changes should add another small migration only when valuable paid results require it. |
| Task Pool | Candidate import/filtering, direct Task/Check construction, a persisted sanitized source-event ledger, symmetric fresh-workspace base-fail/reference-patch-pass certification for every repeat, rejection summaries, frozen pool records, and shared validation of persisted SourceEvent/Task/Check/certification artifacts. Candidate parsing rejects non-string identity, task, cluster, and stratum fields instead of coercing them; solver refs and resource-limit containers also keep their declared shapes before candidate identity is derived. Freeze likewise requires its persisted metadata and optional Task Pool ID to be strings instead of converting arbitrary caller values. The Task Pool record itself reuses Records schema and self-digest validation before artifact reconciliation; malformed top-level timestamps return errors. Every observed-frame observation must not postdate generation run completion, and run completion must not postdate Task Pool creation. Record validity and Task/Check member validity are ordered prerequisites, so certification and SourceEvent relations never consume malformed top-level collections or member bindings. Certification repeat count requires an exact positive integer at config construction; a boolean cannot execute a check and then become unreplayable evidence. WorkspaceConfig and RuntimeConfig validate before any certification Check or config digest enters evidence. Filtering retains unavailable or out-of-range events as excluded records; missing Check maturity remains right-censored. Candidate-linked SourceEvents are unique, and persisted certification plus rejected-candidate evidence retains canonical candidate-ID order. Transient certification decisions require an exact boolean before evidence serialization, SourceEvent finalization, or Task Pool freeze. Certification evidence shares one Workspace/Runtime context across the pool while binding each exact Check execution and the built-in Verification adapter. Top-level non-object evidence and malformed nested attempts return validation errors; normalized attempts keep outcome, timeout, and failure-label state coherent. Verifier-workspace, check-launch, and unexpected verification failures stop certification rather than becoming candidate rejections. The fixed Pylint SWE-bench adapter also certifies `FAIL_TO_PASS` and `PASS_TO_PASS` counts separately, persists sanitized trusted-patch path-overlap relations as a generation-provenance adapter sidecar, derives deterministic dependency components, keeps stable behavior identity independent of run-specific dependency inventory, and opens and replays the complete Task Pool bundle before paid stages. A second static SWE-bench adapter freezes one exact dataset/repository slice plus OCI manifests, emits the ordinary strict prepared package, and reuses the same certification/publication boundary; its first full run certified all 75 SymPy Verified candidates and published 75 Tasks, 75 Checks, and 54 patch-overlap clusters. Evidence retains normalized outcomes, paths, and digests rather than raw patches, workspaces, or Check output. | Concrete source collection and relation types remain adapter responsibilities. Patch-path overlap is conservative dependence evidence, not proof that disjoint Tasks are independent. The static adapter intentionally does not download datasets, clone repositories, install harnesses, or choose source populations. |
| Verification | Hidden material is injected only after diff capture; one canonical tree digest covers path, entry type, content, and executable bits; symlinks, unsupported entries, pre-existing reserved paths, and merge injection fail closed. Check outcomes are normalized; raw timeout, exit code, and duration require exact finite types, and malformed state cannot become pass evidence. Normalization config rejects overlapping exit meanings and malformed failure-label/redaction controls at construction. The exact bound command is rechecked before preparation and execution without forcing local paths into semantic Check identity. Agent and Check subprocesses validate time/capture bounds before launch, retain bounded output with full-stream digests, run in owned process groups on POSIX, and escalate timeout cleanup from TERM to KILL. | The built-in path still shares the caller's host privileges. Stronger network, filesystem, CPU, or memory limits belong in an optional execution adapter. Non-POSIX fallback cannot prove descendant containment and therefore reports containment failure. |
| Workspace | Fresh solver/verifier checkouts containing the immutable base commit and its ancestors but no later source refs, direct Task text in `TASK.md`, validated checkout-local supporting-file refs, diff capture/replay that omits Python runtime caches, semantic Check-manifest binding, optional artifacts, cleanup after high-level runs, complete-plan preflight, and just-in-time Agent model-scope/harness/endpoint revalidation. Repository binding validates WorkspaceConfig before it can key the immutable run context; preflight reapplies that contract plus full RuntimeConfig validation even to an empty plan. Complete-plan relation checks remain per cell while immutable Check and full Agent bindings are validated once per unique identity; per-cell pre-invocation rechecks remain unchanged. Repository, Agent, and Check bindings are tuple-backed values in an immutable per-run context; bind functions return a new context and reject conflicting rebinds. Paid bindings bind each declared resolved harness path to its exact content digest and use only `OPENAI_BASE_URL` and `OPENAI_API_KEY`; unresolved model aliases cannot execute outside their declared campaign window. Optional artifacts always use relative refs below their output root; retention controls require exact booleans and summary modes are validated at config construction. Current Workspace runs persist monotonic solver/verifier checkout, diff replay, Agent, Check, and cleanup phase timings in the existing latency mapping. Evidence stores digests rather than credentials or raw URLs. | The built-in harness shares the caller's host privileges. Use a host-isolation adapter when the Agent is adversarial or concurrent same-user runs require isolation. The process-global owned-workspace table is only a locked cleanup-ownership guard, not execution configuration. Checkout caching still requires warm/cold measurements across repository sizes and must cross the documented reopening threshold. |
| Result Store | Exact execution cache identity including requested/resolved/scoped model identity, Records-owned Agent/Task/Check projection checks at construction, exact ResultCell binding replay, complete Matrix policy replay across join/denominator digests, cells, abstention, and scoreability, derived scoring and policy identities, append-only repricing from retained usage without rerunning Agents, missing-cell queries, result matrices, one locked live index per Runner operation, durable flush/fsync appends, shared-lock reads, line-numbered schema/canonical-ID/tail/duplicate-ID failures, and explicit conservative truncated-tail recovery. Exact cache-identity computation validates Task, Check, Agent, WorkspaceConfig, RuntimeConfig, and Task/Check linkage before construction; Result construction additionally validates WorkspaceRun before linkage or cache projection. Scoring configuration validates at construction, canonicalizes equivalent numeric rates to sorted floats, and owns a read-only snapshot so one pricing behavior has one stable digest. Exact-identity reuse is a fixed non-weakening invariant; `ResultCacheConfig` retains only one exact-boolean opt-in for structurally valid benchmark-invalid Results. ResultQuery validates all filter tuples, explicit nullable timestamps, and bound order before store existence can affect the response. Local batch-append and filtered-load medians scale linearly through 10,000 records. | JSONL intentionally has no persistent secondary index or multi-writer design. POSIX advisory locking matches the current scoreable-execution platform; add another platform lock only with a real supported execution adapter. |
| Selection | Random, chronological-recency, coverage, and Dirichlet-smoothed stratified-forecast fixed rules plus an executable fitted rule mixture and a ten-point thirds-simplex rank-mixture grid; canonical algorithm-specific parameter snapshots so equivalent continuous numeric forms share one Selector identity and nested maps cannot drift with caller mutation; arrival-cohort rolling origins with fixed label-maturity lag and explicit censored refs; exact strict-prospective and counterfactual-replay semantics; exact-boolean future-holdout state and typed nonempty-string dependency filters at policy and persisted Origin boundaries; dependency-cluster blocking separated from Selector-visible sampling strata; derived budget/origin/feature/leakage identities; one-axis FeatureConfig validation that canonicalizes supported names and derives implementation-owned leakage classes; self-digested, leakage-linted feature snapshots; complete pre-origin Selector inputs; Benchmark Selections frozen by construction; shared deterministic Selection replay, ordered pre-origin Result-evidence assertions including frozen Agent cache-identity projection, and exact Task Pool-backed `task_count`/`task_stratum` value/time/source replay; capped post-stratification weights consumed by prediction metrics; mean-MAE, shrinkage-safe, EWMA-guarded, and one-standard-error simplex choice; replay-checked stratum TV/ESS/cap diagnostics; and a predeclared paired MAE summary with macro/weighted losses, pairwise differences, exact seed-bank variation, and deterministic Origin-block intervals gated at eight Origins. Metric construction rejects Selection/Origin eligibility-mode drift before prospective or counterfactual matrix alignment and derives one versioned metric-protocol digest from implemented scoring behavior; callers cannot supply an identity-only metric config. Training and paired Selector comparison accept only that current protocol, even when an unknown digest is internally consistent. `build_rule_selector` is the explicit fixed-rule path. `train_selector` replays each expert Selection, requires one ordered full Agent identity across Origins, validates the common frozen Task Pool and every `RollingOrigin`/`FeatureSnapshot`, projects each pre-origin and outcome Result cache identity back to its frozen Agent/Task/Check records, validates every bound Matrix Result including excluded cells and derives their allowed states from Result invalid ownership, recomputes MAE, requires mature training labels before deployment, and persists compact fitted weights. | ALG-001 through ALG-004 have no valid core outer-origin win claim and are not Runner defaults. A zero-call historical-order diagnostic rejected the current duration-stratum ALG-002 configuration, found ALG-003 seed-unstable, and observed ALG-001/004 retain coverage; because the source Checks materialized in 2026, those rows are explicitly not core rolling-origin evidence. The current metric-only fitter does not consume Task metadata values, but its Task Pool-backed evidence path is ready for a learned successor. The simplex chooser requires actual evaluated mixture Selections and does not replace the inverse-MAE trainer. The EWMA chooser ranks by recent loss but cannot bypass the unweighted full-history safe-switch. Interval calibration, core run-level replicate analysis, and model-based Selectors remain unimplemented. Add another fitting path only with a concrete estimand, enough prior-origin data, and comparative evidence; do not add a generic training platform. Dependency evidence remains adapter-owned rather than a core Selection graph service. |
| Reporting | Markdown/JSON summaries, source digests, claim boundaries with canonical requested-claim config and derived identity, fixed non-weakening Matrix-completeness and Metric-validity semantics, requested-claim-only evaluation, local-path sanitization, semantic-ID uniqueness for every top-level evidence type consumed by a claim, semantic plus digest validation of referenced SourceEvent/Task/Check/certification artifacts, source-event disposition and label-delay summaries, certification yield and rejection diagnostics, repeated-certification outcome-conflict quarantine rates, deduplicated later benchmark-invalid rates, arrival-versus-label-time cohort diagnostics, monotonic phase-latency coverage and checkout-plus-cleanup share, deterministic replay of the full Selector provenance chain including Task metadata Feature sources, exact bound ResultCell-to-Result identity/outcome replay, Matrix exclusion-state derivation from supplied Results, and paired MAE aggregation only after exact metric recomputation under the current implementation-owned metric protocol. Agent/Result identity claims require every Result's frozen Agent projection to match a supplied Agent and bind the Agent manifest digests. Separately supplied Agent records are an unordered evidence set; frozen SelectorInput and ResultMatrix order remains exact. Strict-prospective and counterfactual-replay performance claims are named separately. | Report strength depends on supplied evidence. Missing or invalid provenance, including an internally consistent unknown Metric protocol, produces `mae_summary=null` and an unsupported claim rather than a weaker implicit interpretation. Older Results omit unavailable phase timing instead of receiving zeros. The quarantine diagnostic detects conflicting normalized outcomes but does not identify their cause. Origin-block intervals do not represent dependency-cluster or run-level uncertainty. |
| Runner | End-to-end orchestration, cache reuse, lazy execution, selection freezing, scoring, fitted-Selector loading, report writing, and an offline `barcarolle report` command. Task Pool construction has direct config preflight, resolve/resource preflight, Workspace-bind/certify, and freeze/publish phases; configs fail before candidate resolution, all candidate resources fail before Workspace binding, and certification performs a just-in-time config recheck. Publication writes immutable content-addressed SourceEvent/Task/Check/certification bundles. Companion evidence appends validate complete semantic-ID uniqueness before idempotent resume or extension. `evaluate_selectors` preflights every Selector record and executable parameter set, all Agent IDs, the mode, and the complete origin schedule before Task Pool reads or companion writes; it then persists every counterfactual `Selector`/`RollingOrigin`/`FeatureSnapshot`/`SelectorInput`/`BenchmarkSelection` before future resolution, batch-validates all Results bound by reusable CellSets, and only then executes one deduplicated pending exact-cell union. `evaluate_prospective_selection` reloads and deterministically replays the complete strict `Selector`/`RollingOrigin`/`FeatureSnapshot`/`SelectorInput`/`BenchmarkSelection` chain, then resolves the exact frozen pre-origin Result view, Feature provenance, and Agent cache-identity projection before Task Pool reads. It validates and replays the selection-time pool, Task/Check cache identities, and Task metadata Feature sources before opening a later pool, materializes mature/censored future refs, and uses the same CellSet resolver and scorer. Censored refs remain provenance but never enter execution. Missing-cell plans are completely preflighted; partial executions keep already appended Results. Runner holds one locked live Result index through resolution, execution, repricing, and final resolution. Report filenames are direct typed children of their configured output directory and cannot traverse or substitute formats. The offline report command accepts the selection-time pool plus optional later pools. The Pylint experiment layer freezes and strictly replays a paired, stratified replicate schedule, binds a new campaign through a self-digested endpoint/total-budget/per-call-limit/schedule-derived-call-cap/pricing authority ledger, rejects malformed authority before file creation, requires enough remaining budget for one authorized call, preflights all remaining Runtime slots, and executes at most the first exact missing cell. An append-only amendment can accept one exact scoreable per-call-cost stop under a larger ceiling while preserving the original stop reason, frozen total authority, schedule, retries, and pricing. A concrete CLI loads the frozen Pylint Agent, Runtime, schedule, Task Pool, and local adapter bindings, verifies pinned verifier-image digest, architecture, and base commit, then exposes only explicit `authorize`, no-call `preflight`, and one-cell `run-next` operations with bounded JSON summaries. | Core Agent execution, training, and benchmark evaluation remain Python APIs while their research configurations are changing. Creating a replicate authority ledger still requires explicit user authorization; none is bundled or inferred from the historical pilot. The per-call reservation controls Barcarolle's estimated-cost authority; enforcing the provider-side maximum remains part of the Agent runtime budget. The CLI consumes a frozen experiment configuration; it does not generate Agent or Runtime records, choose pricing, or loop over paid cells. Core Runner does not consume replicate schedules or estimate run-level variation. Bounded concurrency and checkout caching remain future work with explicit prerequisites. |

The multi-repository research layer under
`examples/multi_repository_study/` inventories repository-local Origin
capacity, normalizes pinned public outcomes, aggregates repository-first
contrasts with cluster and leave-one-cluster-out uncertainty, calibrates
equal-budget random Selection, exercises outer repository folds, and replays
pinned local semantic rules. It is experiment code, not another module:
product Runner, Task Pool, Result Store, and Selection inputs remain
single-repository. The completed public screen nominated no algorithm, so it
does not justify widening core `train_selector` or adding an embedding service.

The generic supply boundary also accepts a strict prepared-candidate package
from an arbitrary external task generator and an existing complete user-maintained
Task Pool. Optional generation provenance separates stable behavior and source
protocol from run, observed frame, and output inventory. Pools without a
task generator remain valid, but cannot retain either task-generator-behavior or
source-protocol digests without the manifest that supports them. Attaching a
manifest replaces the pre-binding Task Pool ID with the final content-derived
identity, so run and output differences cannot retain one semantic ID. High-level
execution and scoring consume a complete validated bundle rather than parallel
Task/Check lists. No concrete built-in task generator or plugin registry is part of this
boundary.

Task Pool and claim-boundary reports enumerate the complete validated generated
bundle: core Task Pool members, generation manifest, observed-frame inventory,
and adapter sidecar. Nested refs are reported only after bundle validation.

Reusable EvaluationCellSet identity binds the requested scoring configuration
and benchmark-invalid Result reuse policy in addition to Selection, Origin,
future pool, refs, Agents, and join policy. A changed resolution policy creates
a new frozen view; an unchanged policy resumes the exact persisted cells.

Generated Task Pools bind a canonical source window separately from stable
task-generator behavior and source-protocol digests. Validation requires the window
to end no later than generation completion, which precedes pool creation, and
reconciles every outside-range SourceEvent disposition. Later pools may add
observed events under unchanged behavior and protocol without reusing run or
output identity.

External Result admission now validates one immutable source manifest against
the complete Task Pool, Agent, Workspace, and Runtime identities. It writes
per-row decisions and an idempotent receipt, defaults availability to an
import-time floor, and rejects different executions sharing one cache identity.
Store- and receipt-scoped import locks serialize the first local observation,
Result admission, and receipt publication without creating an empty Result
Store. Receipt publication syncs the receipt file and parent directory before
returning success.
Runner lazy fill replays the persisted Selection chain before cache access, and
multi-origin evaluation derives all origin views from one physical Result
snapshot.

Runner represents an absent pre-origin Result-availability lower bound as null;
rolling evaluation forwards the explicit history-window start. TimeRange is
reserved for actual parseable windows rather than empty-string sentinels.

The batch Runner evaluator remains counterfactual-only. The two-phase strict
path freezes a planned window with `select_benchmark`, then
`evaluate_prospective_selection` reloads and deterministically replays that
persisted chain, resolves its frozen pre-origin Result view, and replays Feature
provenance plus Agent cache identity before supply reads. It validates and
replays the selection-time pool, pre-origin Task/Check cache identities, and
exact Task metadata Feature sources before binding one later Task Pool into the
EvaluationCellSet. It
retains censored refs without executing them, reuses the ordinary
Result/preflight/scoring path, and fails on Agent drift, missing or drifted
pre-origin Results, non-replayable Selections, snapshot drift, incomplete
source-window coverage, premature pool creation, or missing report evidence.
Reporting indexes the supplied later pools by immutable identity, rejects
duplicates, loads only referenced bundles once per identity, and replays each
mature/censored cohort before publishing a strict-prospective performance
claim.

Task Pool publication validates a sibling staging directory, fsyncs every
member and the staging directory, renames to an absent target, and fsyncs the
target parent. A different existing target fails instead of being overwritten.
Paid example scripts share one examples-layer reservation/completion ledger for
durable events and cost folding. Accounting-snapshot replay rejects malformed timestamps
and nonfinite, negative, string, or boolean accounting values before writing;
missing cost remains absent for a call without Result evidence. A no-event
initial snapshot requires zero spend and remaining amount equal to its budget;
event-backed overrun evidence remains recordable. Experiment-specific endpoint,
pricing, scoreability, exact-result, and continuation checks remain direct code.

Selection also exposes an offline ALG-001 safe-switch chooser with explicit
shrinkage, minimum-history, margin, and sample-standard-error gates over the
same validated paired MAE rows. It is not wired as a Runner default and has not
shown an outer-origin empirical gain. The offline chooser family validates
Selection/Metric/future-matrix comparability but does not receive selected
matrices or exact Results; promotion requires full replay plus persisted choice
provenance rather than treating these analysis functions as evidence gates.

The offline ALG-002 path is the fixed `stratified_forecast` family. It consumes
the existing `task_stratum` snapshot records, applies symmetric Dirichlet
smoothing to a declared trailing ref window, allocates capacity-constrained
largest-remainder quotas, and stores either unit weights or capped
post-stratification weights in `BenchmarkSelectionRecord.selected_weights`.
`summarize_stratified_forecast` replays the chain and derives TV, effective
sample size, and cap diagnostics from explicit evaluation-time future strata.
Reporting publishes those rows only after complete provenance validation and
binds the frozen TaskRecords digest. No real comparison has selected its
hyperparameters.

The offline ALG-003 path consists of `build_rule_mixture_grid`,
`SimplexChoiceConfig`, and `choose_rule_mixture_from_grid`. It freezes all ten
thirds-simplex points before outcomes, requires actual complete paired MAE for
every point, returns equal weights under the minimum history, and otherwise
uses the discrete one-standard-error rule to prefer the eligible point closest
to equal weights. It does not infer blended performance from expert metrics,
replace `train_selector`, or establish an empirical advantage.

The offline ALG-004 path consists of `EWMASwitchConfig` and
`choose_selector_with_ewma_guard`. It validates exact paired MAE plus training
and deployment Origin evidence, rejects training times, cutoffs, or label
maturity beyond deployment, orders history by unique Origin cutoffs, ranks
Selectors with a declared EWMA half-life, and then requires the ranked
non-fallback candidate to clear the ordinary unweighted full-history
safe-switch. It does not add a weighted confidence interval, Runner policy,
record field, or empirical claim.

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

A claim of reliable evaluation for a self-evolving agent additionally requires:

- a declared agent lineage and optimizer, including every behavior-changing
  persistent-state transition relevant to the claim;
- a frozen evaluation method, versioned evaluators, feedback interface,
  optimization budget, and complete retention of every considered candidate's
  identity, lineage, update, and disposition; if expensive prospective outcome
  measurement samples candidates, its sampling rule and inclusion probabilities
  must also be frozen;
- future real-world tasks and reference standard that remain unavailable to the
  agent optimizer and evaluator-update process until predictions and the
  protocol are frozen;
- absolute error limits for both primary errors, plus coverage,
  uncertainty, abstention, and fallback rules;
- error curves over matched budget checkpoints and explicit separation of
  capability improvement, evaluator-specific adaptation, and integrity
  violations;
- a claim bounded to the tested optimizer, feedback, budget, threat model,
  repositories, agent families, and time horizon.

These requirements assume a cooperative Agent. Host-level isolation is
mandatory when the deployment treats the Agent as adversarial or runs mutually
untrusted same-host jobs.

Repository-maintenance tests and deterministic offline demos do not cross this
paid evidence boundary.

The cross-module storage, cache, pricing-view, and interruption rules are
consolidated in
[`docs/design/evidence-storage-and-recovery.md`](design/evidence-storage-and-recovery.md).
Only Task Pool members form an atomically published immutable bundle. Result
and Selector evidence remain owner-managed append logs; Workspace artifacts are
optional and best effort.

## One-Off Result Migrations

The current core does not load the pre-2026-07 Result cache schema. Preserve
those paid executions in a new file with:

```bash
uv run python scripts/migrate_pre_2026_07_results.py \
  --results path/to/records/results.jsonl \
  --checks path/to/records/checks.jsonl \
  --output path/to/records/results.latest.jsonl
```

The script refuses to overwrite either source or an existing output. It
preserves supported paid execution evidence while assigning current cache,
Result, and evidence identities. Preservation is not proof of exact cache
reusability: a changed Agent-visible task format, repository-history boundary,
or other execution identity keeps the old record as historical evidence rather
than relabeling it as equivalent. Rebuild FeatureSnapshots, SelectorInputs,
Selections, fitted Selectors, EvaluationCellSets, matrices, and metrics from
compatible migrated records rather than maintaining old-schema support.
It also normalizes two legacy states rejected by the current contract:
the known legacy `agent_failed` error becomes Agent-invalid, and an empty usage
map keeps usage unknown with `total_cost=null`. Other error, timeout, invalid,
or contradictory state combinations are rejected for manual ownership review
instead of being made reusable automatically.

Results produced by the immediately preceding schema may already have current
Check, pricing, and latency fields but still use `model_snapshot_id` for an
unresolved alias. Preserve them separately with:

```bash
uv run python scripts/migrate_unscoped_model_results.py \
  --results path/to/records/results.jsonl \
  --output path/to/records/results.latest.jsonl \
  --model-scope-id campaign-2026-07 \
  --model-scope-started-at 2026-07-01T00:00:00Z \
  --model-scope-ended-at 2026-08-01T00:00:00Z
```

This migration never treats the old value as a proven snapshot. It records it
as `requested_model_id`, requires one declared scope containing every execution,
recomputes current digests, and leaves the source unchanged. Rebuild downstream
FeatureSnapshots, SelectorInputs, Selections, fitted Selectors,
EvaluationCellSets, matrices, and metrics because their old Result bindings do
not silently follow the new identity.

Results already using the current cache identity but created before explicit
evidence provenance can be migrated with:

```bash
uv run python scripts/migrate_result_evidence_provenance.py \
  --results path/to/records/results.jsonl \
  --output path/to/records/results.latest.jsonl
```

This script is only for records known to have been written by Barcarolle. It
adds managed observation provenance using the existing availability timestamp,
assigns the resulting canonical Result IDs/digests, validates canonical source
digests, refuses overwrite, and leaves the source unchanged. Rebuild the same
derived evidence chain listed above. It must not relabel third-party evidence;
import such evidence through the external Result admission contract instead.

## Near-Term Engineering Order

1. Add only the minimum closed-loop experiment evidence needed for a fixed
   candidate archive: evaluator identity, parent links between agent versions,
   behavior-changing persistent state, agent optimizer, evaluator feedback
   channel and detail, round/epoch, budget, candidate disposition, and
   prospective-cohort status. Do not prebuild a generic agent-optimization
   platform.
2. Extend current evidence-backed summaries so `future_pass_rate_mae` and
   `pairwise_gap_mae` receive comparable replay across time splits, agent-pair
   weighting, and reporting. Add separate evidence-validity, absolute-error,
   degradation-under-optimization, and method-comparison outcomes rather than
   one scalar reliability score.
3. Use the existing prepared-package boundary for the first experiment with
   repeated task instantiation. Add a concrete built-in task generator only
   when that experiment exposes a boundary the package must own.
4. Build adversarial stress tests with controlled agent variants and metric
   perturbations in experiment code first. Move a contract into core only after
   replay on an independent temporal validation set shows what must be durable.
5. Do not pay for a full repeated evaluator-guided optimization campaign until
   a frozen evaluator comparator, fixed-archive protocol, lineage and feedback
   evidence, independent prospective-evidence boundary, and analysis for both
   error curves are replayable. A small instrumented protocol pilot does not
   require an opened-data static winner. Do not tune the old five-repository
   pass-rate result again.
6. Keep checkout caching and bounded concurrency behind measured reopening
   thresholds. Strengthen host isolation before deliberately adversarial agent
   execution rather than treating hidden checks as a sandbox.
