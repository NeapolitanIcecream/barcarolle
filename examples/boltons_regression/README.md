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

To run the same path as an opt-in integration test, set
`BARCAROLLE_BOLTONS_REPO` to that checkout before running
`tests/test_boltons_regression.py`. Unit tests always verify the five tracked
check and patch digests; they do not silently depend on an ignored local
checkout.
