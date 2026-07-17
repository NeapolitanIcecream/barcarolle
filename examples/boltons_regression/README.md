# Boltons current-schema regression

This fixture reuses the five tasks, hidden checks, and known-good changes from
the 2026-07-01 controlled boltons journey. It now executes base-fail and
reference-pass certification before running a deterministic scripted Agent
through the normal Workspace and Result paths.

It is a real-target mechanism regression, not rolling-origin or predictive
validity evidence. It makes no LLM or other paid call.

Run it against a local boltons checkout that contains the pinned commit:

```sh
uv run python examples/boltons_regression/run.py \
  --target-repo /path/to/boltons \
  --output-dir outputs/user-journeys/boltons-current-schema-regression
```

Success means all five base checks failed, all five reference patches passed,
and all five scripted Agent Results passed. The summary is written to
`summary.json` under the output directory.

## Paired rolling-origin mechanism experiment

`paired_experiment.py` reuses the certified five-task fixture to compare two
fixed `gpt-5.4-mini` Agent configurations (`low` and `high` reasoning). It
freezes coverage, random, and recency selections for two origins, runs one
Agent/Task/Check cell per paid invocation, fits the rule mixture only from the
first origin, freezes its second-origin selection, and then evaluates the
second holdout.

The paid path requires an approved resource ledger plus `OPENAI_BASE_URL` and
`OPENAI_API_KEY`. Run the stages explicitly:

```sh
uv run python examples/boltons_regression/paired_experiment.py \
  --target-repo /path/to/boltons --output-dir /path/to/output --prepare-only
uv run python examples/boltons_regression/paired_experiment.py \
  --target-repo /path/to/boltons --output-dir /path/to/output --freeze-origin-one
uv run python examples/boltons_regression/paired_experiment.py \
  --target-repo /path/to/boltons --output-dir /path/to/output --canary
```

Inspect the canary Result, raw event artifact, usage, estimated cost, and ledger
before each `--next-cell`. After eight first-origin cells, run `--fit-mixture`;
then run the two second-origin cells and finish with `--evaluate`. The fit and
evaluation stages only read exact Results and cannot invoke the Agent.

This remains a mechanism experiment over five hand-authored tasks with
controlled availability times. Its report must not be presented as evidence
of real-world predictive validity. See the
[sanitized mechanism report](../../docs/boltons-paired-mae-mechanism.md) for the
completed 2026-07-15 run.

To run the same path as an opt-in integration test, set
`BARCAROLLE_BOLTONS_REPO` to that checkout before running
`tests/test_boltons_regression.py`. Unit tests always verify the five tracked
check and patch digests; they do not silently depend on an ignored local
checkout.
