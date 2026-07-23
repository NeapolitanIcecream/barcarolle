# Barcarolle Internal Process Notes

Last updated: 2026-07-23.

These notes are for repository-maintenance agents. They are not user
documentation and they are not a source of truth for intended system behavior.
For implementation, use the current design documents under `docs/design/` as
the design authority. If this file conflicts with those documents, the design
documents win.

## Current Mode

The current development direction is predictive validity. Stages 0 through 2
in `docs/research-improvement-backlog.md` are complete. Immutable Task Pool
bundles and base OIDs, common Agent denominators, complete rolling-origin
provenance, repricing-safe summaries, bounded process containment, paid-call
preflight, focused runtime reliability, and the minimal final-form Selector
path are enforced. Certification binds the
verifier execution identity and canonical hidden-material tree; behavior-only configs derive their
own digests; FeatureConfig accepts one canonical set of supported names and
derives implementation-owned leakage classes; resumed timestamped records
reuse their first exact observation;
Repository, Agent, and Check bindings travel in an immutable per-run context;
Records owns one timezone-aware UTC contract and canonical Check-command
identity;
Runner uses one locked Result Store session per operation, appends each produced
Result durably, recovers only explicit unterminated tails, and preserves
monotonic phase timings. Result reuse is always exact full-identity reuse;
`ResultCacheConfig` exposes only an exact-boolean benchmark-invalid opt-in.
WorkspaceConfig and RuntimeConfig use one Records-owned shape contract at exact
cache identity, Runner Task Pool batch preflight, Task Pool certification,
Workspace repository binding, and Workspace execution preflight.
Workspace artifact refs are always relative to their output root; retention
flags and summary modes validate at config construction. Certification repeat
count is an exact positive integer before any Workspace check. Benchmark
Selection is frozen by construction. Report outputs accept only direct typed
Markdown/JSON filenames below their configured output directory.
`build_rule_selector` creates fixed rules without pretending to train;
`train_selector` fits the existing rule mixture only from replayed prior-origin
evidence under one ordered full Agent identity binding, and every training
Result cache identity projects back to that binding. The trainer also receives
the common validated Task Pool records, replays Origin/Snapshot provenance,
and binds every Result Task/Check cache projection; `select_with_selector`
requires the actual leakage-linted snapshot;
and `evaluate_selectors` freezes every counterfactual Selection before
executing one deduplicated exact-cell union. It validates the entire Selector
batch, executable parameters, Agent IDs, evaluation mode, and origin schedule
before Task Pool reads or companion writes. Selection derives one versioned
metric-protocol digest from concrete implemented scoring behavior; callers do
not supply an identity-only metric configuration. Training, paired comparison,
and Reporting accept only that current protocol; Records remains version-neutral.
Strict-prospective evaluation is a
separate two-phase path: `select_benchmark` freezes the Selection and planned
window, then `evaluate_prospective_selection` reloads the Selector, Origin,
FeatureSnapshot, SelectorInput, and Selection, deterministically replays the
Selection, resolves the exact pre-origin Result view, and verifies its Origin,
Agent, cutoff, Feature provenance, and cache-identity Agent projection before
Task Pool reads. It validates and replays the selection-time Task Pool and
pre-origin Task/Check identity, then replays exact `task_count` and
`task_stratum` FeatureRecord sources against the frozen Origin and TaskRecords
before opening the later pool. It then uses the same CellSet resolver and
scorer. Task Pools bind
their canonical source windows separately from behavior-only generator
identity. `SelectorInput` freezes both ordered Agent IDs and complete
Agent-record digests, so the second phase cannot reuse an ID with changed
execution behavior. Stage 3 now defines future cohorts by task
material arrival, separates label maturity with a fixed lag, retains censored
refs, persists a sanitized source-event frame, and certifies symmetric fresh
base/patched pairs. Dependency clusters are reserved for origin blocking while
sampling strata are the only one of those fields exposed to Selector features.
Comparable evidence now also produces predeclared macro/weighted paired MAE,
seed-bank variation, and sample-size-gated deterministic Origin-block
intervals; Reporting withholds that summary unless the complete chain validates
and recomputes. Core evidence JSONL now accepts only exact latest-schema,
canonical records with recursive type checks and line-numbered failures;
public validators replay that same schema before domain semantics, so malformed
containers or nested records return errors instead of reaching unsafe field
operations;
certification outcomes add an exact nested schema, while Result Store separately
owns durable-tail recovery. Direct SourceEvent validation requires tuple-shaped
nonempty rejection reasons and returns errors for malformed containers;
ResultCell payload validation requires exact nulls or nonempty string bindings,
and Metric dimensions/completeness use exact tuple, nonempty-string, and null
shapes, so directly validated nested records remain reloadable. Agent and Result
identities separate the requested model from a proven immutable snapshot;
unresolved aliases are limited to one declared campaign window and cannot
execute outside it. The Pylint experiment
layer now freezes the stratified replicate subset, seeded Agent order, exact
cell plan, and campaign-scoped Runtime slots before Results are opened. It
strictly replays that schedule, resolves every slot against exact Result
identity in frozen order, and can return only the first missing slot. The
Pylint adapter also persists sanitized trusted-patch path-overlap evidence,
derives deterministic dependency components, binds the evidence into Task Pool
identity, and replays patches plus SourceEvent clusters before paid stages. The
storage, cache, pricing-view, and crash-recovery contract is consolidated in
`docs/design/evidence-storage-and-recovery.md`; it does not introduce another
service or artifact abstraction. RI-031 now exposes observational certification
yield, rejection, outcome-conflict quarantine, and later benchmark-invalid
rates without tightening task gates. Paid examples share only the duplicated
single-writer resource-ledger persistence. Its snapshot replay validates a
nonempty timestamp plus finite nonnegative budget and known costs before any
write; a no-event initial snapshot must have zero spend and remaining amount
equal to budget before its first reservation. A result-less stopped call may
retain unknown cost. Experiment-specific
guards remain direct. RI-028 now has an examples-layer paid execution boundary. A new
campaign authority ledger binds the frozen schedule, Task Pool, Agents,
Workspace/Runtime configs, endpoint digest, total budget, one campaign-wide
per-call estimated-cost limit, schedule-derived call cap, and pricing.
Remaining budget must cover one full per-call limit before execution; preflight
covers every remaining Runtime slot, while each invocation can run only the
first missing cell. Result/ledger evidence is reconciled after an
interrupted completion event, and any stopped or reserved-without-Result cell
forbids automatic retry. Creating that ledger is an authorization act: no
campaign ledger or paid call was created during repository maintenance. Do not
reuse the historical pilot's constants or move the schedule into core Runner
without reuse evidence. RI-021
now records monotonic solver/verifier checkout, diff replay, Agent, Check, and
cleanup phases and reports checkout-plus-cleanup share only for complete
denominators; do not add a checkout cache until multi-repository warm/cold
measurements cross its reopening gate. The scoped RI-034 structural audit now
has a temporary full-suite branch-coverage input and no dead-code candidates;
the coverage artifact remains outside the repository. Two Reporting slices
separate
latency summarization and Selector trace responsibilities; a third slice
separates certification-evidence record parsing, per-record semantics, and
cross-record reconciliation; a fourth separates paired-MAE Selection, Metric,
future-matrix, and comparability validation; a fifth separates Selector
provenance indexing, required evidence, Task Pool reconciliation, and
per-Selection links; a sixth separates pre-origin Result resolution from
FeatureSnapshot Result-view and leakage checks; a seventh separates Selector
report cohort/Selection rows, MAE derivation, and source-digest assembly; an
eighth separates Result execution-state, cost, and limitation summaries; a
ninth separates source-event collection, observation-boundary, accepted/
rejected linkage, and coverage checks; a tenth separates latest-schema Union,
collection, mapping, nested-record, and scalar coercion without changing its
fail-closed behavior; an eleventh separates learned-Selector training
FeatureSnapshot indexing, SelectorInput indexing, and provenance links while
retaining the complete future training contract; a twelfth separates training
Result indexing, matrix-cell binding, exact denominator coverage, and
strict-prospective availability; a thirteenth separates training Metric
indexing, matrix provenance, value recomputation, exact coverage, and
within-origin comparability; a fourteenth separates training ResultMatrix
indexing, per-matrix provenance, role pairing, and shared future-evidence
checks; a fifteenth separates FeatureRecord scope/time checks from Result
provenance and requires every present Result-level Task, Check, and Agent link
to match the bound Result; a sixteenth separates rolling-origin cohort
partitioning from record assembly and rejects missing or mislinked Task Pool
member records before deriving denominators; a seventeenth separates
certification-result indexing, exact frozen-pair coverage, and frozen-record
digest reconciliation without changing the certification evidence schema.
An eighteenth separates Cell membership, payload-state, exact-denominator, and
ResultMatrix scoreability checks; Result, excluded, and missing payloads now
fail closed on incoherent bindings. A nineteenth separates RollingOrigin mode,
cohort, cluster, time, maturity, cutoff-rule, and policy validation; Origin
records now bind the declared cutoff rule and reject a future window that starts
before the cutoff. A twentieth separates SourceEvent material-time validation
from its disposition state machine; malformed material times now fail closed
and rejection reasons must be non-empty. A twenty-first separates replicate
schedule protocol, Task/Check membership, Agent treatment, and Runtime preflight;
campaign IDs are strings, repeat counts are integers, and paired Agent
configurations must differ. A twenty-second separates the historical Pylint
pilot's exact Result selection, per-effort rows, paired rows, and completion
claim; unrelated Runtime identities cannot enter the summary, and completion
requires a completed resource ledger. A twenty-third separates registered
Selector validation from per-Origin MAE row coverage and normalization; the
former combined helper is no longer a structural hotspot. A twenty-fourth
keeps intrinsic SelectorInput membership, budget, and Origin bindings in
Records while Selection uses the same validator; the separately supplied
Reporting Agent records are compared as a set, while the frozen SelectorInput
and matrix Agent order remains exact.
A twenty-fifth keeps the Task Pool certification reconciler as the visible
cross-record audit surface while making its nested inputs fail closed. A
malformed scalar rejection-reason value is rejected once and is not iterated
during SourceEvent linkage. Certification attempts also enforce the normalized
Verification state machine: passes have no failure label, non-passes have a
non-empty failure label, and timeouts are invalid outcomes.
A twenty-sixth keeps the replicate campaign authority direct: finite-cost
parsing is shared, limit validation is isolated, and the exact call cap is
derived from the frozen schedule instead of accepted as duplicate input. The
campaign executor has no `refactor_now` or `refactor_soon` hotspot.
A twenty-seventh makes the public Selector-evaluation boundary explicit and
removes one misleading identity path. `evaluate_selectors` rejects any policy
that cannot supply a predeclared future denominator before reading Task Pool
artifacts, writing evidence, or invoking an Agent. `make_selector_id` now takes
a Selector record and derives the same ID used by the builder from behavior and
provenance fields; observation time, the ID itself, and the self-digest are not
identity inputs. Keep strict-prospective Selection and the existing evidence
records. Reopen performance evaluation only with a separately linked
post-origin Task Pool or source frame; do not mutate the frozen Origin or add a
generic streaming service.
A twenty-eighth completes that retained final-form boundary without adding a
source-frame service. Generated Task Pools persist and validate their source
windows while generator identity describes behavior rather than observed
inventory. One later Task Pool is linked through the existing
`EvaluationCellSet`; Selection derives and replays mature/censored future refs,
Runner reuses its one Result/CellSet/scoring path, and Reporting plus the
offline CLI require both immutable bundles before supporting a strict claim.
The frozen strict Origin remains unchanged. `SelectorInput` also binds complete
Agent-record digests in Agent order, closing same-ID configuration drift between
the two phases. The full-signal 38-file structural scan now reports 123 hotspots
(3 now / 47 soon / 73 monitor), with no baseline regression and no dead-code
candidate. The new shared resolver, prospective report replay, and source-window
validator are characterized future refactor boundaries; do not add a context
object, validation framework, source service, or second executor solely to
reduce static counts.
A twenty-ninth closes RI-048 at the paid preflight boundary. A validly
self-digested Selection log could change selected refs to another eligible
history cell while keeping its original Selection ID and provenance links. The
prospective Runner previously opened Task Pool artifacts before Reporting could
detect that deterministic Selector replay disagreed. Selection now owns one
`ensure_selection_replay` assertion over all semantic Selection fields. Runner
loads Selector and FeatureSnapshot evidence and calls it before Task Pool reads;
Reporting, learned-Selector training, and stratified diagnostics use the same
assertion instead of three local field lists. Observation time and self-digest
remain excluded because replay happens later. No report-to-runner dependency,
preflight framework, or new record was added.
A thirtieth closes RI-049 at the same boundary. The complete persisted
Selector chain could replay while a Result frozen by SelectorInput was absent,
had a different digest, fell outside the frozen Agent/history/cutoff scope, or
no longer matched FeatureSnapshot provenance. Reporting and training checked
those links, but strict execution reached Task Pool reads first. Selection now
owns one direct `ensure_selector_input_result_evidence` assertion that resolves
frozen Result bindings in SelectorInput order and replays the scope and Feature
provenance contract. Input construction, training, and prospective Runner use
it; Reporting retains its multi-error claim accumulator rather than becoming a
Runner dependency. No record, registry, validator framework, or storage index
was added. The full-signal 38-file scan falls to 122 hotspots
(3 now / 47 soon / 72 monitor), with no regression or dead-code candidate.
A thirty-first closes RI-050 without adding a cross-record framework. Result
Store construction, Selection, and Reporting had three copies of the
ResultCacheIdentity-to-Agent/Task/Check field relation, while strict Runner did
not replay it. Records now owns one Agent projection and direct mismatch
functions. SelectorInput's frozen Agent digests reject Result Agent drift
before any Task Pool read. Runner then validates the selection-time bundle,
replays Origin, and checks Task/Check identity before reading the future pool
or invoking an Agent. The two-phase order reflects actual data availability;
it is not a new service or context object. The full-signal scan falls again to
119 hotspots (3 now / 47 soon / 69 monitor), with no regression or dead-code
candidate.
A thirty-second closes RI-051 at the first point where frozen TaskRecords are
available. FeatureSnapshot and Selector replay previously proved internal
consistency but did not prove that `task_metadata` values came from the
selection-time Task Pool. A fully redigested `task_stratum` counterexample
changed the deterministic Selection and reached the future-pool read. Selection
now owns one direct metadata provenance assertion: all FeatureRecords bind the
Origin/config digest; `task_count` matches the Origin and Task Pool; and
`task_stratum` exactly covers history refs with the Task value, known-at time,
and canonical Task digest. Construction, strict Runner, and Reporting reuse
it. Unknown Task metadata fails closed. Runner invokes it after validating the
selection pool and Origin but before future supply or Agent execution. The
current trainer does not consume metadata values, so no speculative training
input, feature registry, or service was added. The full-signal scan remains at
119 hotspots (3 now / 47 soon / 69 monitor), with no regression or dead-code
candidate.
A thirty-third closes RI-052 by removing a redundant configuration axis.
FeatureConfig previously accepted feature names and a separately declared
leakage-class list even though the builder hardcoded that relation. Empty,
duplicate, unknown, and permuted names could also produce distinct digests
without distinct extraction behavior. FeatureConfig now validates non-empty,
unique supported names, normalizes them to builder order, and derives classes
from one three-entry mapping. Production callers pass names only. This is an
alpha config API cleanup; persisted FeatureSnapshot records do not migrate.
No compatibility shim or FeatureSpec registry was added. The full-signal scan
remains at 119 hotspots (3 now / 47 soon / 69 monitor), with no regression or
dead-code candidate.
A thirty-fourth closes RI-053 at the learned-Selector Agent boundary. Training
previously compared only Agent IDs across Origins. Fully redigested evidence
could vary model/prompt/harness identity by Origin, or change every frozen Agent
digest consistently while retaining Results from the old Agent, and still fit.
Selection now compares ordered `(agent_id, agent_record_digest)` bindings across
Origins and uses the Records-owned cache projection to bind every training
Result back to that AgentRecord. Task/Check replay is a separate next decision
because it requires Task Pool records. No duplicate Agent inputs or training
context object were added. The full-signal scan remains at 119 hotspots (3 now
/ 47 soon / 69 monitor), with no regression or dead-code candidate.
A thirty-fifth closes RI-054 at the learned-Selector Task/Check boundary.
Training Origins carried only a Task Pool identity, so a fully redigested
Result/Matrix/Metric chain could change base commits or Check identity and
still fit. Selection's training API now explicitly receives the existing
TaskPoolRecord, ordered Tasks, and Checks. Runner loads one validated bundle;
Selection validates deployment/training Origins, replays Snapshot Task metadata,
and applies the Records-owned Task/Check cache predicate to pre-origin and
outcome Results. The existing Origin Task Pool digest already binds the fitted
Selector provenance. No TrainingDataset, context object, or new record was
added. The full-signal scan remains at 119 hotspots (3 now / 47 soon / 69
monitor), with no regression or dead-code candidate.
A thirty-sixth reduces the Runner training boundary after its evidence contract
stabilized. `train_selector` now delegates ordered Selection-provenance loading,
outcome-log filtering, and exact Result-binding resolution to three direct
helpers while retaining the same public arguments and read order. Its measured
CCN/NLOC fell from 24/125 to 4/47 and it moved from `refactor_soon` to `monitor`;
the helpers are below hotspot thresholds. The full-signal scan remains at 119
hotspots, now 3 now / 46 soon / 70 monitor. The remaining monitor signal is the
public seven-argument contract; do not hide it with `**kwargs` or add a one-use
context object solely to clear the metric.
A thirty-seventh closes RI-055 at the ResultCell-to-Result boundary. Reporting
previously checked a bound Matrix cell's Result ID, Agent/Task/Check, and cache
identity but not its outcome. A fully redigested CellSet/Matrix chain could
therefore claim a different outcome while retaining the original Result;
Runner scoring also downgraded that mismatch to a missing cell. Records now
owns one seven-field mismatch predicate covering Result ID/digest,
Agent/Task/Check, required identity, and outcome. Result Store, Runner,
Selection training, and Reporting share it. The full suite passes 641 tests
with 2 skipped. The full-signal scan remains at 119 hotspots (3 now / 46 soon /
70 monitor), and the predicate is below hotspot thresholds. No record, schema,
framework, telemetry, network access, or paid call was added.
A thirty-eighth closes RI-056 at the shared CellSet resume preflight. The
resolver previously validated persisted CellSet structure before executing the
pending union, but did not resolve its bound Results until later scoring. A
drifted reused outcome therefore allowed an unrelated pending Agent call first.
Runner now batches every reused Result ID into one read and applies the RI-055
binding predicate before missing-result planning or Agent execution. Explicit
missing/abstained CellSets remain immutable and reusable. The full suite passes
642 tests with 2 skipped. The full-signal scan falls to 118 hotspots (3 now /
46 soon / 69 monitor); the new loader and pure validator are below thresholds.
No execution context, persistent index, schema, network access, or paid call
was added.
A thirty-ninth closes RI-057 for bound excluded training cells. Runner loaded
every Matrix cell carrying a Result ID, while Selection required exact coverage
only for cells whose state was `result`. Legitimate common benchmark exclusions
were therefore rejected as extra Results through Runner, while direct training
could omit their evidence. Training now distinguishes bound from unbound cells
by Result ID/digest rather than state and applies the RI-055 predicate to every
binding. A `complete_with_exclusions` fixture fits with the excluded Result and
fails when it is absent. The full suite passes 643 tests with 2 skipped; the
full-signal scan remains at 118 hotspots (3 now / 46 soon / 69 monitor). No new
exclusion policy, schema, framework, network access, or paid call was added.
A fortieth closes RI-058 at Matrix exclusion derivation. Exact Result fields
alone did not prove that a cell was entitled to be `excluded`; a normal passing
Result could be removed from the common denominator and still support a
Reporting identity claim or learned-Selector fit. Result Store now owns one
pure Matrix-evidence check. It resolves exact bindings, derives task-wide
benchmark-invalid exclusions, and reconstructs the two existing agent-invalid
policy outcomes. Selection training and Reporting reuse it. Binding resolution
and derived-state checks remain separate small helpers. The full suite passes
645 tests with 2 skipped, and the full-signal scan returns to 118 hotspots (3
now / 46 soon / 69 monitor) with no new hotspot. No join-policy registry,
record, schema, framework, network access, or paid call was added.
A forty-first closes RI-059 at Matrix-wide join-policy consistency. The first
RI-058 implementation accepted each agent-invalid cell when it matched either
supported policy independently, so one scoreable Matrix could exclude one
agent-invalid Result while counting another as failure. No single
`ResultJoinConfig` could produce that denominator. The evidence check now
reconstructs the complete Matrix under each supported configuration and
requires one whole-Matrix match. A direct Result Store specification preserves
the counterexample. The full suite passes 646 tests with 2 skipped; the
full-signal scan remains at 118 hotspots (3 now / 46 soon / 69 monitor), and
the revised helper remains below thresholds. No policy registry, persisted
config record, schema, framework, network access, or paid call was added.
A forty-second closes RI-060 at declared Matrix policy replay. RI-059 proved
that one policy could produce all cells, but it did not bind that policy to the
Matrix's declared join/denominator digests or policy-derived abstention reason.
A redigested Matrix could retain default failure cells while claiming the
agent-exclusion policy, or rename an agent-exclusion abstention as missing
evidence. Result Store now replays the current four executable combinations of
missing-cell and agent-invalid behavior and accepts only an exact match across
policy digests, cells, abstention, and scoreability. Existing builder and replay
share the agent-exclusion predicate. The full suite passes 648 tests with 2
skipped; the full-signal scan remains at 118 hotspots (3 now / 46 soon / 69
monitor), and the changed helpers remain below thresholds. No policy registry,
persisted config record, schema, framework, network access, or paid call was
added.
A forty-third closes RI-061 at campaign-authority publication. The initializer
previously trusted Python annotations: a scalar `pricing_sources` string became
a character list, while non-string endpoint, scope, or accounting values could
publish a ledger that its own loader rejected and overwrite protection made
unrecoverable. Authority timestamps, non-empty strings, and the pricing-source
sequence now fail before snapshot or event-file creation. Small scalar/source
helpers keep the validator at `monitor` (CCN 6) after an intermediate
`refactor_soon` signal. The full suite passes 654 tests with 2 skipped; the
full-signal scan remains at 118 hotspots (3 now / 46 soon / 69 monitor). No
authority was created, no policy/schema/framework was added, and no paid or
network call occurred.
A forty-fourth closes RI-062 at Result Store load uniqueness. Locked append
prevented a new conflicting `result_id`, but shared reads accepted duplicate IDs
already present in JSONL. Some callers preserved both records, session indexing
kept the first, and CellSet batch preflight's dictionary kept the last. The
shared loader now rejects the second occurrence with its line number, whether
the digest is identical or conflicting, before filtering or indexing. Four
public cases cover ordinary and locked-session reads. The additional hash pass
is linear beside the existing linear parse. The full suite passes 658 tests
with 2 skipped; the full-signal scan remains at 118 hotspots (3 now / 46 soon /
69 monitor), and the helper is below thresholds. No schema/index/service,
network access, or paid call was added.
A forty-fifth advances RI-034 at Task Pool source-window validation. The
47-line helper mixed window shape/canonical-time/creation checks with per-event
disposition and reason reconciliation. One characterization freezes its exact
error tuples and order across absent, partial, invalid, noncanonical, reversed,
late, inside, and outside cases. The public orchestrator now combines one
boundary parser and one event reconciler; both helpers remain below thresholds.
The full suite passes 659 tests with 2 skipped, and the full-signal scan falls
from 118 to 117 hotspots (3 now / 45 soon / 69 monitor). Ruff and Lizard each
lose one signal. No state object, framework, schema, network access, or paid
call was added.
A forty-sixth advances RI-034 at strict-prospective Reporting replay. The
83-line helper mixed later-Task-Pool identity indexing and lazy bundle loading
with mature/censored cohort replay. One direct characterization freezes the
duplicate, drift, replay-failure, and missing-pool error order; proves that an
unreferenced pool is not loaded; and proves that two Selections sharing one
future pool load its bundle once. Reporting now keeps identity/load
orchestration visible while small helpers own duplicate indexing and one-cohort
comparison. The original helper moves from `refactor_soon` to `monitor` (64
NLOC, Lizard CCN 14, cognitive complexity 16); both helpers remain below
thresholds. The full suite passes 660 tests with 2 skipped. The full-signal
scan remains at 117 hotspots but shifts from 45 to 44 `refactor_soon` findings
and from 69 to 70 `monitor` findings; Ruff and Lizard each lose one warning.
No cache service, context object, framework, schema, network access, or paid
call was added.
A forty-seventh advances RI-034 at the shared Runner CellSet resolver. The
153-line helper mixed plan indexing, reusable evidence preflight, pending-union
execution, ResultCell indexing, and CellSet construction. Existing integration
specifications already cover one execution per shared cell, cached sequential
equivalence, partial-failure recovery, reusable-Result preflight before pending
calls, missing-CellSet resume, and the strict-prospective reuse path. One new
ordering specification requires duplicate plan identities to fail before the
CellSet log is read. Small pure helpers now own plan indexing, pending-union
derivation, ResultCell uniqueness, and one CellSet build; the shared locked
session and its nine real dependencies remain visible in the orchestrator. The
resolver falls to 113 NLOC and Lizard CCN 11; its cognitive-complexity and Ruff
signals disappear, leaving only one Lizard `refactor_soon` signal for the
explicit orchestration contract. All four helpers remain below thresholds. The
full suite passes 661 tests with 2 skipped. The 38-file scan remains at 117
hotspots (3 now / 44 soon / 70 monitor), while Ruff and Complexipy each lose
one warning. Further extraction would either duplicate eight or nine execution
dependencies or add a one-use context object, so this boundary is retained.
No execution fork, framework, schema, network access, or paid call was added.
A forty-eighth closes RI-063 at companion evidence-log append. Runner's shared
append helper returned as soon as it found the target semantic ID. If an
existing Selection/Origin/Snapshot/Input/CellSet/Matrix/Metric log contained a
second identical or conflicting ID, append could report an idempotent resume
while later readers rejected the same log or observed a different cardinality.
Two red Selection-log cases reproduce both forms. The already-linear scan now
checks every existing ID for uniqueness before applying the unchanged
same-digest or first-observation-time resume rule. It also prevents an
unrelated duplicate from being extended by a new append. The full suite passes
663 tests with 2 skipped. The full-signal scan remains at 117 hotspots (3 now /
44 soon / 70 monitor); the helper remains a single `monitor` finding at
cognitive complexity 18. No persistent index, lock redesign, repair path,
migration, schema, network access, or paid call was added.
A forty-ninth closes RI-064 at Reporting evidence identity. Top-level
Selections, CellSets, Matrices, and Metrics were grouped or indexed without an
explicit uniqueness error, while Result reports indexed Agents and executions
without rejecting duplicate Result or Agent IDs. Two identical Selection
records could therefore leave `benchmark_selection_frozen` supported, and the
direct Result report API could support a summary over duplicated identities.
Six public cases cover Result/Agent summaries, the frozen-Selection claim,
cache completeness, Agent/Result identity, and all four Selector evidence
record types. One linear helper now rejects repeated semantic IDs; each claim
uses the identities in its own evidence boundary. Existing provenance checks
for Origin/Snapshot/Input/Selector records remain unchanged. The full suite
passes 669 tests with 2 skipped. The full-signal scan remains at 117 hotspots
(3 now / 44 soon / 70 monitor) with no new tool finding. No uniqueness
registry, validation framework, schema, network access, or paid call was added.
`build_claim_boundary` remains the one public orchestrator for five explicit
claim predicates and their reason order. Each stable predicate owns its local
validation, while Selector provenance retains its explicit evidence parameters
instead of adding a one-use argument bundle solely to clear a static threshold.
Reporting's remaining SelectorInput linker is a direct list of independent
consistency checks for multi-error claim diagnostics and should not be split
again. Characterized tests preserve these evidence contracts. Continue one
evidence boundary at a time. Do not introduce a validation framework or Cremona
baseline during this large active change set.
A fiftieth separates Task Pool construction into the existing three execution
phases: resolve and preflight candidates, bind Workspace material and certify,
then freeze and publish the immutable bundle. A three-case specification fixes
the requirement that every candidate's reference patch, Check command, and
hidden-material path fail before any Workspace binding. The public orchestrator
falls from 139 NLOC / Lizard CCN 24 / cognitive complexity 24 to 7 NLOC / CCN
2 / cognitive complexity 1. The three phase helpers stay below high-priority
thresholds. The full-signal scan falls from 117 to 116 hotspots (3 now / 43
soon / 70 monitor), while Lizard and Complexipy each lose one finding. The
original commit-resolution and error order is unchanged. No context object,
pipeline framework, schema, dependency, telemetry, network access, or paid
call was added.
A fifty-first closes two persisted Task Pool replay gaps. Candidate coverage
formerly used sets, so two distinct rejected SourceEvents could share one
candidate ID and inflate the source frame while validation succeeded. Non-null
SourceEvent candidate IDs are now unique. Certification evidence must also
retain the producer's candidate-ID order, and rejected candidate IDs match that
ordered sequence exactly. The full suite passes 673 tests with 2 skipped; the
full-signal scan remains at 116 hotspots (3 now / 43 soon / 70 monitor) with no
new tool finding. Keep these as direct linear checks in Task Pool; do not add a
candidate registry or persistent index.
A fifty-second closes Task Pool certification-context drift. Runner certifies a
pool with one WorkspaceConfig and one RuntimeConfig, but persisted evidence
previously allowed candidate records to mix those digests. One linear helper
now requires a single non-empty value for each shared config field; reference
patch and Check-execution bindings remain per candidate. The full suite still
passes 673 tests with 2 skipped, and the full-signal scan remains at 116
hotspots (3 now / 43 soon / 70 monitor). Do not duplicate these digests into
TaskPoolRecord or introduce a config registry.
A fifty-third closes malformed bounded-process request handling and separates
the stable containment phases. Empty commands, nonpositive or nonfinite time
bounds, and nonpositive or non-integer capture bounds now fail before process
start. The public runner delegates stream setup, bounded wait, containment and
pipe drain, and exceptional cleanup; existing POSIX process-group behavior is
unchanged. It falls from 73 NLOC / Lizard CCN 20 / cognitive complexity 29 /
Ruff 15 to 46 / 3 / 1 / below threshold. The full suite passes 680 tests with 2
skipped; the scan falls to 115 hotspots (3 now / 42 soon / 70 monitor). Keep
this as direct functions; do not add a process-runner class or state object.
A fifty-fourth closes malformed resource-ledger accounting and separates its
stable replay phases. Snapshot reconstruction now rejects malformed timestamps,
nonfinite budgets, and negative, nonfinite, string, or boolean known costs
before opening the output file. A completion without Result evidence may omit
cost; downstream experiment rules decide whether that stopped call permits any
further action. The public function delegates reservation/completion folding,
budget validation, and cost summation and falls from 57 NLOC / Lizard CCN 21 /
cognitive complexity 27 / Ruff 12 to 19 / 3 / 2 / below threshold. The full
suite passes 690 tests with 2 skipped; the scan remains at 115 hotspots and
shifts to 3 now / 41 soon / 71 monitor. Keep this as direct examples-layer
functions; do not add a ledger class or experiment framework.
The same first-call boundary rejects an empty snapshot with inflated remaining
authority or unproven prior spend. Apply that exact-total rule only before the
first event; event-backed completion costs must still rebuild even when they
exhaust or exceed the budget. Four public cases cover the distinction, and the
full suite passes 694 tests with 2 skipped without changing the structural scan.
A fifty-fifth closes malformed SourceEvent rejection-reason containers and
separates disposition binding, reason, and maturity checks. Strings and mappings
can no longer masquerade as reason sequences, and an integer no longer raises
from validation. The public helper falls from 39 NLOC / Lizard CCN 20 /
cognitive complexity 25 / Ruff 12 to 9 / 1 / 0 / below threshold; its direct
binding state machine is monitor-only.
A fifty-sixth closes ResultCell payload type drift and separates result,
excluded, and missing state checks. Empty exclusion data is not equivalent to
null on a result cell; Result IDs/digests and exclusion reasons are nonempty
strings when present. The dispatcher falls from 30 NLOC / Lizard CCN 21 /
cognitive complexity 28 / Ruff 13 to 8 / 4 / 3 / below threshold. The full
suite passes 697 tests with 2 skipped; the scan falls to 114 hotspots (3 now /
39 soon / 72 monitor). Keep these as direct state helpers; do not add a general
runtime type-validation framework.
A fifty-seventh closes Metric dimension and completeness truthiness. Agent
scope requires one nonempty Agent ID, pair scope requires a two-element tuple
of nonempty IDs, aggregate scope requires one nonempty aggregation level, and
unused dimensions are null. Optional budget/stratum refs and incomplete-state
reasons are nonempty strings when present. The public validator falls from 47
NLOC / Lizard CCN 20 / cognitive complexity 20 / Ruff 12 to 22 / 3 / 2 / below
threshold; its dimension table is monitor-only. The full suite passes 704 tests
with 2 skipped; the scan remains at 114 hotspots and shifts to 3 now / 38 soon /
73 monitor. Do not replace these direct checks with a schema framework.
A fifty-eighth closes transient certification-decision truthiness. An integer
`accepted=1` could previously pass both SourceEvent finalization and an
otherwise valid Task Pool freeze. Certification evidence serialization,
finalization, and freeze indexing now share one exact-boolean guard. The
finalizer delegates candidate coverage, one-record projection, and ordered
local validation; freeze remains the sole cross-artifact reconciler. It falls
from 66 NLOC / Lizard CCN 20 / cognitive complexity 20 to 17 / 2 / 0 and leaves
the hotspot list. The full suite passes 707 tests with 2 skipped; the scan falls
to 113 hotspots (3 now / 37 soon / 73 monitor). Do not add a generic runtime
schema validator or repeat Task/Check/evidence reconciliation in the finalizer.
A fifty-ninth closes non-object certification-evidence handling. Record parsing
already reported the malformed item, but SourceEvent linkage then called
`.get()` on it and raised. Linkage now indexes mapping-shaped evidence only.
The retained certification reconciler delegates parsing/semantics,
collection/config checks, accepted Task/Check coverage, and rejected/summary
coverage to direct functions. It falls from 79 NLOC / Lizard CCN 24 / cognitive
complexity 34 / Ruff 17 to 13 / 1 / 0 / below threshold; the phase helpers stay
below hotspot thresholds. The full suite passes 708 tests with 2 skipped; the
scan falls to 112 hotspots (2 now / 37 soon / 73 monitor), and Task Pool leaves
the investigation queue. Do not add a certification-evidence bundle or generic
validation framework.
A sixtieth closes Selection/Origin eligibility-mode drift at Metric
construction. A self-digested strict-prospective Selection could be scored with
a counterfactual Origin and same-pool future evidence. Matrix alignment now
checks the mode first and characterizes all 18 ordered failure reasons,
including prospective pool, denominator, and censoring branches. The public
helper delegates provenance, mode-specific denominator, and cell-identity
phases and falls from 70 NLOC / Lizard CCN 24 / cognitive complexity 28 / Ruff
19 to 32 / 5 / 4 / below threshold; both phase helpers stay below hotspot
thresholds. The full suite passes 709 tests with 2 skipped; the scan falls to
111 hotspots (1 now / 37 soon / 73 monitor). Preserve error precedence; do not
add a matrix context object or policy registry.
A sixty-first closes Claim Boundary control and Agent-evidence drift. ClaimConfig
now accepts only one unique tuple of supported claims and canonicalizes it to
the stable claim order. Matrix completeness and Metric validity are fixed claim
semantics; the former configurable weakening axes are removed. The
`agent_result_identity` predicate requires every Result Agent to be supplied and
to match the Agent projection frozen in its cache identity; Claim Boundary
source digests include Agent manifests. `build_claim_boundary` evaluates only
requested claims, reuses existing Selector source-digest and Task Pool
artifact-path projections, and delegates five stable claim decisions plus local
Selection/Matrix/Metric/CellSet evidence phases. It falls from 288 NLOC /
Lizard CCN 73 / cognitive complexity 21 to 133 / 14 / 5 and moves to `monitor`;
the Selector-metric decision is 43 / 8 / 1. The full suite passes 714 tests with
2 skipped; the full-signal scan reports 113 hotspots (0 now / 37 soon / 76
monitor), critical counts 0/20/0, and no dead-code candidate. Keep the existing
provenance function's explicit evidence parameters; do not add a claim registry,
context object, or generic validation framework.
A sixty-second closes the metric-identity and batch side-effect boundary.
`MetricConfig` had no scoring behavior: its caller digest could relabel
identical metrics and its optional budget duplicated Selection evidence. It is
removed from Selection and Runner APIs. Metric records use one versioned,
implementation-derived protocol digest and retain the frozen Selection budget;
add another configuration axis only with concrete varying behavior. Runner
materializes and validates every Selector record and executable parameter set,
then Agents, mode, and the full origin schedule, before Task Pool reads or
companion writes. A pure mode/schedule helper removes one cognitive-complexity
signal while `evaluate_selectors` keeps its 15 real dependencies explicit. The
full suite passes 714 tests with 2 skipped; the full-signal scan reports 112
hotspots (0 now / 36 soon / 76 monitor), critical counts 0/19/0, and no
dead-code candidate. Do not add a metric registry, generic configuration
framework, or one-use evaluator context.
A sixty-third closes the Result-cache control boundary. The removed
`reuse_policy` represented no executable choice: exact full-identity reuse is a
benchmark invariant. The remaining benchmark-invalid reuse flag now accepts
only an exact boolean, so integers and strings cannot silently change missing
cells or paid-work planning. The replicate campaign keeps its direct ban on
enabling that flag. Five red constructor specs, 91 Result Store/campaign tests,
and the full suite of 719 tests with 2 skipped pass. The scan remains 112
hotspots (0 now / 36 soon / 76 monitor), with critical counts 0/19/0 and no
dead-code candidate. Do not add alternate cache policies without a concrete,
evidence-safe reuse contract.
A sixty-fourth closes Workspace artifact controls. Relative refs below the
configured output root are invariant, so the one-value `path_mode` field is
removed. Stdout/stderr and final-diff retention flags require exact booleans;
both workspace-summary modes validate at construction. The one-use execution
validator is removed. Four red constructor specs and all 71 Workspace tests
pass. The scan remains 112 hotspots (0 now / 36 soon / 76 monitor), critical
counts 0/19/0, while Ruff findings fall from 21 to 20. Do not add another
artifact mode until a concrete safe behavior exists.
A sixty-fifth closes certification repeat-count shape before execution.
`CertificationConfig(True)` previously ran one base/patched pair and then
produced evidence rejected by its own nested schema. The config now accepts
only an exact positive integer; floats, strings, nulls, booleans, and
nonpositive integers fail before any Workspace check or digest construction.
The weaker runtime comparison is removed. Six red specs and all 63 Task Pool
tests pass. The scan remains 112 hotspots (0 now / 36 soon / 76 monitor), with
critical counts 0/19/0, 20 Ruff findings, and no dead-code candidate.
A sixty-sixth closes report output confinement. `ReportConfig` now rejects
absolute, traversal, nested, backslash-containing, whitespace-padded, or
format-swapped filenames and accepts one direct `.md` plus one direct `.json`
name below `output_dir`. Six red specs and all 56 Runner tests pass. The scan
stays at 112 hotspots (0 now / 36 soon / 76 monitor), critical counts 0/19/0,
20 Ruff findings, and no dead-code candidate. Keep this as direct config
validation; do not add a path wrapper or report-publication service.
A sixty-seventh closes current Metric-protocol enforcement at consumption.
Selection batch-preflights training and paired-comparison Metrics against the
implementation-owned digest; Reporting reports unknown protocols as
unsupported. Records does not hard-code the algorithm version. A shared direct
guard replaces arbitrary-digest equality and keeps the paired validator at
`monitor` after rejecting a transient structural regression. Two red specs and
all 229 Selection/Reporting tests pass; the full suite passes 736 tests with 2
skipped. The scan remains 112 hotspots (0 now / 36 soon / 76 monitor), critical
counts 0/19/0, 20 Ruff findings, and no dead-code candidate. Do not add a
protocol registry until more than one executable protocol must coexist.
A sixty-eighth through seventieth close two rolling/Verification truthiness
boundaries. `future_holdout_known` is an exact boolean before cohort branching
or policy identity. Raw Check timeout, exit code, and duration accept only
their declared finite types, so `exit_code=False` cannot become pass evidence.
`CheckNormalizationConfig` rejects overlapping code meanings and malformed
labels, excerpt bounds, markers, or raw-text controls at construction. Sixteen
red specs pass.
A seventy-first deduplicates complete-plan binding preflight by immutable Check
key and full Agent-record digest. Relation validation remains per plan, and
Workspace still rechecks each selected cell before creation and immediately
before invocation. Direct plan and Agent-binding helpers removed a transient
complexity regression; the final scan remains at 112 hotspots.
A seventy-second requires rolling-origin dependency filters to be a tuple of
nonempty strings in both policy construction and persisted Origin validation.
Three red specs and the full suite of 756 tests with 2 skipped pass. No paid
call, campaign authority, schema, registry, generic validation framework, or
new dependency was added.
A seventy-third compares three independent Stage 0 hypotheses. Scoring config
and Task Pool source-window validation both fail before their execution
boundaries, so they remain lower-priority cleanup. The two persisted fields
declared as `float` were the live gap: integer representations passed public
record validation with matching self-digests but failed canonical reload after
schema coercion. Selection weights and Metric values now require built-in
finite floats before companion append. Two red public specs pass; the loader,
schema, and generic writer remain unchanged. The full suite passes 758 tests
with 2 skipped, and the 38-file full-signal scan remains at 112 hotspots (0 now
/ 36 soon / 76 monitor) with no dead-code candidate.
A seventy-fourth compares scoring identity, an internal open-lower-bound
TimeRange sentinel, and Selection's lone investigate-soon hotspot. Scoring is
the only reproduced behavior gap: integer and float rates computed the same
cost but produced different digests, and the caller's mutable source mapping
could change a frozen config after construction. `ScoringConfig` now validates,
normalizes rates to sorted floats, and stores a read-only snapshot while Runner
retains its pre-Agent recheck. The TimeRange case remains P2 cleanup and
Selection is not refactored without a correctness finding. The full suite
passes 763 tests with 2 skipped; the 38-file full-signal scan remains at 112
hotspots (0 now / 36 soon / 76 monitor) with no dead-code candidate.
A seventy-fifth removes the retained open-lower-bound sentinel. Selection-only
pre-origin loading no longer constructs `TimeRange("", cutoff)` merely to pass
an empty string into ResultQuery. The helper accepts `str | None`, receives null
for an unbounded query, and receives `history_window.start` in rolling
evaluation. The actual TimeRange and ResultQuery contracts remain unchanged.
The full suite passes 763 tests with 2 skipped; the 38-file full-signal scan
remains at 112 hotspots (0 now / 36 soon / 76 monitor) with no dead-code
candidate.
A seventy-sixth compares shallow-frozen configuration aliases with the
persisted-record write boundary. Task Pool source mappings are projected into
content-digested records before publication, and the replicate schedule plus
campaign inputs are tuple-backed or replayed against authority; neither path
supplied a silent-drift counterexample. The live mismatch was shared by Task,
Check, and Agent records: an integer ID passed its public validator but the
latest-schema loader rejected the serialized line. Public record validation now
runs its existing semantic checks and then reuses the existing dataclass schema
conversion. Domain-specific errors remain visible, and a validator cannot
approve the reproduced non-reloadable scalar shapes. Three red specs and the
full suite of 766 tests with 2 skipped pass. No deep-freeze utility, schema
registry, record wrapper, network access, or paid call was added. The 38-file
full-signal scan remains at 112 hotspots (0 now / 36 soon / 76 monitor), with
full signal health and no dead-code candidate.
A seventy-seventh closes the one top-level persisted record not covered by the
shared validator/schema rule. A self-digested `TaskPoolRecord` with an integer
generator-config digest passed the complete artifact validator although its own
JSONL schema rejected it. Records now owns the Task Pool record's required
shape, latest-schema replay, and self-digest check; Task Pool member validation
calls that function and removes its duplicate digest branch. One red bundle
case and all 64 then-current Task Pool tests pass.
A seventy-eighth removes coercive candidate ingestion. History and import
payloads now require string identity, task, availability, Check, cluster, and
stratum fields; solver refs must be a string sequence, and resource limits must
be a mapping with string keys. The default candidate ID is derived only after
these fields are validated. Excluded SourceEvents use the same cluster/stratum
rule, so an out-of-window item cannot bypass it. Nine red ingress cases and all
73 Task Pool tests pass. The full suite passes 776 tests with 2 skipped. No
candidate schema class, ingestion service, compatibility mode, network access,
or paid call was added. The 38-file full-signal scan remains at 112 hotspots (0
now / 36 soon / 76 monitor), full signal health, and no dead-code candidate.
A seventy-ninth closes Selector parameter identity normalization. Continuous
stratified-forecast parameters accepted integer and float forms with identical
execution but different config and Selector digests, while nested group maps
remained aliased to caller-owned dictionaries. The existing algorithm-specific
parameter parsers now produce one canonical snapshot before identity is
derived. Numeric weights are stored as floats, nested maps are copied in stable
key order, and an externally supplied executable Selector must already have
that canonical shape. Three red public specs and all 166 Selection tests pass.
No Selector-config class, registry, generic deep-freeze utility, or training
framework was added.
An eightieth removes Task Pool metadata coercion. `freeze_task_pool` no longer
turns repository IDs, artifact refs, config digests, timestamps, or an optional
Task Pool ID into strings. Its existing metadata preflight requires each
persisted field to be a string before Task/Check validation or identity
construction. Nine red public cases and all 82 Task Pool tests pass. The full
suite then passed 788 tests with 2 skipped; no schema, metadata object,
compatibility mode, network access, paid call, or campaign authority was added.
An eighty-first closes the remaining rule-mixture weight equivalence. The
algorithm divides every expert weight by their total, so overall scaling,
omitted zero experts, explicit zero experts, and signed zero had identical
ranking behavior but different Selector identities. Construction now stores all
three experts as built-in floats on a canonical unit simplex; a one-ULP
correction makes normalization idempotent under `fsum`. External executable
records must already use the complete scale-free form; signed-zero spelling is
now equivalent through the shared canonical JSON rule from the eighty-sixth
slice. Two rejection cases, one signed-zero identity case, the fitted-trainer spec,
10,000 deterministic randomized idempotence probes, and all 169 Selection tests
pass. The algorithm family, trainer boundary, and record schema remain intact.
An eighty-second completes signed-zero scoring normalization. `-0.0` and `0.0`
rates produce the same cost but previously different scoring digests. The
existing rate constructor now stores either spelling as positive `0.0`; one red
public case and all 65 Result Store tests pass. The full suite passes 792 tests
with 2 skipped. No pricing schema, registry, dependency, network access, paid
call, or campaign authority was added. The final 38-file full-signal scan stays
at 112 hotspots (0 now / 36 soon / 76 monitor), with critical counts 0/19/0 and
no dead-code candidate; the new numeric helpers do not enter the hotspot list.
An eighty-third closes a Task Pool timestamp failure path. A self-digested pool
with integer `created_at` first produced the correct latest-schema error, then
artifact reconciliation passed the same value to the shared UTC parser and
raised `AttributeError`. `parse_utc_timestamp` now rejects every non-string as
`ValueError`, preserving the public error-returning validator contract without
adding Task Pool-specific exception branches.
An eighty-fourth makes the existing latest-schema conversion the first public
record-validation gate. It previously ran only after domain semantics, so
malformed strings, containers, and nested records could raise before the gate.
The conversion now runs once during initial validation and invalid shapes return
immediately; the duplicate final replay was removed. Three representative red
cases cover string, sequence, and nested-record fields. A deterministic
one-field disturbance audit over all 16 public record validators and 256 fields
reports zero base failures and zero exceptions. No validator framework, schema
registry, compatibility mode, network access, paid call, or campaign authority
was added. The refreshed 38-file full-signal scan remains at 112 hotspots (0
now / 36 soon / 76 monitor), critical counts 0/19/0, and no dead-code candidate.
An eighty-fifth makes Task Pool artifact-validation prerequisites explicit. A
schema-invalid `rejected_candidate_ids` value was reported by Records but then
iterated by SourceEvent coverage, raising `TypeError`. Task Pool member
validation now stops when the pool record is invalid, and complete artifact
validation stops when the record/member layer is invalid; certification and
SourceEvent reconciliation run only on their declared prerequisites. One red
public bundle case and a deterministic disturbance of all 20 Task Pool record
fields report zero exceptions. No per-field catch, validation framework, or
new artifact layer was added. The refreshed 38-file full-signal scan remains at
112 hotspots (0 now / 36 soon / 76 monitor), critical counts 0/19/0, and no
dead-code candidate.
An eighty-sixth closes signed-zero identity at the shared canonical JSON
boundary. Result measurements and Metric values could use `-0.0`, compare equal
to `0.0`, pass validation, and still produce different JSON and self-digests.
`canonical_data` now emits every built-in floating zero as positive `0.0`, so
all records, nested feature/parameter JSON, writers, loaders, and digests share
one representation. Field validators and constructors do not duplicate the
rule; ScoringConfig retains its positive-zero in-memory snapshot. One red
canonical serialization/digest case plus direct Result/Metric probes pass. The
refreshed 38-file full-signal scan remains at 112 hotspots (0 now / 36 soon / 76
monitor), critical counts 0/19/0, and no dead-code candidate.
An eighty-seventh makes Task/Check record validity the first Task Pool member
gate. Member validation previously computed linkage before calling the existing
record validators, so integer `TaskRecord.check_ids` raised during iteration.
The existing accepted-record check now validates each record before repository,
digest, ID, or linkage relations; an invalid member returns immediately. One
red public bundle case and a deterministic disturbance of all 21 Task/Check
fields report zero exceptions. No member wrapper, schema copy, or catch list was
added. The refreshed 38-file full-signal scan remains at 112 hotspots (0 now /
36 soon / 76 monitor), critical counts 0/19/0, and no dead-code candidate.
An eighty-eighth closes ResultQuery's state-dependent input behavior. A numeric
filter returned an empty result against an absent store but raised `TypeError`
after the same store gained a Result; empty timestamps silently meant unbounded,
and inverted bounds silently returned no matches. `load_results` now validates
all six filter tuples, explicit nullable timestamp shapes, UTC parsing, and
bound order before checking store existence. Eleven red public cases and all 76
Result Store tests pass. No query schema, normalization object, or index was
added. An initial combined implementation created one monitor-only structural
hotspot; separating direct filter validation from timestamp parsing returns the
38-file full-signal scan to 112 hotspots (0 now / 36 soon / 76 monitor),
critical counts 0/19/0, and no dead-code candidate.
An eighty-ninth makes Result construction prove all four input records before
relations. `build_result_record` previously validated only WorkspaceRun; nine
schema-invalid Task/Check fields were accepted when they did not alter cache
projection, and integer `TaskRecord.check_ids` raised during linkage. It now
reuses the Task, Check, Agent, and WorkspaceRun validators before linkage or
cache-identity checks. Five red public cases and a deterministic disturbance of
all 52 input fields report zero accepted invalid inputs and zero leaked
exceptions. No Result-input wrapper or duplicate schema was added. The
refreshed 38-file full-signal scan remains at 112 hotspots (0 now / 36 soon / 76
monitor), critical counts 0/19/0, and no dead-code candidate.
A ninetieth slice applies the same prerequisite at exact cache-identity
construction.
`compute_result_cache_identity` is called directly by missing-cell and reuse
planning, so it cannot rely on later Result construction. A deterministic
disturbance of all 36 Task/Check/Agent fields initially found 15 schema-invalid
values accepted and one `TypeError` from integer `TaskRecord.check_ids`. The
compute and build paths now share one direct three-record validator, and the
existing Task/Check relation has one shared check before identity construction.
Four red public cases and the repeated disturbance report zero accepted invalid
inputs and zero leaked exceptions. All 85 Result Store tests and the full suite
of 819 tests with 2 skipped pass. No input wrapper, copied schema, validation
framework, network access, paid call, or campaign authority was added. The
refreshed 38-file full-signal scan remains at 112 hotspots (0 now / 36 soon / 76
monitor), critical counts 0/19/0, and no dead-code candidate.
A ninety-first slice closes the remaining exact cache-identity input shapes.
WorkspaceConfig and RuntimeConfig had no shared validators; six schema-invalid
fields absent from direct identity projection still produced valid-looking
identities, and an empty hardware digest was accepted beside null or a real
digest. Records now owns two direct validators that reuse the latest-schema
conversion and require nonempty identity strings, a positive integer timeout,
and a null or nonempty hardware digest. Result Store applies them before
identity construction. Six red public cases and 13 deterministic type/semantic
disturbances report zero accepted invalid inputs and zero leaked exceptions.
All 91 Result Store tests and the full suite of 825 tests with 2 skipped pass.
No config wrapper, schema copy, validation framework, network access, paid call,
or campaign authority was added. The refreshed 38-file full-signal scan remains
at 112 hotspots (0 now / 36 soon / 76 monitor), critical counts 0/19/0, and no
dead-code candidate.
A ninety-second slice applies the shared config prerequisite to Task Pool
certification. `certify_task_candidate` previously ran its first base Check
before validating either config, then wrote both config digests into
certification evidence. Invalid config IDs could therefore enter evidence even
though Result Store rejected the same objects. Certification now validates both
configs before Task/Check construction or Check execution. Two red public cases
prove that no Check call occurs; all 87 Task Pool tests pass.
A ninety-third slice applies the same prerequisite at Workspace's execution
preflight. Invalid config IDs passed `preflight_run_bindings`, including with an
empty plan, while Workspace hand-coded only the Runtime timeout constraint.
Preflight now validates both complete configs before repository or plan state;
Runner reuses `validate_runtime_config` instead of repeating its timeout type
branches. Two red public cases and all 74 Workspace tests pass. The full suite
passes 829 tests with 2 skipped. No config wrapper, execution context, schema
copy, network access, paid call, or campaign authority was added. The refreshed
38-file full-signal scan remains at 112 hotspots (0 now / 36 soon / 76 monitor),
critical counts 0/19/0, and no dead-code candidate; `_run_agent_cells` loses two
Lizard branches while remaining an explicit orchestration surface.
A ninety-fourth slice aligns Workspace repository binding with its Agent and
Check peers. `bind_repository_source` accepted an invalid WorkspaceConfig and
stored a source under one of its fields before later preflight rejected the
same object. It now validates before creating the immutable context binding; one
red public case and all 75 Workspace tests pass. Preflight still revalidates
before execution.
A ninety-fifth slice moves the same pair of config checks to Runner's Task Pool
batch boundary. `build_task_pool` previously resolved candidates and commits,
then repeated config validation once per certification candidate. It now fails
before candidate resolution while Task Pool retains the just-in-time check
before each Check execution. Two red public cases and all 58 Runner tests pass.
The full suite passes 832 tests with 2 skipped. No TaskPoolConfig wrapper,
generic preflight framework, network access, paid call, or campaign authority
was added. The refreshed 38-file full-signal scan remains at 112 hotspots (0 now
/ 36 soon / 76 monitor), critical counts 0/19/0, and no dead-code candidate.
Certification-evidence characterization now also covers malformed records,
non-boolean acceptance, duplicate candidates and accepted pairs, and a
certification-config mismatch without splitting the cross-record reconciler.
Empirical MAE, interval calibration, and run-variation comparisons still
require a newly authorized paid evidence run.
ALG-001 now has an offline `SafeSwitchConfig` and paired-evidence chooser. It
shrinks candidate improvement toward the fallback and applies minimum-history,
margin, and standard-error gates. It is not a Runner default and has no
empirical outer-origin win claim; tune it only inside nested rolling origins.
ALG-002 now has an offline `stratified_forecast` rule family. It reads only the
frozen `task_stratum` FeatureRecords, estimates the next mix from a declared
trailing Task/Check window with symmetric Dirichlet smoothing, uses
capacity-constrained largest-remainder quotas, and writes optional capped
post-stratification weights into the existing Benchmark Selection field. The
existing MAE scorer consumes those weights. A replay-checked diagnostic reports
forecast, unweighted-selection, and weighted-selection TV error plus effective
sample size and cap activation. No Record schema, generic trainer, Runner
default, report claim, network call, or empirical advantage was added. Tune
alpha, lookback, cap, and seed only inside nested rolling-origin history and
compare against the declared baselines before promotion.
ALG-003 now has an offline ten-point thirds-simplex rank-mixture grid and a
one-standard-error chooser. Every grid point is an ordinary executable
`rule_mixture` and must be evaluated through the existing paired
Selection/Metric/future-matrix chain; do not estimate mixture loss by averaging
the three expert losses. With enough prior Origins, the chooser finds the
lowest mean-MAE point and then selects the point closest to equal weights whose
mean is within one sample standard error of that best point. Short history
returns equal weights. This is not a replacement for the current inverse-MAE
trainer or a Runner default, and it has no outer-origin gain claim.
ALG-004 now has an offline drift-aware chooser. It validates complete paired
MAE evidence, validates the supplied training and deployment Rolling Origins,
rejects training cutoffs or label-maturity boundaries after deployment, orders
rows by the materialized `as_of_cutoff`, and ranks Selectors by an exponentially
weighted mean with a declared half-life. A non-fallback candidate is returned
only if
that same candidate also clears ALG-001's unweighted full-history safe-switch
gate. This deliberately does not invent a weighted confidence interval. The
default half-life of two Origins and the comparison grid 0.5/1/2/4 are
predeclared starting points for nested rolling-origin evaluation, not empirical
defaults. It is not a Runner default and has no outer-origin gain claim.
ALG-005 remains deferred. Current records already preserve the resource and
availability evidence needed by a future direct implementation; the missing
piece is a predeclared estimand. Do not add a ResourceMetric, prediction service,
or generic resource trainer until outer evidence identifies a material problem
and chooses among per-Cell p90, whole-Selection total, and bounded-concurrency
wall time. Cost studies must also freeze one pricing view.
`docs/implementation-status.md` records which effects the alpha implementation
enforces.

