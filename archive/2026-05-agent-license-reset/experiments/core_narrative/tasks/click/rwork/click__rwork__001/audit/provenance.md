# click__rwork__001 Provenance

This audit-only artifact preserves source and replay provenance that is intentionally excluded from the ACUT-visible statement.

## Source

- Kind: `pull_request`
- Anchor: `pallets/click#2956`
- Public URL: `https://github.com/pallets/click/pull/2956`
- Base commit: `5c1239b0116b66492cdd0848144ab3c78a04495a`
- Target commit: `565f36d5bc4a15d304337b749e113fb4477b1843`
- Commits ahead: `2`

## Changed Files From Source Compare

- `src/click/core.py`
- `src/click/types.py`
- `tests/test_options.py`
- `tests/test_basic.py`
- `tests/test_imports.py`

## Leakage Boundary

The ACUT-visible statement is `public/acut_statement.md`. It excludes target commit URLs, target SHAs, compare links, and reference patch material. This file is verifier/coordinator audit material, not ACUT input.
