# click__rwork__107

## Problem Statement

Render prompts and confirmations correctly when prompt_suffix is an empty string, including stdout and stderr prompt destinations.

## Public Source

- Kind: pull_request
- Anchor: pallets/click#3021
- URL: https://github.com/pallets/click/pull/3021

## Visible Context Guidance

Provide the PR title and behavior summary. Hide the implementation diff and target tests.

## Expected Touched Area

- src/click/termui.py prompt suffix rendering
- tests/test_utils.py prompt output capture
