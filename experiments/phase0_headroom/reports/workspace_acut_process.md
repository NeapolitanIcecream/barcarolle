# Workspace ACUT Process

Generated UTC: `2026-05-21T02:52:31Z`.

## Step 0 Preflight

- Runbook: `docs/experiments/phase-0-workspace-acut-adapter-runbook.md`.
- Branch: `codex/restart-benchmark-compiler`.
- HEAD after adapter implementation commit: `0b920e3b`.
- `AGENTS.md` present: `true`.
- Endpoint env after sourcing shell config: `LLM_BASE_URL=true`, `LLM_API_KEY=true`.
- Current Phase 0 evidence present:
  - `reports/overnight_research_report.md`.
  - `results/generic_comparator_protocol.json`.
  - `results/headroom_matrix.json`.
  - `reports/phase0_decision_memo.md`.
- Generic comparator same-protocol tasks: `4`.
- `git diff --check`: passed.
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools`: `29 passed`.
- `uv run --project experiments/phase1_compiler pytest -q`: `4 passed`.
- Raw/workspace/cache paths tracked by git: `0`.

## Step 1 Adapter Contract

- Added `configs/acut_workspace_adapter.yaml`.
- Added `configs/workspace_acut_matrix.yaml`.
- Added `tools/workspace_acut_run.py`.
- Added `tools/test_workspace_acut_run.py`.
- Fake ACUT tests cover:
  - allowed code edit captured via `git diff --binary`;
  - empty workspace diff as `invalid_output`;
  - prohibited test edit as `policy_violation`;
  - non-zero ACUT process as `acut_harness_error`;
  - fresh verifier workspace replay;
  - hidden verifier material absent from solver workspace.

## Step 2 ACUT Harness Preflight

- Preflight status: `blocked_no_acut_command`.
- Required endpoint environment variables: present.
- Adapter config exists, but `command_template` is empty.
- `ACUT_WORKSPACE_COMMAND` was not available to provide the command template.
- No paid workspace ACUT task-solving calls were made.
- Empty sanitized result artifacts were initialized under `results/workspace_acut_*`.

## Stop Decision

The run stops at Step 2 because no endpoint-backed ACUT harness command is configured. This follows the runbook stop condition and avoids falling back to the old one-shot diff-only prompt path.

To continue, configure either `configs/acut_workspace_adapter.yaml` or `ACUT_WORKSPACE_COMMAND` with a command that mutates `{workspace}` and is proven to use `LLM_BASE_URL` plus `LLM_API_KEY`.
