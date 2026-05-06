# Post-Pilot-008 Transport/Harness Gate

status: option_c_review_integrated_single_direct_probe_authorized
recorded_at: 2026-05-06T21:55:01+08:00
updated: 2026-05-07T01:00:00+08:00
owner: coordinator
related_status: `pilot_008_integrated_local_triage_recorded`

## Decision

Do not authorize another live BARCAROLLE ACUT patch-generation attempt on the current Codex CLI Responses streaming path.

Only no-model/static planning is authorized until the coordinator records reviewed evidence for an alternate patch-generation transport/harness, a materially different bounded output/transport profile, or an operational readiness criterion that is not another pilots 006/007/008 same-path repeat.

## Evidence

| Run | ACUT | Model route | Specialist context | Result | Failure class | Verifier-ready patch? | Scorable ACUT result? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pilot_006__cheap-click-specialist__click__rbench__001__attempt1` | `cheap-click-specialist` | `openai/gpt-5.4-mini` | injected | `command_failed` before verifier | `nonzero_exit` | no | no |
| `pilot_007__cheap-generic-swe__click__rbench__001__attempt1` | `cheap-generic-swe` | `openai/gpt-5.4-mini` | excluded | `command_failed` / normalized `infra_failed` before verifier | `nonzero_exit` | no | no |
| `pilot_008__frontier-generic-swe__click__rbench__001__attempt1` | `frontier-generic-swe` | `openai/gpt-5.5` | excluded | `command_failed` / normalized `infra_failed` before verifier | `responses_streaming_disconnect` | no | no |

The three reviewed attempts cross the relevant treatment and model-tier axes enough to conclude that the observed pre-verifier failure is independent of Click-specialist treatment and independent of cheap-vs-frontier tier within the current Codex CLI Responses streaming command path.

The cost ledger currently parses as JSONL with 11 records and cumulative estimated cost USD `31.0008`, below the USD `$240` soft stop and USD `$300` hard cap. Being below cap is not sufficient reason to spend more: further same-path attempts would consume budget without producing a new capability signal.

## Gate Before Any Future Live Call

A future live BARCAROLLE model call must stop for coordinator approval and record all of the following first:

1. Exact run id, ACUT, task, split, attempt, and whether specialist context is expected.
2. Why the run is not another current-path repeat of pilots 006/007/008 and, for direct-transport proposals, not another pilots 001/002/003 direct-command `gaierror` repeat.
3. Fresh no-secret env preflight: `BARCAROLLE_LLM_API_KEY` present and `BARCAROLLE_LLM_BASE_URL` present; values must not be printed or recorded.
4. Cost ledger parses and is writable; current cumulative cost, projected additional cost, and projected cumulative cost are below the USD `$240` soft stop and USD `$300` hard cap.
5. Reviewed no-model evidence for one of:
   - an alternate patch-generation transport/harness;
   - a bounded output/transport profile materially different from the failing Responses streaming path;
   - fallback behavior that can produce verifier-ready patches without weakening the 2x2 control contract.
6. Explicit statement that broad execution, retries, second attempts, additional specialist runs, further pilots, and large batches remain unauthorized unless separately named.

## Non-Decisions

- This record does not retire the 2x2 ACUT design.
- This record does not approve broad execution, retries, second attempts, additional specialist runs, further pilots, large batches, or any live model call.
- This record does not claim a negative capability result for any ACUT; the observed results are pre-verifier infrastructure/transport failures.

## Next Safe Work

Use the no-model options note at `experiments/core_narrative/reports/post_pilot_008_transport_options.md` and the completed Option C spike at `experiments/core_narrative/reports/post_pilot_008_option_c_no_model_spike.md`. The next safe step is review of that no-model spike, then either pause/report no scoreable result or prepare a separate no-secret operational-readiness record for exactly one future direct-transport probe. If a probe is ever proposed, it must explain why it is not another pilots 006/007/008 Codex CLI Responses streaming repeat and not another pilots 001/002/003 direct-command `gaierror` repeat.


## 2026-05-07 Update: Option C Review And Single Direct Probe

The Option C no-model spike review is integrated at `.codex-workflows/core-narrative-experiment/reviews/post-pilot-008-option-c-no-model-spike-review.md` with status `no_issues`. Reviewer prompt/run audit artifacts are retained under `.codex-workflows/core-narrative-experiment/workers/option-c-no-model-reviewer/` and no `cli.log` content was inspected.

Voyager's `2026-05-07T00:52+08:00` budget instruction is recorded in `.codex-workflows/core-narrative-experiment/decisions/post-option-c-direct-probe-readiness.md`. The USD `300` hard cap remains binding; the USD `240` soft stop is now an internal recorded coordinator decision point.

The coordinator records exactly one live direct Option C probe as authorized: `pilot_009__frontier-generic-swe__click__rbench__001__attempt1`. This does not reopen broad execution, retries, second attempts, additional specialist ACUT runs, further pilot attempts, or large batches. If this single probe repeats the prior direct-command `gaierror`/pre-verifier no-patch family, live execution on Option C must stop and the blocker should be reported rather than retried.
