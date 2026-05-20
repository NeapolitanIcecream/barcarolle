# click__rbench__007 Provenance

This audit-only artifact preserves source and replay provenance that is intentionally excluded from the ACUT-visible statement.

## Source

- Kind: `pull_request`
- Anchor: `pallets/click#1312`
- Public URL: `https://github.com/pallets/click/pull/1312`
- Base commit: `563b1a7116a6806e699d31d327dd9bca93c40cb3`
- Target commit: `990ca8e664a0610fe0583f3aa8924fd49f928a74`
- Commits ahead: `2`

## Changed Files From Source Compare

- `src/click/testing.py`
- `tests/test_testing.py`

## Leakage Boundary

The ACUT-visible statement is `public/acut_statement.md`. It excludes target commit URLs, target SHAs, compare links, and reference patch material. This file is verifier/coordinator audit material, not ACUT input.
