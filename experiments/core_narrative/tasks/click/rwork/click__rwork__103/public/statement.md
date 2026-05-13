# click__rwork__103

## Problem Statement

Handle options that set is_flag=False together with flag_value so optional value parsing and output remain consistent across flag types.

## Public Source

- Kind: pull_request
- Anchor: pallets/click#3152
- URL: https://github.com/pallets/click/pull/3152

## Visible Context Guidance

Provide the PR title and behavior summary. Hide the implementation diff and target tests.

## Expected Touched Area

- src/click/core.py option value processing
- tests/test_options.py zero-or-one argument flag_value cases
