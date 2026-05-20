# click__rwork__005 Provenance

This audit-only artifact preserves source and replay provenance that is intentionally excluded from the ACUT-visible statement.

## Source

- Kind: `commit`
- Anchor: `commit:4f9086bf8fd98aca1d804bf742f4f1ceb6c12295`
- Public URL: `https://github.com/pallets/click/commit/4f9086bf8fd98aca1d804bf742f4f1ceb6c12295`
- Base commit: `1339fd3323357119a9c7a6326c788f80295954ce`
- Target commit: `4f9086bf8fd98aca1d804bf742f4f1ceb6c12295`
- Commits ahead: `1`

## Changed Files From Source Compare

- `src/click/testing.py`
- `tests/test_testing.py`

## Leakage Boundary

The ACUT-visible statement is `public/acut_statement.md`. It excludes target commit URLs, target SHAs, compare links, and reference patch material. This file is verifier/coordinator audit material, not ACUT input.
