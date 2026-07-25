# 2026-07-25 Coding-Agent / Model Study

Status: active. The contract was frozen before paid execution; subsequent
changes are recorded as append-only amendments below.

## Research contract

### Decision to produce

Choose a small, auditable default portfolio of Codex CLI model configurations
for Barcarolle experiments and decide whether a single cached Result per
Agent×Task is empirically stable enough for current studies. The decision must
be supported by hidden-oracle Results, observed gateway accounting, latency,
and repeat executions. It is not a general model leaderboard.

### Scope and fixed boundaries

- Keep the coding-agent harness fixed to the repository's isolated Codex CLI
  adapter. Vary model and, where supported, reasoning effort. This separates
  model/configuration effects from harness effects.
- Use only solver-visible SWE-bench task text and a clean repository worktree.
  Score in a fresh verifier workspace with the pinned hidden check.
- Treat each requested model plus reasoning configuration as a distinct Agent.
- Treat a scoreable hidden-check pass as the primary task outcome. Also report
  scoreability, cost, token use, latency, and terminal/failure labels.
- The source/task population and sampling strata must be frozen before outcome
  inspection. Repository and dependency clusters are analysis units, not
  interchangeable independent observations.
- Results observed in 2026 are retrospective evidence for these tasks. They
  cannot be backdated into strict-prospective rolling origins or used to claim
  historical Selector MAE.
- Raw prompts, completions, workspaces, verifier output, credentials, and
  provider payloads stay below ignored `outputs/`. Only sanitized plans,
  summaries, schemas, digests, and reports may be committed.

### Required evidence

The sprint is complete only when it produces:

1. a replayable, certified Task Pool from an explicitly versioned classic
   source adapter;
2. a frozen candidate/configuration portfolio and an outcome-independent
   calibration/selection rule;
3. exact per-call Result records plus observed proxy-quota deltas and
   reconstructable token-price estimates;
4. a held-out or expanded main comparison with no outcome-driven cell
   additions;
5. repeat cells sufficient to estimate run-level outcome flips with a
   cluster-aware interval;
6. an adversarial audit of identity, oracle isolation, missingness, dependence,
   multiplicity, pricing, and claim scope; and
7. a decision report with supported conclusions, rejected hypotheses, exact
   limitations, and follow-up triggers.

### Insufficient outcomes

The following do not complete the study:

- a successful Responses API smoke test without coding and hidden verification;
- public-test success, patch plausibility, or an Agent self-report;
- ranking models only by raw pass count while ignoring paired tasks,
  scoreability, cost, latency, or dependency clusters;
- selecting the main sample or repeat cells after inspecting main outcomes;
- treating repeated executions as independent tasks;
- pricing from missing usage, an undocumented rate, or a provider balance
  snapshot without a before/after delta;
- spending the budget merely to exhaust it; or
- describing retrospective SWE-bench Results as prospective Selector evidence.

### Epistemic stance

Established before paid execution:

- The user authorizes at most USD 300 through `LLM_API_KEY` and
  `LLM_BASE_URL`.
- On 2026-07-25 the `LLM_*` and repository-standard `OPENAI_*` pairs had
  identical key and base-URL digests, so the existing paid harness can be used
  without changing the endpoint.
- The gateway reports quota in points with 500,000 points per USD. The hard
  sprint allowance is therefore 150,000,000 additional points from the frozen
  baseline.
- The current strict-prospective protocol forbids assigning newly observed
  Results to historical origins.

Working hypotheses, not conclusions:

- a cheap model may dominate expensive frontier models on cost-adjusted Pylint
  or SymPy tasks;
- provider-family diversity may produce useful task-level disagreement even
  when aggregate pass rates are close;
- at least one Agent×Task cell may flip under repeated execution, making
  replicate-aware experiment analysis useful;
- a single-repository pilot may not transfer to other repositories.

Allowed terminal states are: supported decision, supported rejection of the
candidate portfolio, or bounded inconclusive with the exact missing evidence.

### Resources and authority

- Monetary cap: USD 300, including every benchmark/evidence-producing model
  call launched by this sprint.
- Accounting guard: 150,000,000 quota points above baseline. The available
  endpoint reports global observed use but does not prove a provider-enforced
  per-study hard cap. A concurrent external use is conservatively charged to
  the sprint, and the local runner must retain a per-call reserve because a
  completed call can only be reconciled after it returns.
- Frozen baseline at `2026-07-25T13:44:44Z`:
  `total_used=707840389`, `total_available=792159611`.
- Reserve: at least USD 30 remains unallocated until calibration and Task Pool
  certification pass. The reserve covers bounded repeats or a predeclared
  recovery, not retries chosen by outcome.
