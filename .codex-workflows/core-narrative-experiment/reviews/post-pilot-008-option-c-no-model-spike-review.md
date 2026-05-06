# Post-Pilot-008 Option C No-Model Spike Review

status: no_issues
updated: 2026-05-07T00:22:39+08:00

## Summary

The completed Option C no-model spike is internally consistent with the post-pilot-008 transport gate. It presents the direct `barcarolle_patch_command.py` path as no-model executable evidence only, not as live-call authorization, and it preserves the gate's key distinction: future live work must explain why it is not another pilots 006/007/008 Codex CLI Responses streaming repeat and not another pilots 001/002/003 direct-command `gaierror` repeat.

The executable evidence stays no-model/no-network in the reviewed checks. `barcarolle_patch_command.py` dry-run and mock-response modes avoid required LLM env and record `model_call_made: false`; live mode with missing env blocks before network with `network_attempted: false`; the default direct request shape for ordinary base URLs is chat-completions style without a streaming flag; and `acut_patch_adapter.py --command-no-model` requires zero projected cost/tokens while preserving ledger append, redaction, patch artifact, normalized-result, and verifier-ready-patch semantics.

No live BARCAROLLE model/API/network call was run or authorized by this review.

## Checks Performed

- Inspected `.codex-workflows/core-narrative-experiment/coordinator.md`, `.codex-workflows/core-narrative-experiment/decisions/post-pilot-008-transport-gate.md`, `experiments/core_narrative/reports/post_pilot_008_transport_options.md`, `experiments/core_narrative/reports/post_pilot_008_option_c_no_model_spike.md`, and `experiments/core_narrative/reports/kickoff_narrative_evidence_memo.md`.
- Inspected `experiments/core_narrative/tools/barcarolle_patch_command.py`, `experiments/core_narrative/tools/acut_patch_adapter.py`, `experiments/core_narrative/tools/codex_cli_patch_command.py`, `experiments/core_narrative/tools/_llm_budget.py`, `experiments/core_narrative/tools/test_barcarolle_patch_command.py`, `experiments/core_narrative/tools/test_codex_cli_patch_command.py`, and `experiments/core_narrative/tools/test_acut_patch_adapter.py`.
- Did not inspect any `cli.log`.
- `PYTHONDONTWRITEBYTECODE=1 python3 experiments/core_narrative/tools/test_barcarolle_patch_command.py` passed: 6 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 experiments/core_narrative/tools/test_codex_cli_patch_command.py` passed: 5 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 experiments/core_narrative/tools/test_acut_patch_adapter.py` passed: 4 tests.
- `PYTHONPYCACHEPREFIX=/tmp/barcarolle_option_c_review_pycache python3 -m py_compile experiments/core_narrative/tools/barcarolle_patch_command.py experiments/core_narrative/tools/acut_patch_adapter.py` passed.
- `git diff --check` passed.

## Findings

1. No issues found.

## Recommendation

Accept the Option C no-model spike as reviewed no-model evidence only. The next coordinator decision should still either pause/report no scoreable result or create a separate no-secret operational-readiness record for exactly one future direct-transport probe that satisfies the post-pilot-008 gate. Broad execution, retries, second attempts, additional specialist runs, further pilots, large batches, and live BARCAROLLE model calls remain unauthorized.
