# Pylint SWE-bench reasoning-effort pilot

Date: 2026-07-17

## Outcome

All 20 fixed Agent/Task/Check executions were scoreable. Low reasoning passed
4 of 10 tasks; high reasoning passed 5 of 10. The configurations disagreed on
one task: high passed `pylint-dev__pylint-6386` and low failed it. There were no
low-only passes.

The two configurations produced different outcomes on one real task. Because
each cell ran once, the experiment does not separate a reasoning-effort effect
from run-level stochasticity. It is not evidence that high reasoning is
generally better, and it does not measure Selector MAE. One discordant pair is
not enough to train or evaluate a task-level meta-controller.

A hindsight oracle that chose the better configuration per task would also
pass 5 of 10, exactly matching always-high, because there was no low-only pass.
The pilot therefore shows no observed accuracy gain from adaptive selection
over always-high. It shows only a possible way to retain those five passes
while using low reasoning on tasks where high added no observed benefit; that
policy was not predicted or evaluated here.

## Protocol

- Tasks: nine instances from SWE-bench Verified and one from SWE-bench Lite,
  all from `pylint-dev/pylint` with source-derived availability times.
- Task certification: every base commit failed all `FAIL_TO_PASS` tests while
  passing all `PASS_TO_PASS` tests; every reference patch passed both sets.
- Agent: Codex CLI 0.144.5 with `gpt-5.4-mini`, once with `low` reasoning and
  once with `high` reasoning.
- Runtime: 900-second cell timeout, Codex CLI default request and stream
  retries, no whole-cell retry, plugins and subagents disabled.
- Verification: the Agent edited a fresh checkout; its diff was replayed in a
  separate verifier checkout before private SWE-bench checks were injected.
- Order: low then high for each task, executed serially.
- Task Pool: `task_pool_f6fbb38063a1f76e94d58af20ae6a70a1acd1ac4d9ea3ef5213d9580f2a58146`.
- Agent manifests: low
  `94ba7c9c1058a8c9054d6c1bcf0c231d15d251856e8655d75ae5369fab0c56e3`;
  high
  `f47d51aa2d5a76cb4d2b11c5138b61c2bd4af2debcd901ccd669aaa879c7fa5d`.

## Agent results

| Instance | Difficulty | Low | High |
| --- | --- | ---: | ---: |
| `pylint-dev__pylint-4551` | 1-4 hours | fail | fail |
| `pylint-dev__pylint-4604` | 15 min - 1 hour | fail | fail |
| `pylint-dev__pylint-4661` | 15 min - 1 hour | fail | fail |
| `pylint-dev__pylint-4970` | <15 min fix | fail | fail |
| `pylint-dev__pylint-5859` | not rated | pass | pass |
| `pylint-dev__pylint-6386` | 15 min - 1 hour | fail | pass |
| `pylint-dev__pylint-6528` | 15 min - 1 hour | pass | pass |
| `pylint-dev__pylint-6903` | <15 min fix | pass | pass |
| `pylint-dev__pylint-7080` | 15 min - 1 hour | fail | fail |
| `pylint-dev__pylint-7277` | <15 min fix | pass | pass |

| Configuration | Passes | Mean workspace latency | Median workspace latency | Uncached input | Cached input | Output | Estimated cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Low | 4/10 | 67.77 s | 62.20 s | 408,303 | 3,544,832 | 36,018 | $0.73417065 |
| High | 5/10 | 148.44 s | 138.49 s | 521,036 | 9,172,864 | 145,618 | $1.73402280 |
| Total | 9/20 | — | — | 929,339 | 12,717,696 | 181,636 | $2.46819345 |

High reasoning used 2.36 times the estimated cost and 2.19 times the workspace
time. Its one additional pass makes the observed pass-rate difference 0.10,
but the sample does not distinguish a stable configuration effect from task
sampling or single-run stochastic variation.

## Network correction

