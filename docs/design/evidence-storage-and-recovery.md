# Evidence Storage, Identity, And Recovery

Status: current enforced behavior, 2026-07-22.

This document defines where Barcarolle evidence lives, which identity controls
reuse, and what recovery is allowed after an interrupted write. It does not add
an Evidence module, a cross-module transaction, or a general artifact service.
Each existing module remains responsible for its records.

## Evidence Classes

| Evidence | Owner | Storage rule | Recovery rule |
| --- | --- | --- | --- |
| Task Pool bundle | Task Pool and Runner | Immutable directory published under an explicit artifact root | Validate the complete target; ignore unpublished staging directories |
| Agent Results | Result Store | Locked append-only canonical JSONL | Fail on an unterminated tail; repair only through `recover_result_store_tail` |
| Selector, Origin, Snapshot, Input, Selection, cell-set, matrix, and metric records | Runner and Selection | Single-writer append-only canonical JSONL with stable semantic IDs | Fail closed on invalid input; the current runtime has no automatic tail repair for these logs |
| Workspace run artifacts | Workspace | Optional files with relative refs and content digests | Best effort; artifact failure does not replace a completed normalized run |
| Reports | Reporting | Derived Markdown and JSON | Rebuild from validated source records |
| Migration output | One-off migration script | New current-schema file; source is unchanged | Validate the new file and rebuild downstream bindings |

The complete evidence for an experiment is the validated set of these records
and refs. It is not one atomically published directory.

## Explicit Roots And Paths

Task Pool creation requires `TaskPoolConfig.artifact_root`. Runner publishes
new bundles below:

```text
<artifact_root>/task-pools/<bundle-digest>/
  task-pool.jsonl
  source-events.jsonl
  tasks.jsonl
  checks.jsonl
  certification-evidence.jsonl
```

Published member refs are relative, share that directory, use the fixed member
names, and cannot escape `artifact_root`. Loading older externally supplied
records may accept absolute refs, but newly published bundles do not emit them.
Runner APIs require `artifact_root` whenever a Task Pool contains relative
refs.

The offline report command resolves its config paths relative to the config
file. Its `artifact_root` defaults to that directory. Reports emit local paths
under the report root or artifact root as relative paths.

Other paths are explicit and independent:

- `ResultStore.path` names the Result JSONL log;
- Runner's companion evidence logs are adjacent to that Result path;
- `WorkspaceArtifactConfig.output_root` owns optional run artifacts;
- `ReportConfig.output_dir` owns regenerated reports.

These roots are not aliases for one shared storage service. A reusable workflow
must pass them rather than depend on the process working directory.

## Immutable Task Pool Publication

Runner derives the bundle directory from the exact accepted Tasks, Checks,
sanitized certification evidence, SourceEvents, generator config,
certification config, canonical source window, creation time, and optional
declared pool identity. It
then:

1. validates the in-memory Task Pool and all members;
2. creates a staging directory beside the final target;
3. writes the manifest and four member files;
4. reloads and validates the staged files;
5. renames the complete staging directory to an absent target.

Creating staging beside the target keeps the rename on one filesystem. Readers
do not receive refs to the staging path. If the target already exists, publish
succeeds only when its manifest and every loaded member equal the requested
bundle. A different bundle at the same path is an error.

An interruption before rename can leave a hidden staging directory, but no
`TaskPoolRecord` produced by the publisher refers to it. An interruption after
rename leaves a target that must pass normal bundle validation before use.
Before rename, the publisher fsyncs every staged member and the staging
directory. After rename, it fsyncs the target's parent directory. This preserves
the complete-or-absent publication boundary across a process interruption and
uses the local POSIX filesystem's durability primitives. Readers still validate
every member before use; a non-POSIX or object-store backend needs its own
equivalent publication contract.

Published Task Pool members are immutable. A correction creates another bundle
and identity. It never edits the old directory or relabels paid Results.

Generated Task Pools separate behavior identity from observations. The
generator digest binds mode and source family; SourceEvent/Task/Check digests
bind inventory; `source_window_start` and `source_window_end` bind the requested
collection interval. Imported pools may have null windows and cannot serve as
prospective future evidence until a concrete adapter supplies a bounded source
frame.

## Result Execution Identity And Cache Reuse

Result reuse always uses `exact_identity`; this is not a configurable policy.
The only cache control is an exact boolean that opts into reusing a structurally
valid benchmark-invalid Result. `ResultCacheIdentity` binds:

- Task and Check identity, repository, base commit, submodule state, solver
  material, and all behavior-changing Check fields;