Selector, Benchmark Selection, and Metric logs retain stable semantic IDs. A
resume reuses the first persisted record only when all fields except the
observation timestamp and self-digest are identical, and Runner passes that
exact record downstream. A same-ID change to behavior or provenance remains an
error; do not turn resumes into duplicate timestamped events.

The fixed real-task Pylint pilot is complete. It observed one high-only pass
among ten single-run low/high pairs, which is too sparse to separate a
reasoning-effort effect from run-level variation or train a controller. Its
hindsight per-task oracle tied always-high at 5/10, so it did not demonstrate
an adaptive accuracy gain. The next outcome-facing step is a larger paired
history followed by rolling-origin MAE comparisons, not another controller
schema or framework.

Complexity is justified when it can improve prediction, prevent invalid
evidence, or preserve reusable paid results. Do not add aliases for existing
concepts, uncommon names for standard methods, unused identity fields, or
frameworks without a current caller.

Reports support Task Pool coverage only after loading the referenced Task,
Check, and certification-evidence files, validating Task/Check semantics, and
matching complete base-fail/reference-patch-pass evidence to every accepted
Task/Check and rejected candidate. Reports also recompute current aggregate
Selector metrics from their bound matrices before supporting metric claims.
Selector performance additionally requires the persisted
Selector→RollingOrigin→FeatureSnapshot→SelectorInput→Benchmark Selection→cell
set→matrix→metric chain, exact Agent/Result bindings, and deterministic Selector
replay. Mode-specific report claims prevent counterfactual replay from being
described as prospective evidence.
Persisted Selector inputs must retain the complete rolling-history denominator;
benchmark infrastructure failures stop certification instead of shrinking it,
and selection metrics abstain if exclusions leave any Agent without results.
Post-diff Check launch and invalid-exit failures are Agent-owned only when the
captured diff changed a workspace-relative path named by the Check command.
Certification evidence binds Workspace and Runtime config digests, the exact
Check command plus hidden destination/tree, and the built-in verifier adapter.
Hidden material uses one canonical tree digest over path, entry type, content,
and executable bits; symlinks fail closed. Injection creates a previously absent
reserved namespace and destination, never merges, and rehashes the copy.
Runner rejects invalid Result cache identities and scoring configuration before
invoking an Agent. For missing cells it validates the entire plan before the
first Agent call. Repository, Agent harness, and Check material bindings are
held in an immutable `WorkspaceRunContext`; bind functions return a new context
and reject conflicting rebinds within one context. Workspace then rechecks those
bindings,
positive runtime and Check timeouts, harness command/content, and the OpenAI
endpoint proof before workspace creation and immediately before invocation.
Only `OPENAI_BASE_URL` and `OPENAI_API_KEY` satisfy the paid mode; the key and
raw URL are never persisted. Cache-only and repricing operations do not require
current credentials. Workspace rejects invalid artifact configuration before
the same boundary; post-execution artifact I/O failures warn without replacing
the completed run record.

