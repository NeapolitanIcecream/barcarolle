# click__rwork__005

## Problem Statement

Patch pdb initialization during CliRunner.invoke so debugger instances created without explicit streams use the real terminal streams, while explicit stream arguments remain honored and the patch is restored after invocation.

## Visible Context Guidance

Provide the commit title and linked issue identifiers 654, 824, 843, and 951. Hide the implementation diff.

## Expected Touched Area

- src/click/testing.py CliRunner isolation context
- tests for pdb stream selection and restoration

## ACUT-Visible Context Boundary

Use only this task statement, the prepared repository workspace, allowed pre-base repository context, and the ACUT policy. Source provenance identifiers, answer artifacts, hidden verifier material, ACUT outputs, public model results, and future execution results are not ACUT-visible.