- the complete Agent manifest, including harness, prompt, tools, retrieval,
  skills, network policy, retry, budget, stochastic settings, and adapter;
- the requested model plus either a proven immutable snapshot or one bounded
  model-resolution campaign scope;
- Workspace, Runtime, and optional hardware profile identity.

Resolution compares the full validated identity, not its digest alone. The
first eligible Result in append order wins when duplicate exact identities are
present. There is no latest-result or best-result policy.

Distinct Result records may share an exact cache identity, for example across
pricing views, but every `result_id` occurs exactly once. Shared and exclusive
loads reject the second identical or conflicting ID before filtering or index
construction, so callers cannot disagree through first-wins versus last-wins
maps.

Agent-attributable invalid Results remain reusable because rerunning them would
change the observation. Benchmark-infrastructure invalid Results are not reused
by default; a caller must explicitly enable that diagnostic policy. A planned
replicate uses a distinct Runtime stochastic-settings identity, so it is a new
observation slot rather than a duplicate cache candidate.

The Pylint replicate resolver strictly replays its frozen schedule before
opening the Result Store, then resolves each named Runtime slot in schedule
order. Resume returns the first exact missing slot; the resolver cannot invoke
an Agent or select a latest or best duplicate.

Historical queries also constrain `result_available_at`. Repricing preserves
that timestamp, so a later price table cannot move old execution evidence into
a later or earlier rolling-origin cohort.

## Execution Views And Pricing Views

One Agent invocation has one `result_execution_digest`. That digest includes
the exact cache identity, normalized outcome, usage, latency, diff, verifier
metadata, and execution times. It excludes cost, pricing provenance, Result
record identity, and availability metadata.

`ScoringConfig` derives its digest from the pricing version and exact rates.
When a reusable execution lacks the requested scoring view, Result Store
recomputes cost from retained usage and appends a new `ResultRecord`. It does
not invoke the Agent or Check. The new view:

- keeps the execution fields and `result_available_at`;
- has the requested scoring-config digest and pricing version;
- receives the deterministic Result ID for that execution and scoring config;
- leaves the source Result unchanged.

Missing usage or a missing priced token field produces `total_cost=null`, not
zero. Reporting counts unique execution digests within each scoring view and
rejects conflicting cost or pricing data for the same execution and scoring
config. Adding pricing views therefore cannot increase execution count, pass
count, or failure count.

## Durable Result Appends

Result Store is the only log with the full current durability and tail-recovery
contract:

- scoreable execution requires POSIX advisory locking;
- readers take a shared lock and writers take an exclusive lock;
- a Runner operation loads and indexes the file once under one write session;
- each append operation writes complete canonical lines, flushes, and fsyncs
  before returning;
- first file creation also fsyncs the parent directory;
- an existing `result_id` is reused only when its digest is identical.

A reader rejects any non-newline-terminated final line. Recovery is explicit:

```python
recover_result_store_tail(ResultStore(path))
```

Under the exclusive lock, recovery adds a newline when the final bytes are a
parseable JSON value. Otherwise it truncates only those final bytes back to the
last complete newline. Normal schema validation still runs afterward. Recovery
never removes or changes a newline-terminated invalid record.

Runner appends each newly produced paid Result before starting the next cell.
After interruption, already fsynced Results remain available and the missing
exact cells can be recomputed. Automatic whole-cell retry remains subject to
the experiment ledger and retry policy; Result Store durability does not grant
permission to repeat a paid observation.

Paid examples share `examples/experiment_ledger.py` for their single-writer
reservation/completion event log. The helper requires newline-terminated event
records, fsyncs each append, validates a nonempty snapshot timestamp plus finite
nonnegative budget and known call costs, folds known cost from events, and
atomically replaces its derived snapshot. A completion without Result evidence
may omit cost; the shared known-spend sum excludes that unknown value, while the
experiment-specific stopped-call policy must prevent it from silently granting
a retry. Before the first event, an empty snapshot is valid only with zero spend
and remaining amount equal to its finite authorized budget. Once events exist,
their fold is authoritative and may retain an actual cost that exhausts or
exceeds the budget. Exact-cell recovery, endpoint authorization, pricing-table
validation, and scoreability remain in each experiment because their inputs and
stop conditions differ.

