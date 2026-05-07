# click__rwork__002

## Problem Statement

Fix a CliRunner EOF regression so commands that read a click.File value from stdin continue to work instead of aborting when the synthetic stdin stream is exhausted.

## Public Source

- Kind: pull_request
- Anchor: pallets/click#2940
- URL: https://github.com/pallets/click/pull/2940

## Visible Context Guidance

Provide the PR title and linked regression issue context. The reference diff and final code remain hidden.

## Expected Touched Area

- src/click/testing.py stdin wrapper behavior
- chain pipeline test using click.File("r") with "-"
