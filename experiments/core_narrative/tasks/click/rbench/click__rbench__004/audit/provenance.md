# click__rbench__004 Provenance

This audit-only artifact preserves source and replay provenance that is intentionally excluded from the ACUT-visible statement.

## Source

- Kind: `pull_request`
- Anchor: `pallets/click#868`
- Public URL: `https://github.com/pallets/click/pull/868`
- Base commit: `b1b4449cda6767f022372890998d6b0eb895d041`
- Target commit: `fdceb39d344603fc73a4d9761766b5701f69236d`
- Commits ahead: `1`

## Changed Files From Source Compare

- `click/testing.py`
- `tests/test_testing.py`
- `tests/test_termui.py`
- `tests/test_utils.py`

## Leakage Boundary

The ACUT-visible statement is `public/acut_statement.md`. It excludes target commit URLs, target SHAs, compare links, and reference patch material. This file is verifier/coordinator audit material, not ACUT input.