- Local Docker/CPU/disk are not billed by this budget, but image availability,
  architecture, and base commit remain preflight gates.
- Provider metadata queries and this repository-maintenance Codex session are
  not counted as model calls. Every Responses call from the benchmark harness
  is counted.
- Current repository revision at contract freeze:
  `713c038ec0f889a30df27a47eb2b7c6e3827dbf8`.

### Failure model and audit checks

| Plausible failure | Required check |
| --- | --- |
| Harness silently uses a different endpoint or model | Bind endpoint, model request, Codex version, harness digest, and isolated home into each Agent identity; compare endpoint digest before every paid cell. |
| Proxy pricing and Result cost disagree | Freeze the pricing payload/version, retain token categories, and reconcile aggregate estimated cost against the observed quota delta. |
| Hidden oracle leaks into the solver | Inspect material bindings and artifacts; require the clean solver/fresh verifier split and no verifier refs in solver-visible files. |
| A failed verifier is counted as model failure | Require a fresh scored summary and separate benchmark-invalid from agent-invalid Results. |
| Calibration overfits the main comparison | Freeze candidate tasks, selection rule, main tasks, repeat cells, and stopping rules before their outcomes are inspected. |
| Nominal sample size overstates evidence | Report repository, dependency-cluster, Task, and repeat-cell counts; use paired and cluster-aware summaries. |
| Unfinished or stopped cells bias results | Publish all frozen cell states and reasons; do not silently replace cells or retry after a scored Result. |
| Historical tasks are presented as deployment evidence | Label source-conditional retrospective claims and keep Selector claims out of scope. |

## Adaptive experiment design

### Execution amendments

`study-amendment-1.json` was frozen after the first cells exposed a protocol
gate that the base plan had treated too coarsely:

- DeepSeek V4 Pro and Gemini 3.1 Pro were advertised by the proxy as OpenAI
  endpoint models, but Codex CLI could not complete a Responses stream. Their
  exact Agent-invalid Results are retained as harness/proxy compatibility
  evidence, not coding-capability evidence.
- A paired campaign cannot observe its second Agent after the first produces a
  non-scoreable Result. The amendment therefore adds a replayable
  single-Agent, single-Task, single-call schedule for mini and Claude. Hidden
  pass/fail does not affect protocol eligibility.
- Sol and Terra both produced scoreable first-block Results, so their original
  paired campaign continues unchanged.
- The two stopped campaign authorities are retired operationally. The canary
  authority reallocates unused calibration allowance and does not increase the
  USD 300 cap.

The first six scoreable frontier calls also established an accounting
correction. Immediate token-balance before/after deltas did not equal the quota
recorded for the same call because the global balance is eventually
consistent. Gateway token-log candidates selected by the bound model and
Result time exactly reproduced each Result's input and output token totals.
The study now uses:

- sanitized, token-matched log receipts for per-call quota attribution; and
- the eventual token balance only for the global guard and aggregate
  reconciliation.