A 2026-07-23 audit found the endpoint/harness preflight complete but reproduced
a separate cost-authority gap: any positive remaining balance formerly allowed
another call, so the total estimate could be exceeded before the Result exposed
its cost. Campaign ledger v2 binds one maximum estimated cost per call, requires
the remaining total budget to cover that amount before reservation, and rejects
a returned Result above the per-call or cumulative limit. Its exact call cap is
derived from the frozen schedule instead of supplied again by the caller. This
is an estimated-cost reservation, not a provider billing guarantee; choose the
limit from an Agent runtime budget that actually bounds the call. The campaign
still matches the current endpoint to authority and preflights every remaining
Runtime slot. Workspace rechecks the selected cell before creating its solver
workspace and revalidates model scope, endpoint, command, and harness content
immediately before invocation. Do not add a lock for hypothetical in-process
environment mutation under the current single-writer execution model; revisit
only with bounded concurrent execution or another adapter that can mutate
credentials or harness files concurrently.

Result Store Runner operations hold one POSIX advisory write lock and one live
in-memory index across missing-cell resolution, Agent execution, repricing, and
final cell resolution. Each newly produced Result is flushed and fsynced before
the next paid cell. Readers take a shared lock. A non-newline-terminated tail is
an explicit load error; `recover_result_store_tail` may complete a parseable
JSON value or truncate only an unparseable final byte tail. It never removes a
complete line. Do not bypass this path with ad hoc JSONL appends.

