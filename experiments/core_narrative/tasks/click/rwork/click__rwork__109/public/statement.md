# click__rwork__109

## Problem Statement

Expand Choice token normalization so enum, custom type, and None cases produce consistent accepted values and error messages.

## Public Source

- Kind: pull_request
- Anchor: pallets/click#2796
- URL: https://github.com/pallets/click/pull/2796

## Visible Context Guidance

Provide the PR title and behavior summary. Hide the implementation diff and target tests.

## Expected Touched Area

- src/click/types.py Choice normalization
- src/click/core.py parameter handling around Choice
- tests/test_types.py Choice argument cases
