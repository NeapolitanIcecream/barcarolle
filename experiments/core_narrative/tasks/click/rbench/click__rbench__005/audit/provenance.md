# click__rbench__005 Provenance

This audit-only artifact preserves source and replay provenance that is intentionally excluded from the ACUT-visible statement.

## Source

- Kind: `pull_request`
- Anchor: `pallets/click#887`
- Public URL: `https://github.com/pallets/click/pull/887`
- Base commit: `a00e01845100ce2b3d5288a2b655aad260346361`
- Target commit: `c70d4636831e391016895587f7ed10e96f49773e`
- Commits ahead: `2`

## Changed Files From Source Compare

- `click/types.py`
- `tests/test_options.py`

## Leakage Boundary

The ACUT-visible statement is `public/acut_statement.md`. It excludes target commit URLs, target SHAs, compare links, and reference patch material. This file is verifier/coordinator audit material, not ACUT input.
