# click__rwork__003

## Problem Statement

Defer normalization of internal UNSET defaults until all options sharing a parameter have been evaluated, so the first real default is preserved regardless of declaration order.

## Visible Context Guidance

Provide the commit message and linked issue identifier 3071. Hide the answer artifact and exact implementation.

## Expected Touched Area

- src/click/core.py default lookup and normalization
- tests/test_defaults.py shared-parameter default regression

## ACUT-Visible Context Boundary

Use only this task statement, the prepared repository workspace, allowed pre-base repository context, and the ACUT policy. Source provenance identifiers, answer artifacts, hidden verifier material, ACUT outputs, public model results, and future execution results are not ACUT-visible.
