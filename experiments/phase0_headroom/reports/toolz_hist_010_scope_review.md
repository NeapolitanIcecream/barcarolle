# Toolz Hist 010 Scope Review

Decision: keep the repaired-matrix policy violation. Package export edits are
optional public-API polish for this task, but they are outside the current
certified ACUT boundary.

## Evidence Reviewed

- Task: `toolz__hist__010`.
- Solver statement: add `pipeline`, a left-to-right function-composition helper,
  while preserving existing `pipe` behavior.
- Certified source commit: `9e97f73fee5fc68bd03adcee3b520593ed5063d6`.
- Reference diff changed only:
  - `toolz/functoolz.py`
  - `toolz/tests/test_functoolz.py`
- Certified code path is `toolz/functoolz.py`.
- Repaired Codex matrix cell changed only `toolz/functoolz.py` and verified
  pass.
- Repaired Kilo smoke cell changed only `toolz/functoolz.py` and verified pass.
- Repaired Kilo full-matrix cell changed `toolz/functoolz.py` plus
  `toolz/__init__.py` and `toolz/curried/__init__.py`, then was rejected by
  policy for the package export paths.

The hidden verifier was inspected for scope only and is not reproduced here.
Its outcome is already captured by the committed verifier result rows.

## Decision

Do not allow package export files for this certified task.

The reason is not that exporting `pipeline` would be an unreasonable product
choice. It is that the benchmark task boundary is narrower than that product
choice:

- the reference implementation did not edit package export files;
- the statement did not ask for package-root or curried namespace exposure;
- implementation-only submissions are sufficient for the current verifier;
- broadening this one task would make the benchmark-side policy depend on an
  optional API interpretation rather than the certified reference scope.

Therefore `toolz/__init__.py` and `toolz/curried/__init__.py` remain
out-of-scope for `toolz__hist__010`.

## Policy Impact

No task metadata is changed. The global test-edit rejection remains unchanged.
Future task certification can include package export files when the source
diff, issue context, or solver-facing statement makes export behavior explicit.
