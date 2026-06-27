# Workspace ACUT Analysis

Status: `blocked_no_acut_command`.

The workspace ACUT adapter is implemented and tested, but the real endpoint-backed ACUT harness was not configured. No paid task-solving calls were made through the adapter.

## Comparison To Diff-Only Matrix A

The old measured endpoint Matrix A remains historical diagnostic evidence:

- task-solving cells: `10`;
- scoreable cells: `2`;
- invalid-output or harness-error cells: `8`;
- `G_mini` scoreable cells: `0`.

The workspace adapter is designed to remove the corrupt model-emitted-patch boundary by letting the ACUT harness edit a real worktree and by capturing `git diff --binary`. That protocol was verified with fake harness tests, but it has not yet been run with a real endpoint-backed ACUT.

## Current Workspace Adapter Artifacts

- Scheduled cells: `0`.
- Scoreable cells: `0`.
- Estimated incremental spend: `USD 0`.
- Blocker: `no_acut_workspace_command_configured`.

## Prior Invalid-Output Blocker

The adapter implementation addresses the mechanism that created corrupt patch text, but the blocker is not empirically resolved for the real ACUT until a configured endpoint-backed workspace harness runs at least the smoke subset.

## Next Step

Configure a real ACUT workspace command using `LLM_BASE_URL` and `LLM_API_KEY`, then run the `smoke` subcommand before any full 10-cell matrix.
