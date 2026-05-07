# click__rwork__005

## Problem Statement

Patch pdb initialization during CliRunner.invoke so debugger instances created without explicit streams use the real terminal streams, while explicit stream arguments remain honored and the patch is restored after invocation.

## Public Source

- Kind: commit
- Anchor: commit:4f9086bf8fd98aca1d804bf742f4f1ceb6c12295
- URL: https://github.com/pallets/click/commit/4f9086bf8fd98aca1d804bf742f4f1ceb6c12295

## Visible Context Guidance

Provide the commit title and linked issue identifiers 654, 824, 843, and 951. Hide the implementation diff.

## Expected Touched Area

- src/click/testing.py CliRunner isolation context
- tests for pdb stream selection and restoration
