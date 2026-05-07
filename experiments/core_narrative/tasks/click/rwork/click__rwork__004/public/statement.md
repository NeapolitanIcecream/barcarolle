# click__rwork__004

## Problem Statement

Prevent callable flag_value objects from being instantiated merely because default=True causes a flag's default to align with its flag_value.

## Public Source

- Kind: commit
- Anchor: commit:546f2851f414b07413777ebcae89b2c21a685252
- URL: https://github.com/pallets/click/commit/546f2851f414b07413777ebcae89b2c21a685252

## Visible Context Guidance

Provide the commit title and linked issue identifiers 3121, 3201, and 3213. Do not show the reference patch.

## Expected Touched Area

- src/click/core.py Option default handling
- tests for callable flag_value defaults and default_map/show_default interactions