The default runtime target is a cooperative Agent. Fresh workspaces, diff
replay, and verifier-only hidden material are required benchmark behavior.
Filesystem, network, process, CPU, and memory limits are optional adapter
requirements for adversarial or shared-host execution.

Archived material is historical reference. It is not an active implementation
input and should not be imported without a specific review.

## Design Rules

- Design before implementation.
- Keep module boundaries direct and small.
- Keep the core data vocabulary to `Task`, `Check`, `Workspace`, `Result`,
  `Selector`, `RollingOrigin`, `Task Pool`, `Benchmark Selection`, and
  `Agent Results`.
- Use the current module vocabulary: `Records`, `Task Pool`, `Verification`,
  `Workspace`, `Result Store`, `Selection`, `Reporting`, and `Runner`.
- Prefer the current module vocabulary; avoid alternate module names.
- Do not introduce a new first-class concept when one of those terms is enough.
- Every design document must include a source-alignment check against the
  architecture document.
- Module-level design should define function names, inputs, outputs, and
  effects, but not implementation bodies.
- Later module documents may refine earlier system documents. Update the
  affected documents instead of leaving contradictions.
- Design learned data and parameter contracts with a concrete algorithm. MAE is
  the current primary prediction objective.

## Schema And Result Preservation

Core code reads and writes only the latest schema. Do not keep runtime
compatibility branches for old records.

