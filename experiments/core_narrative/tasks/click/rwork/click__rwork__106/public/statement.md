# click__rwork__106

## Problem Statement

Respect string-valued show_default in prompt rendering so prompt text can display custom default descriptions instead of internal default objects.

## Public Source

- Kind: pull_request
- Anchor: pallets/click#3328
- URL: https://github.com/pallets/click/pull/3328

## Visible Context Guidance

Provide the PR title and behavior summary. Hide the implementation diff and target tests.

## Expected Touched Area

- src/click/core.py prompt/default display metadata
- src/click/termui.py prompt text rendering
- tests for string show_default in prompts
