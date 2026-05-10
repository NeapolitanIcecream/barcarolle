# click__rbench__008 Provenance

This audit-only artifact preserves source and replay provenance that is intentionally excluded from the ACUT-visible statement.

## Source

- Kind: `pull_request`
- Anchor: `pallets/click#1618`
- Public URL: `https://github.com/pallets/click/pull/1618`
- Base commit: `7332f00ed4c27d8da041788ca6a7aa405f062c76`
- Target commit: `8efb348e2bc820aeba60d4cce6939708c6b2b11c`
- Commits ahead: `2`

## Changed Files From Source Compare

- `src/click/core.py`
- `src/click/parser.py`
- `tests/test_options.py`
- `tests/test_termui.py`

## Leakage Boundary

The ACUT-visible statement is `public/acut_statement.md`. It excludes target commit URLs, target SHAs, compare links, and reference patch material. This file is verifier/coordinator audit material, not ACUT input.
