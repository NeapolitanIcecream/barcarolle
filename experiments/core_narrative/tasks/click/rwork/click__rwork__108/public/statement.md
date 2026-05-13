# click__rwork__108

## Problem Statement

Ensure custom Parameter subclasses overriding type_cast_value do not receive internal UNSET sentinel values during argument or option parsing.

## Public Source

- Kind: pull_request
- Anchor: pallets/click#3090
- URL: https://github.com/pallets/click/pull/3090

## Visible Context Guidance

Provide the PR title and behavior summary. Hide the implementation diff and target tests.

## Expected Touched Area

- src/click/core.py type_cast_value call boundary
- tests for custom Argument and Option subclasses
