# click__rwork__004 Provenance

This audit-only artifact preserves source and replay provenance that is intentionally excluded from the ACUT-visible statement.

## Source

- Kind: `commit`
- Anchor: `commit:546f2851f414b07413777ebcae89b2c21a685252`
- Public URL: `https://github.com/pallets/click/commit/546f2851f414b07413777ebcae89b2c21a685252`
- Base commit: `ae46cfd6bc997804893adc799589248eadcdbc29`
- Target commit: `546f2851f414b07413777ebcae89b2c21a685252`
- Commits ahead: `1`

## Changed Files From Source Compare

- `src/click/core.py`
- `tests/test_defaults.py`
- `tests/test_options.py`

## Leakage Boundary

The ACUT-visible statement is `public/acut_statement.md`. It excludes target commit URLs, target SHAs, compare links, and reference patch material. This file is verifier/coordinator audit material, not ACUT input.