The first attempt explicitly set Codex request and stream retries to zero. Its
low canary completed, but the high cell ended on a stream disconnect. That
attempt remains unchanged under the ignored
`outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/` directory.
Its known estimated cost is $0.13451550; the interrupted high cell has unknown
usage and cost.

The completed matrix used a new output directory, ledger, Task Pool, Runtime,
and Agent manifests after removing the zero-retry overrides. It retained the
same ten task IDs, task material, oracle bundles, verifier images, and base
commits; the record identities changed with the runtime and output-bound Check
commands. All 20 streams then reached `turn.completed`; none reached terminal
`turn.failed`. This shows that the corrected protocol completed under the
observed network conditions. It does not isolate retry defaults as the cause,
because network conditions also changed between attempts. No recorded event
proves that an internal retry was needed, and external session resume was not
exercised.

After the run, the adapter was corrected so future Check manifests bind the
check implementation, SWE-bench revision, verifier image, hidden-bundle
destination, and timeout without binding local Python or raw-output paths. The
completed paid records retain their original identities and remain loadable
from the original output directory; they were not relabeled as equivalent to
the corrected identity.

## Evidence and cost integrity

- The completed ledger has 20 reservations and 20 matched completions. All 20
  Results are distinct, completed, and scoreable.
- Raw streams have 20 `thread.started` and 20 `turn.completed` events, with no
  terminal `turn.failed` event. Raw streams, workspaces, checks, and credentials
  remain under ignored paths.
