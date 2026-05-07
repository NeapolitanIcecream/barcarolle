# OpenClaw As-Is Status Sync Process

status: delivered_as_is_sync
updated: 2026-05-07T19:20:00+08:00
repo: `/Users/chenmohan/gits/barcarolle`
branch: `codex/core-narrative-experiment`
scope: synchronize current experiment state for Codex resumption only

## User Direction

The user stated they are preparing to switch the experiment back to Codex and no longer try to have OpenClaw take over this experiment.

This sync records the current state as-is. It does not start any model call, retry, broad execution, OpenClaw continuation, worker, reviewer, or tmux session.

## Current State

- Main status report: `experiments/core_narrative/reports/2026-05-07_openclaw_overnight_experiment.md`.
- Aggregate summary: `experiments/core_narrative/results/overnight_2026-05-07_summary.json`.
- Score summary: `experiments/core_narrative/results/normalized/openclaw_search_replace_summary.json`.
- Cost reconciliation: `experiments/core_narrative/results/cost_reconciliation_2026-05-07.json`.
- Coordinator synchronized in: `.codex-workflows/core-narrative-experiment/coordinator.md`.

The OpenClaw direct runner got past the previous launch/output plumbing blocker and produced first live scoreable data, but did not produce a passing verifier result.

## Live Result Snapshot

| run_id | ACUT | normalized status | scoreable | as-is diagnosis |
| --- | --- | --- | --- | --- |
| `openclaw_001__cheap-generic-swe__click__rbench__001__search-replace__attempt1` | `cheap-generic-swe` | `failed` | yes | generated a patch and reached verifier, but rendered tuple repr instead of expected comma-separated Click default help text |
| `openclaw_002__cheap-click-specialist__click__rbench__001__search-replace__attempt1` | `cheap-click-specialist` | `infra_failed` | no | generated `src/click/core.py` for a historical workspace whose path is `click/core.py` |
| `openclaw_003__frontier-generic-swe__click__rbench__001__search-replace__attempt1` | `frontier-generic-swe` | `failed` | yes | same semantic miss as cheap generic |

Aggregate OpenClaw live status:

- total live OpenClaw runs: 3
- scoreable verifier results: 2
- passed: 0
- failed: 2
- infra_failed: 1

No-model verifier sanity:

- `noop_verify_check__click__rbench__001__20260507` failed as expected.
- `openclaw_direct_mock__cheap-generic-swe__click__rbench__001__attempt1` passed the hidden verifier, proving the patch/verifier path can work when given a correct patch.

## Prior Codex Direct Probes

- `pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1`: strict `structured-files-json-v1` path timed out at the direct HTTP layer before model response; no verifier-ready patch.
- `pilot_011__frontier-generic-swe__click__rbench__001__structured-files-json-http300__attempt1`: env and budget gates passed, one model response arrived in 67.3s, but the strict contract failed with `unsupported_patch_response`; no verifier-ready patch.

## Cost / Ledger State

- `experiments/core_narrative/results/cost_ledger.jsonl` has 17 records.
- Latest cumulative estimated cost: USD `66.0008`.
- OpenClaw provider response usage cost sum: USD `0.177407`.
- Actual provider billed cost observed in repo artifacts: `null`.
- Cost interpretation: ledger estimate is local budgeting, and provider response usage cost is not invoice proof.

## No-Secret Sync Checks

- `BARCAROLLE_LLM_API_KEY`: present during sync; value not inspected or recorded.
- `BARCAROLLE_LLM_BASE_URL`: present during sync; value not inspected or recorded.
- Cost ledger: writable.
- Core-narrative tmux sessions matching `core`, `narrative`, `barcarolle`, `bcx`, or `openclaw`: none.
- `cli.log` inspected: false.

## Current Blocker

The current blocker is not basic transport, env presence, or whether a runner can produce a verifier artifact. The blocker is the Codex-owned next execution path and patch/context behavior:

- generic ACUTs generated plausible but semantically wrong patches;
- specialist context biased the model toward a modern `src/` path that does not exist in the historical task workspace;
- the user has superseded the OpenClaw-primary recommendation and wants Codex to resume ownership.

## Next Bounded Step

Resume from Codex with this as-is handoff. Do not start another live model call, OpenClaw continuation, retry, second attempt, additional specialist run, broad execution, further pilot attempt, or large batch without a new explicit coordinator decision.
