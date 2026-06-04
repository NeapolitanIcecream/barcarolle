# click__rbench__002 Provenance

This audit-only artifact preserves source and replay provenance that is intentionally excluded from the ACUT-visible statement.

## Source

- Kind: `pull_request`
- Anchor: `pallets/click#151`
- Public URL: `https://github.com/pallets/click/pull/151`
- Base commit: `b557743f3bc26a4cdbf610b221e7e81d609aa65d`
- Target commit: `637447f9ccf882d5c810540ca261e8ba2af9cb1c`
- Commits ahead: `2`

## Changed Files From Source Compare

- `click/testing.py`
- `tests/test_testing.py`

## Leakage Boundary

The ACUT-visible statement is `public/acut_statement.md`. It excludes target commit URLs, target SHAs, compare links, and reference patch material. This file is verifier/coordinator audit material, not ACUT input.
