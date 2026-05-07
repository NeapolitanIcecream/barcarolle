# click__rbench__007

## Problem Statement

Preserve a command callback's return value on the CliRunner Result object when running in standalone mode.

## Public Source

- Kind: pull_request
- Anchor: pallets/click#1312
- URL: https://github.com/pallets/click/pull/1312

## Visible Context Guidance

Show the PR title and desired testing API behavior. Keep implementation and patch details hidden.

## Expected Touched Area

- src/click/testing.py Result and invoke plumbing
- tests for Result.return_value
