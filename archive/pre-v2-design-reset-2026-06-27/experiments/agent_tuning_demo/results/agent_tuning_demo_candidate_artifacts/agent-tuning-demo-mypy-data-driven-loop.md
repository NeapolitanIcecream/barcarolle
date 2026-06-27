## Barcarolle Agent Tuning Demo Appendix

When solving mypy tasks for this benchmark, treat the task as a narrow data-driven regression repair.
Start from the listed editable implementation paths and inspect adjacent implementation code before editing.
If the statement names TypeCheckSuite or `test-data` entry points, infer the expected behavior from nearby existing cases,
but do not edit tests or test-data files. Prefer a minimal semantic fix over broad rewrites, and run the targeted verifier
command shape from the task statement before finishing when feasible.
