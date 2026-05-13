# click__rwork__101

## Problem Statement

Treat an internal UNSET value in default_map as absent for option lookup, so a mapped absence does not suppress the normal declared default path.

## Public Source

- Kind: pull_request
- Anchor: pallets/click#3240
- URL: https://github.com/pallets/click/pull/3240

## Visible Context Guidance

Provide the PR title and behavior summary. Hide the implementation diff and target tests.

## Expected Touched Area

- src/click/core.py default_map lookup behavior
- tests/test_defaults.py default_map regression
