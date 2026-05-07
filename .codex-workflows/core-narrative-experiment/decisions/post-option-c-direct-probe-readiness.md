# Post-Option-C Direct Probe Readiness

status: single_probe_consumed_non_scoreable_invalid_patch
recorded_at: 2026-05-07T01:00:00+08:00
updated: 2026-05-07T01:24:00+08:00
owner: coordinator
related_gate: `.codex-workflows/core-narrative-experiment/decisions/post-pilot-008-transport-gate.md`
related_review: `.codex-workflows/core-narrative-experiment/reviews/post-pilot-008-option-c-no-model-spike-review.md`

## Budget Authority Update

Voyager instructed at `2026-05-07T00:52+08:00`: “让 lab agent 持续推进，预算该花就花，不要阻塞”.

Coordinator interpretation for this experiment: Lab/coordinator may spend the assigned BARCAROLLE experiment budget without stopping for Voyager before each spend when a reviewed, non-redundant execution hypothesis justifies the call, the no-secret gates pass, and the projected cumulative estimated cost remains below the USD `300` hard cap. Crossing the USD `240` soft stop remains an internal coordinator decision point that must be recorded before proceeding.

## Reviewed Evidence Accepted

The delivered Option C no-model spike review was integrated on the coordinator branch as merge commit `26afcab` after recording the reviewer prompt/run audit artifacts on branch `codex/core-exp-option-c-no-model-reviewer`.

Review result: `no_issues`. The review confirms the Option C direct-command evidence is no-model/no-network, preserves adapter budget/ledger/redaction/normalization/verifier semantics, and does not itself authorize live calls.

Focused no-model verification was rerun by the coordinator after integration:

- `PYTHONDONTWRITEBYTECODE=1 python3 experiments/core_narrative/tools/test_barcarolle_patch_command.py` passed: 6 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 experiments/core_narrative/tools/test_codex_cli_patch_command.py` passed: 5 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 experiments/core_narrative/tools/test_acut_patch_adapter.py` passed: 4 tests.
- `PYTHONPYCACHEPREFIX=/tmp/barcarolle_lab_pycache_<pid> python3 -m py_compile experiments/core_narrative/tools/barcarolle_patch_command.py experiments/core_narrative/tools/acut_patch_adapter.py` passed.
- `git diff --check` passed.

## Fresh No-Secret Preflight

- `BARCAROLLE_LLM_API_KEY`: present; value not printed or recorded.
- `BARCAROLLE_LLM_BASE_URL`: present; value not printed or recorded.
- Cost ledger: `experiments/core_narrative/results/cost_ledger.jsonl` exists, parses as JSONL, and is writable.
- Ledger state before the proposed probe: 11 records; cumulative estimated cost USD `31.0008`.
- Projected additional cost for the proposed frontier direct probe: USD `10.00`.
- Projected cumulative estimated cost: USD `41.0008`, below both the USD `240` soft stop and USD `300` hard cap.
- No credential values, bearer tokens, resolved secrets, full base URLs, hostnames, or IP addresses were recorded.

## Authorized Single Probe

Exactly one live BARCAROLLE model-call probe is authorized:

- run_id: `pilot_009__frontier-generic-swe__click__rbench__001__attempt1`
- ACUT: `frontier-generic-swe`
- model route: `openai/gpt-5.5`
- task: `click__rbench__001`
- split: `rbench`
- attempt: `1`
- specialist context expected: false; the generic ACUT must not receive the Click specialist context pack.
- outer adapter: `experiments/core_narrative/tools/acut_patch_adapter.py`
- inner command: `experiments/core_narrative/tools/barcarolle_patch_command.py`
- transport hypothesis: direct BARCAROLLE-env-only HTTP request path; ordinary base URLs resolve to non-streaming chat-completions request shape; no `codex exec` Responses streaming path.

## Why This Is Not A Bad Repeat

This probe is not another pilots 006/007/008 repeat because it does not use the reviewed-failing Codex CLI Responses streaming path; it replaces only the inner patch-generation command with the reviewed Option C direct command while preserving the outer adapter gates.

This probe is not accepted as a cleared direct path. Pilots 001/002/003 already showed direct-command `gaierror` failures, including after the provider-prefixed model-route fix. The non-redundant value of this single probe is diagnostic and final for Option C: it tests the reviewed direct non-streaming path on the previously untried frontier generic ACUT/model route, with current env/ledger gates and no-model evidence integrated. If it returns the same redacted `gaierror` family or another pre-verifier no-patch transport failure, the coordinator must stop live BARCAROLLE execution on this path and report a hard/repeated infrastructure blocker instead of retrying.

If it produces a verifier-ready patch, run exactly one verifier pass for this same task/workspace and record the normalized result. Do not start any retry or second attempt.

## Still Not Authorized

This record does not authorize broad ACUT execution, retries, second attempts, additional specialist ACUT runs, further pilot attempts beyond the single run id above, large batches, external/public actions, pushing, or PR creation.


## Result Update

The single authorized probe was consumed by `pilot_009__frontier-generic-swe__click__rbench__001__attempt1` and integrated as merge commit `314fffa`. It did not repeat the prior direct-command `gaierror` family; the direct path reached a live model response. The response failed patch validation (`generated unified diff failed git apply validation`, `corrupt patch at line 12`), leaving no verifier-ready patch and no scoreable ACUT result.

Ledger state after the run: 12 records, cumulative estimated cost USD `41.0008`. No retry, second attempt, additional specialist run, broad execution, further pilot, large batch, or verifier run occurred. No further live probe is authorized by this readiness record.
