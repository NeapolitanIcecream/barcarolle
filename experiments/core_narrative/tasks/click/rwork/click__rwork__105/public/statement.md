# click__rwork__105

## Problem Statement

Add a CliRunner-level default for catch_exceptions so repeated invokes can share the same exception-capture policy without passing it each time.

## Public Source

- Kind: pull_request
- Anchor: pallets/click#2818
- URL: https://github.com/pallets/click/pull/2818

## Visible Context Guidance

Provide the PR title and behavior summary. Hide the implementation diff and target tests.

## Expected Touched Area

- src/click/testing.py CliRunner initialization and invoke defaults
- tests/test_testing.py catch_exceptions behavior
