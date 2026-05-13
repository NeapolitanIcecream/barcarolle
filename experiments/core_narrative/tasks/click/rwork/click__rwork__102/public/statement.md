# click__rwork__102

## Problem Statement

Fix empty-string default display handling so show_default behavior does not depend on speculative truthiness checks.

## Public Source

- Kind: pull_request
- Anchor: pallets/click#3299
- URL: https://github.com/pallets/click/pull/3299

## Visible Context Guidance

Provide the PR title and behavior summary. Hide the implementation diff and target tests.

## Expected Touched Area

- src/click/core.py default display logic
- tests/test_options.py show_default empty-string cases
