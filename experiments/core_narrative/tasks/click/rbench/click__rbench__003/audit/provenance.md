# click__rbench__003 Provenance

This audit-only artifact preserves source and replay provenance that is intentionally excluded from the ACUT-visible statement.

## Source

- Kind: `commit`
- Anchor: `commit:02ea9ee7e864581258b4902d6e6c1264b0226b9f`
- Public URL: `https://github.com/pallets/click/commit/02ea9ee7e864581258b4902d6e6c1264b0226b9f`
- Base commit: `d3f36e884e18f374c3e4e6cf062ba19f100d0fd6`
- Target commit: `02ea9ee7e864581258b4902d6e6c1264b0226b9f`
- Commits ahead: `1`

## Changed Files From Source Compare

- `click/core.py`
- `click/termui.py`
- `tests/test_termui.py`

## Leakage Boundary

The ACUT-visible statement is `public/acut_statement.md`. It excludes target commit URLs, target SHAs, compare links, and reference patch material. This file is verifier/coordinator audit material, not ACUT input.
