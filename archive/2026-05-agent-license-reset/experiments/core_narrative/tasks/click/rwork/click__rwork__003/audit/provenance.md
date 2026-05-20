# click__rwork__003 Provenance

This audit-only artifact preserves source and replay provenance that is intentionally excluded from the ACUT-visible statement.

## Source

- Kind: `commit`
- Anchor: `commit:1c20dc6e724cd5625faaa17b715ba928d44c08bf`
- Public URL: `https://github.com/pallets/click/commit/1c20dc6e724cd5625faaa17b715ba928d44c08bf`
- Base commit: `6a1c0d077311f180b356965914e2de5b9e0fdb44`
- Target commit: `1c20dc6e724cd5625faaa17b715ba928d44c08bf`
- Commits ahead: `1`

## Changed Files From Source Compare

- `src/click/core.py`
- `tests/test_defaults.py`

## Leakage Boundary

The ACUT-visible statement is `public/acut_statement.md`. It excludes target commit URLs, target SHAs, compare links, and reference patch material. This file is verifier/coordinator audit material, not ACUT input.
