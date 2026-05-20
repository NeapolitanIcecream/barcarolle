# Post-Pilot-008 Option C No-Model Spike

status: no_model_spike_completed
updated: 2026-05-06T23:51:30+08:00
related_decision: `.codex-workflows/core-narrative-experiment/decisions/post-pilot-008-transport-gate.md`
related_options_note: `experiments/core_narrative/reports/post_pilot_008_transport_options.md`

## Decision-Relevant Result

Option C is not a new live path yet. The repo already contains a direct
BARCAROLLE-env-only patch command, `experiments/core_narrative/tools/barcarolle_patch_command.py`,
which is materially different from the failed Codex CLI Responses streaming path
in pilots 006/007/008 because it:

- runs behind the same outer `acut_patch_adapter.py` budget/ledger/redaction wrapper;
- uses a direct HTTP request boundary instead of `codex exec`;
- defaults ordinary base URLs to a non-streaming `chat/completions` payload shape;
- supports `--dry-run` and `--mock-response*` modes that require no live BARCAROLLE model call;
- records prompt hashes and sizes, not prompt content.

This spike adds executable no-model specs for that direct command and for the
adapter-wrapped no-model path. It does **not** authorize a live model call.

## New Executable Evidence

Added `experiments/core_narrative/tools/test_barcarolle_patch_command.py`.

The tests specify that:

1. direct `--dry-run` works with both required BARCAROLLE env vars absent, prepares
   prompt metadata only, and records `model_call_made: false`;
2. live mode with missing env blocks before network with `network_attempted: false`;
3. direct `--mock-response-text` applies a unified diff without required BARCAROLLE
   env vars and records `model_call_made: false`;
4. URL-like mock response text passed as a CLI argument is rejected before parsing
   or workspace mutation;
5. the default direct transport shape resolves ordinary base URLs to
   `chat_completions`, uses a `messages` payload, and does not set streaming;
6. `acut_patch_adapter.py --command-no-model` can wrap `barcarolle_patch_command.py`
   in mock-response mode, append a zero-cost ledger record, emit a non-empty patch
   artifact, and preserve `model_call_made: false`.

Verification command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 experiments/core_narrative/tools/test_barcarolle_patch_command.py
# Ran 6 tests: OK
```

## Interaction With Existing Evidence

This does not erase the earlier direct-command live failures:

- pilots 001/002/003 used the direct `barcarolle_patch_command.py` path and still
  ended before verifier with redacted `LLM request failed` / `gaierror` outcomes;
- pilots 006/007/008 used the Codex CLI Responses streaming path and ended before
  verifier across treatment/model-tier axes, with pilot 008 classified as
  `responses_streaming_disconnect`.

So the current evidence says there are two different blocked live paths, not a
scoreable ACUT capability result:

- direct non-streaming command path: prior redacted `gaierror` failures;
- Codex CLI Responses streaming path: treatment/model-tier-independent streaming
  or nonzero pre-verifier failures.

## Gate Implication

The next safe action is review, not execution. Before proposing any future live
probe, the coordinator must record why the proposal is not merely a repeat of
both known failure families:

- not another pilots 006/007/008 Codex CLI Responses streaming attempt;
- not another pilots 001/002/003 direct-command `gaierror` attempt without a new
  operational readiness signal.

A future one-run probe would need the existing post-pilot-008 gate plus a fresh
no-secret operational preflight showing at minimum: env var presence only,
ledger parse/writability/cumulative cost, default direct transport kind, and a
reason the prior direct-command `gaierror` condition is plausibly resolved or
materially diagnosed. Broad execution, retries, second attempts, additional
specialist runs, further pilots, and large batches remain unauthorized.

## Budget

No live/model/API calls were made by this spike. Budget used: USD `0.00`.