The two management surfaces are documented separately by New API:
[`/api/log/token`](https://doc.newapi.pro/api/fei-log/) exposes token-key log
rows, while [`/api/usage/token`](https://doc.newapi.pro/api/token-usage/)
exposes the token's aggregate granted/used/remaining balance. The observed
eventual-consistency behavior is an empirical result of this gateway, not a
claim made by those documents.

One Terra Result was already durable when its immediate post-call balance
query returned HTTP 429. It was not retried. Its ten successful gateway log
rows reproduced all Result tokens and recovered 69,552 quota points; the
aggregate attributed log quota later equaled the global balance movement
exactly. Metadata queries now use bounded retry, and a missing post-call
balance does not erase an exact Result or its log receipt.

Repeated `/api/usage/token` requests then remained rate limited for more than
three minutes without a `Retry-After` or rate-limit header, while the exact
per-call token-log route remained available. Per-cell balance sampling was
therefore both operationally brittle and scientifically misleading. The
execution driver now takes one live global-balance checkpoint every six frozen
schedule cells, reuses an already-live snapshot for at most five minutes across
campaign boundaries, uses exact attributed token-log quota between
checkpoints, and defers the next global reconciliation instead of querying a
post-call balance. Six cells correspond to three paired Task blocks; five
minutes covers the observed greater-than-three-minute rate-limit window and
leaves the original per-call reserve in force. This cadence detects concurrent
external movement periodically; the endpoint still does not provide a
provider-enforced study-specific hard cap.

`study-amendment-2.json` was frozen after the complete frontier panel and both
single-Agent canaries:

- Sol and Terra each passed 5/10 Pylint base Tasks, disagreed on none, and
  reproduced one frozen pass and one frozen fail. Exact gateway receipts cost
  USD 6.013130 for Sol and USD 2.491162 for Terra, so Terra is the common
  control.
- GPT-5.4 mini completed the full protocol with priceable usage and a scoreable
  hidden failure. Claude Sonnet 4.6 returned an Agent-invalid Result with empty
  usage and zero attributed quota. Hidden outcome did not determine either
  eligibility decision.
- One 24-cell mini-versus-Terra panel is the only replacement calibration.
  Mini receives a canonical ten-Task/two-repeat view. Terra's repeated panel
  connects the graph and measures bridge variation but does not replace or
  double-weight its canonical frontier view.
- Main admission now separates an actual gateway p90 projection capped at USD
  180 from a USD 260 conservative campaign-ledger ceiling. The latter exists
  only because one shared ScoringConfig prices both Agents at the larger rate;
  it does not enlarge the USD 300 actual-spend cap or remove the USD 30 reserve.

The fifth replacement-panel Result was scoreable and durable before all of its
successful token-log rows were visible. The immediate receipt check therefore
stopped after the Result without rerunning it. Receipt acquisition now makes at
most six observations with bounded 1/2/4/8/16-second gaps and still accepts
only an exact input/output token match. Results are attributed in six-cell
batches from one snapshot: global balance checkpoints occur before cells
0/6/12/18, and receipt checkpoints after cells 5/11/17/23. Every pending call
reserves its full per-call quota ceiling, and the next block cannot start until
the prior block has exact receipts. A receipt-recovery pass uses the last live
balance checkpoint; the next receipt-complete pass refreshes the global
balance.

This cadence is also consistent with the observed gateway's reported
`v1.0.0-rc.4` source at commit `e8cfb546`: both the
[`/api/usage/token` route](https://github.com/QuantumNous/new-api/blob/e8cfb546fa7e1d5bf266c5998181c0021826e045/router/api-router.go#L274-L281)
and the
[`/api/log/token` route](https://github.com/QuantumNous/new-api/blob/e8cfb546fa7e1d5bf266c5998181c0021826e045/router/api-router.go#L310-L313)
use `CriticalRateLimit`. Its
[default configuration](https://github.com/QuantumNous/new-api/blob/e8cfb546fa7e1d5bf266c5998181c0021826e045/common/init.go#L121-L123)
is 20 requests per 1,200-second fixed window, though a deployment may override
both values. `/api/status` identifies the observed deployment as
`v1.0.0-rc.4`; that exact tag has the same route and default-window behavior.
The proxy did not return the `Retry-After` header present in current upstream
code, so the study treats the exact reset time as unknown and uses a full quiet
window rather than polling. The rc.4
[`TokenAuthReadOnly`](https://github.com/QuantumNous/new-api/blob/e8cfb546fa7e1d5bf266c5998181c0021826e045/middleware/auth.go#L214-L232)
authenticates from the `Authorization` header, so the client does not duplicate
the key in its query string.

The block size also respects log retention. Upstream
[`GetLogByTokenId`](https://github.com/QuantumNous/new-api/blob/e8cfb546fa7e1d5bf266c5998181c0021826e045/model/log.go#L69-L72)
returns at most
[`MaxRecentItems = 1000`](https://github.com/QuantumNous/new-api/blob/e8cfb546fa7e1d5bf266c5998181c0021826e045/common/constants.go#L61).
Across the first 32 exact or zero-usage receipts, one cell used at most 28
successful log rows (p90 22); six times the observed maximum is 168. This is
not a guarantee against unrelated traffic, so a missing exact token match
still stops the campaign rather than accepting a partial receipt.

The first recovery snapshot exposed a different shared-gateway hazard. Terra's
sixth replacement Result matched 12 candidate rows exactly, while mini's fifth
Result window contained 23 candidates totaling 562 input and 628 output tokens
more than the Result. This was an overlapping same-model call, not eventual
log incompleteness. Attribution now accepts all model/time candidates when
their totals match; otherwise it requires exactly one candidate-row subset to
reproduce both Result totals. The receipt records candidate and excluded
counts plus digests. A missing or non-unique subset remains an accounting stop.

### Route portfolio

| Route | Mechanism | First decisive test | Status / reopening rule |
| --- | --- | --- | --- |
| R1: fixed Pylint anchor | Reuse the already audited, certified ten-Task Pylint SWE-bench pool and compare diverse models on the same hidden checks. | All ten candidates certify; model canaries are scoreable and quota-accounted. | Frontier panel complete; one frozen mini-versus-Terra replacement panel remains. The proposed 15-Task union was not needed once the 75-Task SymPy route passed offline feasibility; changing the anchor after outcomes would weaken comparability. |
| R2: broader static classic source | Implement one explicit dataset-import adapter for a larger single-repository SWE-bench Verified slice, with pinned source and verifier manifests. | Package replay, base-fail/reference-pass certification, arm64 image/base binding, and disk/time feasibility. | Admitted: all 75 SymPy candidates passed 150 fresh base/reference checks in about 66 minutes, and the published 75-Task/54-cluster bundle reopens. Main calls remain gated on calibration selection and cost. |
| R3: repeatability-first | Run outcome-independent repeated cells and estimate pass/fail flip probability. | Two or three executions exist for every frozen repeat cell without replacement. | Mandatory analysis route. Promote replicate-aware core design only if the interval crosses the predeclared decision gates. |
| R4: retrospective Selector simulation | Reconstruct historical origins from newly generated Results. | Statistical-protocol audit. | Rejected: Result observation time makes it non-prospective. Reopen only with Results observed under a future authorized rolling campaign. |
| R5: multiple coding-agent harnesses | Compare Codex CLI with another coding-agent implementation. | Identity/isolation parity and a separately certified harness. | Deferred. It confounds model and harness in this sprint and no equally mature local adapter is installed. Reopen after the fixed-harness model decision. |

### Stages and allocation rules

1. **Offline admission.** Freeze source revisions, tasks, dependency strata,
   verifier image digests, candidate configs, price records, and the quota
   baseline. Certify every Task without an Agent call.
2. **Protocol canaries.** Run at most one predeclared Task per candidate. A
   candidate continues only if the call uses the bound Responses endpoint,
   emits priceable usage, returns a scoreable Result, and stays within its
   per-call ceiling.
3. **Calibration.** Run the frozen small paired panel. Choose the first main
   configuration by hidden-pass count, then observed cost. Choose the second
   from configurations whose pass count is no more than two Tasks below the
   best; maximize paired outcome disagreement with the first, then hidden-pass
   count, lower cost, and model-family diversity. Protocol/scoreability eligibility and a
   conservative complete-main-run budget bound precede both choices.
4. **Main comparison.** Before inspecting main outcomes, freeze the selected
   configurations, source/task set, cell order, repeat cells, and maximum
   calls. Expand only if certification and a conservative p90 cost projection
   leave the USD 30 reserve.
5. **Repeatability.** Repeat 20–30% of main Tasks two additional times for each
   selected Agent. The Task set is chosen deterministically from dependency
   clusters before main outcomes.
6. **Synthesis.** Reconcile Results, ledger events, proxy quota, and artifacts;
   run the failure-model audit; then publish the decision and remaining gap.

No outcome is an operational early-stop signal. Operational looks may stop only
for identity drift, unpriceable usage, missing exact Results, non-scoreable
Results, certification failure, or insufficient remaining budget for the next
predeclared block.

## Statistical decisions

- Primary model comparison: paired per-Task hidden pass/fail differences, with
  exact discordant counts and dependency-cluster bootstrap intervals. Cost and
  latency are co-primary operational measures; no scalar utility is invented.
- Repeatability estimand: \(R=P(Y_{r1}\ne Y_{r2})\). For three executions,
  retain the three pairwise disagreements but resample the Agent×Task cell as
  one cluster.
- If the upper 95% interval for \(R\) is at most 0.05, one cached Result is
  sufficiently stable for current experiment-layer comparisons. If the lower
  bound is at least 0.10, future comparisons must be replicate-aware. Otherwise
  retain repeat slots in the experiment layer and do not change the core
  Result/controller schema.
- Model superiority is claimed only for the frozen source population when a
  paired difference is supported and the operational trade-off is explicit.
  Otherwise the decision is a Pareto portfolio, not a universal winner.

## Exit gates

Stop with a supported report when all required evidence exists or when a
predeclared operational gate makes further calls unsafe or non-informative.
Stop immediately before another call if:

- observed gateway use reaches 150,000,000 points above baseline;
- the remaining authorized balance cannot cover the next frozen block plus
  reserve;
- endpoint, model identity, source, image, or harness binding drifts;
- usage cannot be priced or reconciled;
- a paid cell is benchmark-invalid or agent-invalid;
- fewer than 90% of the first 20 main cells are scoreable; or
- the larger-source route fails certification or feasibility.

The final report must state spent and remaining budget, every retired route,
the strongest supported conclusion, and the exact evidence still needed for
cross-repository or prospective-Selector claims.