The Pylint replicate executor adds a self-digested static authority section to
that ledger. It binds the frozen schedule and Task Pool, Agent identities,
Workspace/base Runtime configs, endpoint digest, total budget, a campaign-wide
maximum estimated cost per call, schedule-derived exact cell-count call cap,
and ScoringConfig. Initialization validates the approval timestamp, every
non-empty string field, and the non-string sequence of non-empty pricing-source
strings before either the snapshot or event log can be created.
The remaining budget must cover one full per-call limit before a reservation;
returned Results must fit both the per-call and cumulative limits. Reservations
must follow the schedule prefix and completion fields must match the durable
Result. A pre-reservation denial adds no event: the snapshot's remaining amount
and bound make the decision replayable, and no paid attempt occurred. A
post-call excess is retained as a stopped completion with the Result's estimated
cost. If the Result was appended but the completion event was interrupted,
replay completes that event. A stopped reservation or a reservation without an
exact Result fails closed and cannot authorize a retry. The per-call limit is a
Barcarolle estimated-cost reservation; the Agent runtime budget remains
responsible for bounding the provider call before usage is returned.

## Companion Evidence Logs

Runner writes Selector evidence records under stable semantic IDs. A resumed
operation reuses the first record when the persisted digest is equal, or when
the only difference is an allowed observation timestamp normalized back to the
first record. Before matching or appending, Runner scans the complete existing
companion log and rejects every repeated semantic ID, whether its digest is
identical or conflicting. Any other same-ID difference fails.

Before a resumed batch executes any pending cell, Runner resolves all Results
bound by reusable EvaluationCellSets in one read and verifies the complete
ResultCell binding. Persisted missing or unbound excluded cells remain frozen
evidence and require no Result lookup.

These logs use one Runner writer, append one canonical line, flush and fsync it,
and fsync the parent directory on first creation. They do not currently share
Result Store's advisory lock, live index, or explicit tail-recovery function.
Invalid or incomplete input therefore fails closed. Do not silently truncate a
companion log or copy Result Store's recovery rule to it.

This is sufficient for the current serial Runner because pre-execution
Selector, Origin, Snapshot, Input, Selection, and cell-set records return from
their durable append before missing paid cells begin. Result matrices, metrics,
and reports can be reconstructed from their frozen inputs and durable Results.
Reopen this boundary before supporting multiple writers or if a real
companion-log interruption demonstrates a need for automated recovery.

## Workspace Artifacts And Reports

Normalized Results contain digests and bounded summaries, not full Agent
transcripts, raw completions, or workspaces. Optional Workspace artifacts use
relative refs below `WorkspaceArtifactConfig.output_root` and record a digest
and privacy bit; no path-mode switch can weaken that rule. Retention switches
are exact booleans, and summary modes are validated when the config is created.
Verifier workspace summaries are private because verification may contain
hidden material.

Workspace artifact writes are not an immutable publication protocol. If an
artifact write fails after execution, Workspace returns the completed
`WorkspaceRunRecord`, emits a bounded warning, and sets its artifact manifest
to null. Reports and cache reuse must not infer missing normalized evidence
from raw files.

Reports are derived outputs. Their configured Markdown and JSON names are
direct typed filenames below `ReportConfig.output_dir`; traversal, absolute
paths, nested paths, and swapped suffixes fail at config construction. An
interrupted or outdated report is rebuilt from the exact current-schema logs
and validated Task Pool bundle. A coverage claim requires the complete Task
Pool bundle. A Selector-performance claim also
requires the exact Selector, Origin, FeatureSnapshot, SelectorInput, Selection,
cell-set, matrix, metric, Agent, and Result chain. Missing provenance produces
an unsupported claim.

## Recovery Procedure

After an interrupted workflow:

1. stop other writers and retain the original files;
2. load the Task Pool manifest from its declared artifact root and validate the
   complete bundle;
3. load Result Store; if and only if it reports an unterminated final line, run
   `recover_result_store_tail`, record the returned action, and load again;
4. load companion evidence logs without modification; invalid content remains
   an owned repair or restore decision;
5. resume from frozen semantic records and exact Result cells;
6. rebuild matrices, metrics, and reports instead of editing persisted records.

Schema migration is separate from crash recovery. A migration writes a new
file, refuses overwrite, preserves the source, and validates the latest schema.
Migrated Results are historical evidence until their current execution identity
is proven compatible. Rebuild downstream cell sets, matrices, and metrics from
the compatible migrated records.

## Reopening Triggers

Do not add an artifact database, object-store layer, persistent Result index,
or distributed transaction for the current serial local workflow. Revisit the
storage boundary only when one of these conditions is concrete:

- a supported execution mode needs multiple Result writers;
- a supported non-POSIX platform needs an equivalent lock contract;
- an object store cannot provide the Task Pool directory-publication behavior;
- measured Result Store scans exceed the accepted linear JSONL boundary;
- companion-log interruption needs repeatable automated recovery;
- a model artifact is too large or unsafe for the existing compact Selector
  record.