- The official-price estimate uses [GPT-5.4 mini rates](https://developers.openai.com/api/docs/pricing#text-tokens)
  of $0.75/M uncached input, $0.075/M cached input, and $4.50/M output. The
  authorized gateway does not publish invoice rates, so cost remains an
  estimate.
- The completed matrix and the known-cost old canary total $2.60270895. The old
  interrupted cell remains unpriced rather than being treated as free.

## Claim boundary and next decision

The experiment covers one repository, ten fixed tasks, and the non-immutable
`gpt-5.4-mini` alias. Low always ran before high. It contains no rolling-origin
split, no learned predictions, and no held-out Selector comparison. Therefore
it supports only two design decisions:

1. Keep reasoning effort bound into Agent identity while testing whether the
   observed configuration difference repeats.
2. Do not claim an accuracy benefit for a controller from this pool: the
   hindsight per-task oracle tied always-high. Expand the paired real-task
   history before designing a learned controller. The next comparison should
   evaluate simple and learned selection rules on future origins with MAE,
   include always-low and always-high baselines, and use a repeated subset to
   estimate run-level variation.

Do not add a classifier or calibration schema from one discordant observation.
External resume remains a transport decision; this run did not require it.

The offline follow-up infrastructure is now available in
`examples/pylint_swe_bench_verified/replicate_schedule.py`. It freezes a
stratified repeated subset, seeded low/high order, exact Agent and Task Pool
bindings, campaign-scoped Runtime observation slots, and the full serial cell
plan before paid execution. Its resolver strictly replays the artifact, joins
each slot to exact Result identity, and returns at most the first missing slot
in frozen order. `replicate_campaign.py` adds the separate execution boundary:
`initialize_replicate_campaign_ledger` records explicit endpoint, model/Agent,
budget, call-cap, pricing, Workspace, Runtime, Task Pool, and schedule authority;
`preflight_replicate_campaign` validates every remaining Runtime slot; and
`run_next_replicate_campaign_cell` can execute only the first missing slot. It
reconciles a Result written before an interrupted completion event and forbids
automatic retry for stopped or result-less reservations. Creating the ledger
requires new authorization and never inherits the historical pilot's budget or
model window. No new replicate run or run-variation estimate has been produced.

### Concrete campaign entry point

`replicate_campaign_cli.py` turns the API into three explicit operations. It
does not generate a Task Pool, Agent configuration, Runtime configuration,
pricing decision, or authorization.

The campaign directory is an ignored local artifact root. By default it must
contain these frozen inputs:

- `records/agents.jsonl`;
- `records/runtime-config.jsonl`;
- `records/replicate-schedule.jsonl`.

The Agent records must use IDs ending in `-low` and `-high` and bind the exact
Codex command, model, reasoning effort, campaign-local Codex home, endpoint,
and harness content. The Runtime record must describe a budget enforced by the
actual harness. Generate the schedule with `replicate_schedule.py`; it must use
the same Agent and Runtime files. An unresolved model alias uses the schedule's
campaign ID and a positive execution window.

Set `OPENAI_BASE_URL` and `OPENAI_API_KEY`, then create authority with an
explicit budget and pricing decision:

```bash
uv run python examples/pylint_swe_bench_verified/replicate_campaign_cli.py \
  --pilot-output-dir "$PILOT_OUTPUT" \
  --campaign-dir "$CAMPAIGN_DIR" \
  authorize \
  --approved-at "$APPROVED_AT" \
  --scope "$CAMPAIGN_SCOPE" \
  --maximum-estimated-cost-usd "$TOTAL_BUDGET_USD" \
  --maximum-estimated-cost-per-call-usd "$PER_CALL_LIMIT_USD" \
  --pricing-version "$PRICING_VERSION" \
  --cost-rate "uncached_input_tokens=$UNCACHED_INPUT_RATE" \
  --cost-rate "cached_input_tokens=$CACHED_INPUT_RATE" \
  --cost-rate "output_tokens=$OUTPUT_RATE" \
  --pricing-source "$PRICING_SOURCE" \
  --accounting-basis "$ACCOUNTING_BASIS"
```

Authority creation writes `campaign-ledger.json` and makes no Agent call. The
next command replays the ledger, schedule, prepared Pylint evidence, current
endpoint, harness, repository, Check material, pinned verifier-image digest,
architecture and base commit, and every remaining Runtime slot:

```bash
uv run python examples/pylint_swe_bench_verified/replicate_campaign_cli.py \
  --pilot-output-dir "$PILOT_OUTPUT" \
  --campaign-dir "$CAMPAIGN_DIR" \
  preflight
```

Run one cell only after inspecting the JSON preflight summary:

```bash
uv run python examples/pylint_swe_bench_verified/replicate_campaign_cli.py \
  --pilot-output-dir "$PILOT_OUTPUT" \
  --campaign-dir "$CAMPAIGN_DIR" \
  run-next
```

Each invocation emits a bounded JSON summary. `run-next` never loops and
returns to `preflight` after recording one Result. All Agent, Runtime, schedule,
Result, and ledger paths must stay below `CAMPAIGN_DIR`. A missing ledger makes
`preflight` and `run-next` fail; neither operation creates authority.

Future preparation also writes
`records/dependency-evidence.jsonl`. The adapter derives exact changed-path
overlap edges from trusted certification-side reference patches, assigns
deterministic connected components, binds the artifact through Task Pool
generator identity, and replays it before paid stages. On the historical ten
patches, `pylint-dev__pylint-6528` and `pylint-dev__pylint-7080` form the only
non-singleton component because both change
`pylint/lint/expand_modules.py`. Absence of another overlap is not evidence of
independence. This post-run contract does not relabel the completed historical
Task Pool or paid Results.

The pilot's resource ledger now uses the shared examples-layer single-writer
event persistence also used by the boltons experiment. Its historical 2-call
interrupted ledger and 20-call completed ledger replay to the same calls, spent
cost, and remaining budget. Pylint-specific endpoint, pricing, scoreability,
and exact-Result checks remain in the pilot. Summary reconstruction filters to
the exact Task/Check/Agent/Workspace/Runtime identities of this pilot; results
from another Runtime slot cannot enter its rates or pairs. The summary is
`complete` only when all 20 exact Results and 20 completed ledger calls are
present.
