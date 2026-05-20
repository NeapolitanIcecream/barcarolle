# click__rbench__001 Provenance

This audit-only artifact preserves source and replay provenance that is intentionally excluded from the ACUT-visible statement.

## Source

- Kind: `pull_request`
- Anchor: `pallets/click#252`
- Public URL: `https://github.com/pallets/click/pull/252`
- Base commit: `4a7fe69f942bd02b811548ff8f02a08fff7429c1`
- Target commit: `39e51d961b9e69c050bb948b1db11275f9630542`
- Commits ahead: `3`

## Changed Files From Source Compare

- `click/core.py`
- `tests/test_options.py`

## Leakage Boundary

The ACUT-visible statement is `public/acut_statement.md`. It excludes target commit URLs, target SHAs, compare links, and reference patch material. This file is verifier/coordinator audit material, not ACUT input.
