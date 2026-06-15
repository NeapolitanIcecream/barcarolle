# Agent Tuning Phase 2 action-level preflight

生成日期：2026-06-15T02:21:07+00:00

Status: `passed`.
Paid calls used: `0`.

## Evidence

| Variant | Exit | Artifact loaded | Bash tool call | Public marker | Paid |
| --- | --- | --- | --- | --- | --- |
| A | 0 | True | False | False | False |
| B | 0 | True | True | True | False |

Variant B caused the real Kilo CLI to execute the `bash` tool with the public pytest command; the test wrote `.barcarolle_public_test_marker`. Variant A did not. This is an action-level difference, not request-context-only evidence.