When a schema change affects valuable paid results, preserve them with a small
one-off migration that validates the new records and leaves the source
untouched. Drop an old result only when it cannot be migrated without guessing
evidence. Stop extending the migration when it starts becoming a compatibility
framework.

Preserved does not mean exact-cache reusable. When Agent-visible task material
or repository-history boundaries change, keep the old paid record for analysis
instead of rewriting its execution identity without proof of equivalence.

## Design Review Stop Line

Future design review should only request document changes for gaps that can
break the trustworthy evidence chain. Continue fixing design docs when a gap
could cause:

- stale paid results to be reused;
- Selectors to see future results or future-derived features;
- Task, Check, or oracle mismatches;
- selected or future denominators to become unauditable;
- frozen selections, results, or metrics to be changed after the fact;
- reports to lose traceability to cell, matrix, or result evidence.

Do not continue expanding design docs only to make fields more complete, feature
provenance more detailed, reports more expressive, validators more exhaustive,
or schemas more strongly typed. Defer those refinements to implementation paths
that actually need them.

## Paid Calls

The user authorized up to USD 300 for the current paired rolling-origin
experiment. Use only:

```text
OPENAI_BASE_URL
OPENAI_API_KEY
```

Every new missing-cell paid harness must be bound with
`execution_mode="openai_paid"` and the files whose tested content enforces the
endpoint. `AgentRecord.network_policy_digest` is the canonical proof over the
normalized endpoint digest, command digest, and harness-content digest. Runner
preflights the complete missing-cell plan; direct Workspace callers must use the
same binding and cannot bypass it with an ad hoc command. Offline harnesses use
the literal network policy `offline`. Do not test the proof with a real request,
store a key or key digest, or add provider/auth registries before a concrete
non-OpenAI benchmark caller exists.

