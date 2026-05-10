# click__rbench__006 Provenance

This audit-only artifact preserves source and replay provenance that is intentionally excluded from the ACUT-visible statement.

## Source

- Kind: `commit`
- Anchor: `commit:5fe0b7e7795f9bb04ae926d00868cfeb1fa33187`
- Public URL: `https://github.com/pallets/click/commit/5fe0b7e7795f9bb04ae926d00868cfeb1fa33187`
- Base commit: `6e62332349db6e93decf47666c4cd6fe20df6b02`
- Target commit: `5fe0b7e7795f9bb04ae926d00868cfeb1fa33187`
- Commits ahead: `1`

## Changed Files From Source Compare

- `click/types.py`
- `tests/test_basic.py`

## Leakage Boundary

The ACUT-visible statement is `public/acut_statement.md`. It excludes target commit URLs, target SHAs, compare links, and reference patch material. This file is verifier/coordinator audit material, not ACUT input.
