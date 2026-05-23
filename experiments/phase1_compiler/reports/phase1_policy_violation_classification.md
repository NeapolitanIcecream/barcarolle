# Phase 1 Policy Violation Classification

Status: `confirmed_acut_policy_violation_no_rerun`.

The `attrs__hist__027` / `kilo_workspace` cell is a genuine ACUT boundary violation. The submission changed `src/attr/_make.py`, and the verifier correctly reported that path as out of scope.

Evidence:

- Current allowed code paths: `changelog.d/774.change.rst`, `conftest.py`, `src/attr/__init__.pyi`, `src/attr/_funcs.py`.
- Certified changed files: `changelog.d/774.change.rst`, `conftest.py`, `src/attr/__init__.pyi`, `src/attr/_funcs.py`, `tests/test_hooks.py`.
- Target commit changed files: `changelog.d/774.change.rst`, `conftest.py`, `src/attr/__init__.pyi`, `src/attr/_funcs.py`, `tests/test_hooks.py`.
- Solver-visible context ref: `issue:766`.
- Candidate code file: `src/attr/_funcs.py`.
- Violating path: `src/attr/_make.py`.

There is a benchmark-side reporting bug, but it only affected the detail attached to the policy violation in two-repo metrics. That reporting bug is repaired. The allowed path list itself is not wrong under the evidence available before the paid run.

No deterministic replay is allowed for this classification, because replay is reserved for benchmark scope metadata bugs. No paid rerun is allowed, because confirmed ACUT policy violations stop before paid repair work. Predictive validity cannot be claimed because the frozen decision logic allows zero policy violations and this validation still has one.
