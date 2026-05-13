# click__rwork__104

## Problem Statement

Preserve access to the original output file descriptor during CliRunner isolation so tooling such as faulthandler can target the real stream.

## Public Source

- Kind: pull_request
- Anchor: pallets/click#3244
- URL: https://github.com/pallets/click/pull/3244

## Visible Context Guidance

Provide the PR title and behavior summary. Hide the implementation diff and target tests.

## Expected Touched Area

- src/click/testing.py stream isolation
- tests/test_testing.py faulthandler stream behavior
