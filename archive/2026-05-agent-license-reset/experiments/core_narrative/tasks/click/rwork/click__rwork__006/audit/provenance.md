# click__rwork__006 Provenance

This audit-only artifact preserves source and replay provenance that is intentionally excluded from the ACUT-visible statement.

## Source

- Kind: `commit`
- Anchor: `commit:c653ec820093ed1dda41aae8d35bff7834b0344a`
- Public URL: `https://github.com/pallets/click/commit/c653ec820093ed1dda41aae8d35bff7834b0344a`
- Base commit: `878de46100e9c29aea9dab5b385b8116863cb5e3`
- Target commit: `c653ec820093ed1dda41aae8d35bff7834b0344a`
- Commits ahead: `1`

## Changed Files From Source Compare

- `src/click/core.py`
- `tests/test_options.py`
- `tests/test_termui.py`

## Leakage Boundary

The ACUT-visible statement is `public/acut_statement.md`. It excludes target commit URLs, target SHAs, compare links, and reference patch material. This file is verifier/coordinator audit material, not ACUT input.
