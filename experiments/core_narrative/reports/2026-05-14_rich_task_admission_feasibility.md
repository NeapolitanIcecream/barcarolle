# Rich Task-Admission Feasibility

Status: `collect_only_feasible_with_isolated_dependencies`

## Result

Rich is not collect-ready in the ambient Python environment, but it is collect-ready in an isolated environment after installing the project plus `pytest` and `attrs`.

| Check | Exit | Observation |
|---|---:|---|
| Ambient `python3 -m pytest -q --collect-only tests` | 2 | 919 tests were listed before 4 collection errors from missing `markdown_it` and `attr`. |
| Isolated venv with `pip install -e . pytest attrs` | 0 | 981 tests collected in 0.52s. |

## Dependency Notes

- `pyproject.toml` declares `markdown-it-py` and `pygments` as project dependencies.
- `pyproject.toml` declares `pytest` and `attrs` as dev dependencies relevant to collection.
- `tox.ini` runs `poetry install` before pytest.

## Boundary

This is not task admission. It does not prove no-op failure, reference-patch pass, hidden-verifier behavior, or historical-base compatibility. It only shows that the ready Rich repo can be made test-collectable with an isolated dependency setup.

Next step: implement Rich task-admission smoke using isolated install commands and construct Golden-Oracle verifiers for source-only W* candidates.
