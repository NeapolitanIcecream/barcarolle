# click__rbench__005

## Problem Statement

Add a case_sensitive=False mode to click.Choice so command-line values can match choices case-insensitively while preserving exact return values.

## Public Source

- Kind: pull_request
- Anchor: pallets/click#887
- URL: https://github.com/pallets/click/pull/887

## Visible Context Guidance

Provide the PR title and linked issue context for Choice matching. Keep the patch hidden.

## Expected Touched Area

- click.types.Choice normalization and conversion
- option tests for case-insensitive choices
