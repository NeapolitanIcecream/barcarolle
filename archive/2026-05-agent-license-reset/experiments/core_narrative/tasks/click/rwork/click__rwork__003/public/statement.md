# click__rwork__003

## Problem Statement

Defer normalization of internal UNSET defaults until all options sharing a parameter have been evaluated, so the first real default is preserved regardless of declaration order.

## Public Source

- Kind: commit
- Anchor: commit:1c20dc6e724cd5625faaa17b715ba928d44c08bf
- URL: https://github.com/pallets/click/commit/1c20dc6e724cd5625faaa17b715ba928d44c08bf

## Visible Context Guidance

Provide the commit message and linked issue identifier 3071. Hide the target diff and exact implementation.

## Expected Touched Area

- src/click/core.py default lookup and normalization
- tests/test_defaults.py shared-parameter default regression
