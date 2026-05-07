# 2026-05-07 Restart Preflight and Transport Timeout Evidence

status: blocked_current_env_missing_no_paid_probe
updated: 2026-05-07T14:28:26+08:00
stage: preflight-and-plan
repo: `/Users/chenmohan/gits/barcarolle`
branch: `codex/core-narrative-experiment`
start_head: `ab539a4` (`Record pilot 010 structured direct timeout`)

## Inventory

- Branch matched expected `codex/core-narrative-experiment`.
- Latest HEAD at restart was `ab539a4` after `ab97157`.
- Pre-existing dirty file preserved and not staged: `docs/experiments/core-narrative-experiment-plan.md`.
  - The diff adds the LLM access/budget contract, `llm_access.yaml` references, cost-ledger references, and budget-constrained gates.
- Flow state remains non-scoreable: pilots `001`-`010` produced zero scoreable ACUT verifier results.
- Current committed ledger: `experiments/core_narrative/results/cost_ledger.jsonl` has 13 records and cumulative estimated spend USD `51.0008`, below the USD `240` soft stop and USD `300` hard cap.
- Latest failing run id: `pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1`.

## Pilot 010 Evidence Re-inventory

Artifacts inspected:

- Raw directory: `experiments/core_narrative/results/raw/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1/`
- Normalized result: `experiments/core_narrative/results/normalized/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1.json`
- Review report: `experiments/core_narrative/reports/2026-05-07_review_probe_direct_structured_contract.md`

Facts:

- Outer adapter command timeout was `300s`.
- Inner `barcarolle_patch_command.py` default HTTP timeout was `120s`.
- Observed command duration was `120.869s`, command exit code `2`, adapter status `command_failed`, normalized status `infra_failed`.
- Inner summary recorded `LLM request failed`, details `error_type: timeout`, `network_attempted: true`.
- No model response was recorded; no verifier-ready patch existed; `submission.patch` was 0 bytes; verifier did not run.
- Pilot 010 consumed one ledgered attempt with estimated cost USD `10.0`; cumulative estimated spend became USD `51.0008`.
- The historical pilot 010 summary was generated before the post-probe timeout classification hardening, so it says `failure_class: llm_request_failed` even though the structured details identify a timeout.

## Current No-Model / No-Secret Readiness Triage

New local artifacts:

- `experiments/core_narrative/results/raw/2026-05-07_restart_preflight_transport_timeout/budget_preflight_current_env.json`
- `experiments/core_narrative/results/raw/2026-05-07_restart_preflight_transport_timeout/direct_structured_dry_run_current_env.json`
- `experiments/core_narrative/results/raw/2026-05-07_restart_preflight_transport_timeout/static_request_profile.json`

Current shell preflight is blocked before any paid probe:

- `BARCAROLLE_LLM_API_KEY`: absent by name in the current worker environment.
- `BARCAROLLE_LLM_BASE_URL`: absent by name in the current worker environment.
- Ledger remains parseable and writable.
- Projecting another USD `10.0` attempt would yield cumulative estimated USD `61.0008`, still below both caps, but missing env blocks execution.
- No endpoint values, hostnames, IP addresses, bearer tokens, credential values, raw prompts, or private artifacts were recorded.

Dry-run request facts for the existing pilot 010 workspace:

- mode: `dry_run`; model call made: `false`.
- model route: `openai/gpt-5.5`.
- output contract: `structured-files-json-v1`.
- prompt content recorded: `false`; prompt char count: `3507`.

Static request-shape facts for the structured direct path, without network:

- route shape for default base URLs is non-streaming `chat_completions`.
- `response_format: {"type":"json_object"}` is requested for `structured-files-json-v1` chat-completions payloads.
- `stream` is not set.
- default inner HTTP timeout is `120s` and default response read cap is `2,000,000` bytes.
- The ACUT runtime budget records `max_tokens: 64000`, but the current direct payload does not pass `max_tokens`, `max_completion_tokens`, or `max_output_tokens` to the provider.

## Local No-Model Hardening Completed

`experiments/core_narrative/tools/barcarolle_patch_command.py` now records a safe request profile on live transport failures:

- `endpoint_kind` only, not endpoint values;
- output contract;
- whether JSON response format was requested;
- timeout seconds;
- max response bytes;
- request body byte count;
- prompt character count.

