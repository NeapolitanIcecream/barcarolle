# Codex CLI Transport Hardening

## Method and inputs

This was a no-model/static harness-hardening pass. I inspected the coordinator
and scoped worker process files, the Codex CLI inner patch command and tests,
the ACUT adapter only for a tight normalized-metadata integration guard, the
core subset run manifest as read-only planning context, and structured pilot
006/007 raw, normalized, and ledger artifacts.

No `cli.log` file was inspected. No ACUT attempt, live BARCAROLLE model call,
retry, second attempt, additional specialist run, broad execution, further
pilot attempt, large model-call batch, or cost-ledger append was started.

Local Codex CLI discovery used no-model commands only: `codex exec --help`,
`codex features list`, and `codex debug models --bundled`. Those surfaces did
not expose a documented non-streaming Responses transport switch for this
inner-command path. The reviewed command already uses the temporary provider
override with `wire_api="responses"` and a temporary model catalog.

## Structured evidence

Pilot 006 (`cheap-click-specialist` on `click__rbench__001`, attempt 1) used
route `openai/gpt-5.4-mini`, injected the reviewed Click specialist context
pack, made exactly one ledgered model-call attempt, and ended before verifier:

- adapter status: `command_failed`
- inner Codex CLI status: `codex_exec_failed`
- inner exit code: `1`
- timeout: `false`
- workspace patch: checked, zero bytes, no unsafe content, not usable
- failure capture: present, class `nonzero_exit`, `cli_log_inspected: false`
- structured stdout tail: five reconnect messages followed by a redacted
  Responses stream-disconnect message for the `/responses` path
- ledger: one `command_failed` record for the run id, cumulative estimate
  advanced to USD `18.0008`
- normalized result: absent for this older pre-normalization nonzero path

Pilot 007 (`cheap-generic-swe` on `click__rbench__001`, attempt 1) used the
same route and harness, excluded the Click specialist context pack as expected,
made exactly one ledgered model-call attempt, and ended before verifier with
the same transport shape:

- adapter status: `command_failed`
- normalized status: `infra_failed`
- inner Codex CLI status: `codex_exec_failed`
- inner exit code: `1`
- timeout: `false`
- workspace patch: checked, zero bytes, no unsafe content, not usable
- failure capture: present, class `nonzero_exit`, `cli_log_inspected: false`
- structured stdout tail: five reconnect messages followed by a redacted
  Responses stream-disconnect message for the `/responses` path
- ledger: one `command_failed` record for the run id, cumulative estimate
  advanced to USD `21.0008`

The shared failure is independent of the generic-vs-specialist treatment and is
not a scorable ACUT capability result.

## Mitigation implemented

Implemented a static transport-failure classifier in
`experiments/core_narrative/tools/codex_cli_patch_command.py`.

When the redacted Codex exec stdout/stderr contains a Responses
`stream disconnected before completion` failure for the `/responses` path, the
inner summary now emits:

- `transport_failure.present: true`
- `transport_failure.failure_class: responses_streaming_disconnect`
- `transport_failure.wire_api: responses`
- `transport_failure.endpoint_path: /responses`
- reconnect count and reconnect limit when present
- no message body, credential value, full URL, hostname, or IP content

The same class is used as `failure_capture.failure_class`, replacing the generic
`nonzero_exit` only for this known transport signature. Other nonzero exits,
timeouts, unsafe patches, and no-patch outcomes remain distinct.

Added a tight integration guard in
`experiments/core_narrative/tools/acut_patch_adapter.py`: when the command uses
the existing `--summary-output` path and that summary is from
`codex_cli_patch_command`, the adapter carries the inner failure class and
sanitized transport metadata into raw adapter output, future normalized
`infra_failed` metadata, and future ledger metadata. It does not change the
adapter status, ledger event, cost accounting, verifier policy, retry policy,
or primary-attempt policy.

## Next execution hypothesis

Before any later live ACUT attempt, a focused reviewer can now verify a
machine-readable distinction between generic `nonzero_exit` and the known
Responses streaming disconnect. If a later reviewed attempt still fails with
`responses_streaming_disconnect`, the coordinator has enough structured
evidence to treat it as a transport issue rather than spend repeated ACUT
budget on the same capability hypothesis.

This pass did not establish a safe non-streaming Codex CLI profile. A later
transport-profile change should require separate static discovery or external
documentation plus focused review before any live run.

## Verification

No-model/static checks run:

- `python3 experiments/core_narrative/tools/test_codex_cli_patch_command.py`
  passed, 5 tests.
- `python3 experiments/core_narrative/tools/test_acut_patch_adapter.py` passed,
  4 tests.
- `PYTHONPYCACHEPREFIX=/tmp/barcarolle-pycache python3 -m py_compile experiments/core_narrative/tools/codex_cli_patch_command.py experiments/core_narrative/tools/acut_patch_adapter.py`
  passed.
- `git diff --check` passed.
- Scoped no-secret scan over the 6 changed files passed with zero findings for
  exact required env values, bearer-token shapes, full URL shapes, IP address
  shapes, or hostname-shaped values after excluding source-syntax/file-extension
  false positives and model slugs.

## No-secret and redaction notes

The implemented classifier runs after existing stdout/stderr redaction and
records only structured booleans, class names, the non-secret endpoint path
`/responses`, and reconnect counts. It does not record credential values,
bearer tokens, resolved secrets, full base URLs, hostnames, or IP addresses.

The scoped artifact review excluded every `cli.log` path. The only inspected
failure text came from already-redacted structured JSON summaries and redacted
stdout/stderr artifacts referenced by those summaries.
