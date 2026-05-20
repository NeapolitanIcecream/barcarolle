# click__rwork__002

## Problem Statement

Fix a CliRunner EOF regression so commands that read a click.File value from stdin continue to work instead of aborting when the synthetic stdin stream is exhausted.

## Visible Context Guidance

Provide the PR title and linked regression issue context. The reference diff and final code remain hidden.

## Expected Touched Area

- src/click/testing.py stdin wrapper behavior
- chain pipeline test using click.File("r") with "-"

## ACUT-Visible Context Boundary

Use only this task statement, the prepared repository workspace, allowed pre-base repository context, and the ACUT policy. Source provenance identifiers, answer artifacts, hidden verifier material, ACUT outputs, public model results, and future execution results are not ACUT-visible.
