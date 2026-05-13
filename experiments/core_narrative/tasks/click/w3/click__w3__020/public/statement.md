# click__w3__020

## Problem Statement

Implement the Click behavior change: Close contexts created during shell completion #2644.

## Public Source

- Kind: commit_or_pull_request
- Anchor: pallets/click#2644
- URL: https://github.com/pallets/click/commit/0ef55fda47bb3d0dece21197d81d8d72a4250e73

## Visible Context Guidance

Expose the public behavior summary and minimal reproduction expectation. Hide the implementation diff, reference patch, and target tests.

## Expected Touched Area

- src/click/core.py behavior surface
- src/click/shell_completion.py behavior surface
- tests/test_shell_completion.py focused regression coverage