Every new replicate campaign authority must bind both the total estimated-cost
budget and one conservative maximum estimated cost per call. Do not reserve a
cell unless the remaining total covers that per-call amount. Treat a Result
above either limit as a stopped cell with no automatic retry. The reservation
does not enforce provider billing before usage is returned, so the declared
per-call amount must agree with a runtime budget enforced by the Agent harness.
Derive the paid-call cap from the frozen schedule; do not accept a second
caller-supplied copy.

Record the exact requested model separately from `model_snapshot_id`. Populate
the snapshot only with adapter evidence that it is immutable. Otherwise bind a
unique campaign ID and positive UTC window into Agent and Result cache identity;
paid preflight and just-in-time validation reject missing-cell execution outside
that window. A new campaign must use a new scope instead of reusing an alias-
based exact-cache identity.

The ignored protocol and exact resource ledger are under
`outputs/user-journeys/2026-07-15-openai-paired-rolling-origin/`. Estimate cost
with current OpenAI standard API prices, as explicitly approved by the user;
label it as an estimate because the gateway does not publish billing rates.
The ten-call, no-retry boltons mechanism experiment is complete: five certified
Task/Check cells for each of the `gpt-5.4-mini` low- and high-reasoning Agent
configurations. All ten Results were scoreable; nine passed and one failed.
Official-price estimated cost was USD 0.35245695. The held-out origin 2 rule
mixture MAE was 0.00, tying coverage and random and beating recency at 0.25.
This is mechanism evidence only because the five tasks and availability times
are controlled. The sanitized report is
`docs/boltons-paired-mae-mechanism.md`.