It also normalizes timeout-shaped transport exceptions to `error_type: timeout` and classifies `TimeoutError` / `socket.timeout` summaries as `llm_request_timed_out` without recording exception messages, hostnames, or URLs.

Regression coverage added in `experiments/core_narrative/tools/test_barcarolle_patch_command.py` confirms a mocked timeout records the safe request profile and does not persist the fake endpoint URL, fake hostname, or fake secret value.

## Timeout Interpretation

Likely ruled out:

- Outer adapter timeout: pilot 010 lasted `120.869s`, well below the outer `300s` timeout and aligned with the inner direct HTTP timeout.
- Patch parser / verifier issues: no model response body reached the parser and no verifier-ready patch existed.
- DNS/TCP/TLS as the immediate pilot 010 class: earlier route health and pilot 009 showed the direct path could reach a live model response; pilot 010 failed later, at response wait.
- Immediate `response_format` rejection: an unsupported parameter would more likely produce a prompt HTTP error than a near-exact 120s wait; not fully ruled out because the provider/gateway could hang on this shape.

Current best hypotheses:

1. The inner `120s` HTTP timeout is too short for `openai/gpt-5.5` on the strict JSON-files contract.
2. `structured-files-json-v1` plus JSON mode increases latency or contract pressure enough to exceed the current inner timeout.
3. The provider/gateway route accepts the request but stalls or does not stream/flush a final response before the urllib timeout.
4. The current direct payload lacks an explicit output-token cap despite the ACUT runtime budget saying `64000`, so the next paid probe should consider a reviewed explicit smaller cap or tighter output contract rather than another unbounded full-file JSON request.

## Evidence Pack for Voyager / GPT-5.5-Pro

Problem statement: Barcarolle still has zero scoreable ACUT patch-generation results. After prior direct transport reached a malformed patch response in pilot 009, the materially different strict structured-files direct path in pilot 010 timed out before any model response after `120.869s`, leaving no verifier-ready patch and no scoreable result.

Exact failing run ids:

- `pilot_009__frontier-generic-swe__click__rbench__001__attempt1`: direct path reached model response; generated unified diff failed `git apply --check`; no verifier.
- `pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1`: strict structured direct path timed out before response at the inner HTTP timeout; no verifier.

Observed evidence:

- pilot 010 raw adapter result: `experiments/core_narrative/results/raw/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1/adapter_result.json`
- pilot 010 inner summary: `experiments/core_narrative/results/raw/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1/patch_command_summary.json`
- pilot 010 normalized result: `experiments/core_narrative/results/normalized/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1.json`
- pilot 010 report: `experiments/core_narrative/reports/2026-05-07_review_probe_direct_structured_contract.md`
- current env gate: `experiments/core_narrative/results/raw/2026-05-07_restart_preflight_transport_timeout/budget_preflight_current_env.json`
- current static request profile: `experiments/core_narrative/results/raw/2026-05-07_restart_preflight_transport_timeout/static_request_profile.json`

Hypotheses ruled out / weakened:

- same-path Codex CLI Responses streaming churn, because pilot 010 used direct HTTP and not `codex exec` Responses streaming;
- malformed diff parser failure for pilot 010, because no model response was received;
- outer adapter timeout, because the failure aligned with the inner HTTP timeout;
- budget cap, because cumulative estimated spend remains below cap.

Current blockers:

- The current worker environment does not contain `BARCAROLLE_LLM_API_KEY` or `BARCAROLLE_LLM_BASE_URL`, so no paid probe can be started from this shell.
- Even after env is restored, repeating pilot 010 unchanged is not justified.

Exact decision needed:

Choose one next single paid probe shape after env restoration, and do not run more than one before stopping again:

1. reviewed inner timeout increase, e.g. strict structured path with `--http-timeout-seconds 300` or `600` and safe request-profile recording; or
2. reviewed smaller/tighter output shape, e.g. explicit output-token cap / compact JSON file edits if the target gateway supports the parameter; or
3. alternate direct transport path that avoids chat-completions JSON-mode hanging while preserving the BARCAROLLE env/redaction/ledger gates.

Recommended next bounded stage: restore required BARCAROLLE env in the worker context, rerun the no-secret budget gate, then run exactly one ledgered paid probe that is materially different from pilot 010. The lowest-risk choice from current evidence is a single strict structured-files direct probe with an explicit reviewed longer inner timeout and the newly added safe request-profile diagnostics; stop at one scoreable verifier result or one classified provider/path blocker.
