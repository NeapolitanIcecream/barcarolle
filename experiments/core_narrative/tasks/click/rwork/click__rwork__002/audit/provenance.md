# click__rwork__002 Provenance

This audit-only artifact preserves source and replay provenance that is intentionally excluded from the ACUT-visible statement.

## Source

- Kind: `pull_request`
- Anchor: `pallets/click#2940`
- Public URL: `https://github.com/pallets/click/pull/2940`
- Base commit: `36deba8a95a2585de1a2aa4475b7f054f52830ac`
- Target commit: `2a0e3ba907927ade6951d5732b775f11b54cb766`
- Commits ahead: `3`

## Changed Files From Source Compare

- `src/click/testing.py`
- `tests/test_chain.py`

## Leakage Boundary

The ACUT-visible statement is `public/acut_statement.md`. It excludes target commit URLs, target SHAs, compare links, and reference patch material. This file is verifier/coordinator audit material, not ACUT input.