The v1 paid diffs retained generated Python caches. Preserve those Results
unchanged. Commit `c052addc` excludes `.pytest_cache` and `__pycache__` from
future captured diffs and binds examples to adapter v2. The next predictive
experiment needs a larger Task Pool with multiple future tasks per origin.

The fixed Pylint pilot used real availability times and executable SWE-bench
`FAIL_TO_PASS`/`PASS_TO_PASS` certification. The first transport-aborted attempt
is preserved under its ignored output directory: one known-cost Result used
USD 0.13451550 and one interrupted Result has unknown usage and cost. The
replacement matrix restored Codex CLI default transport retries and completed
20/20 scoreable cells for USD 2.46819345 estimated at official prices. Low
passed 4/10; high passed 5/10; the only disagreement was high-only. The
sanitized report is `docs/pylint-swe-bench-reasoning-pilot.md`.

Future Pylint pools use a semantic Check manifest that excludes ignored output
directories and local harness paths while retaining the check implementation,
SWE-bench revision, verifier image, timeout, and hidden-oracle digest. The
exact runtime command is still checked before execution. Current paid Results
keep their original identities and remain loadable from their original output
directory; do not rewrite them to claim equivalence.

Known authorized spend across the boltons mechanism run and both Pylint
attempts is USD 2.95516590. Keep the interrupted Pylint cell's cost unknown; do
not subtract a guessed zero from the USD 300 authorization.

Repository-maintenance Codex sessions used to implement, review, or coordinate
work are outside this paid-call boundary. Reviewer Codex CLI sessions should
use the user's local Codex CLI authentication/subscription unless the user
explicitly requests a different reviewer execution mode.

## Local Experiment Time Estimates

Estimate task supply, deterministic certification, preflight, paid execution,
and analysis separately. Record active wall time for each phase and exclude
user pauses or known network outages instead of folding them into throughput.

For a serial paid matrix, wait for at least three scoreable cells per Agent
configuration, then estimate remaining wall time as:

```text
overhead factor * sum(remaining cells for config * observed mean workspace seconds for config)
```

Use `result time span / summed workspace seconds` as the overhead factor. This
pilot observed 1.009; use 1.02 for the same local serial runner until a later
run replaces it. Low averaged 67.77 seconds and high averaged 148.44 seconds,
so the observed pair mean was 216.21 seconds. At that rate, 30 paired tasks take
about 1.8 paid hours and 50 take about 3.0, before setup and analysis.

Do not extrapolate research and task-source repair from warm recertification.
The first ten-task supply pass took 81 minutes 6 seconds because it included
source research, a rejected task, an architecture probe, and repository repair.
Rebuilding the same fixed ten tasks from warm local inputs took 7 minutes 34
seconds; preflight took 3 seconds. State which case an estimate uses.
