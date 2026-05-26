# Phase 1 Reference-Pass Environment Drift Audit

Plain-language summary: repeated reference failures are grouped by bounded error classes. This separates local validation-code bugs from old-repo environment or dependency drift.

## Environment Labels

| label | count |
| --- | ---: |
| dependency_version_drift | 1 |
| pytest_collection_or_config_error | 5 |
| python_version_drift | 6 |

## Dependency Probes

| repo | returncode | error | output |
| --- | ---: | --- | --- |
| attrs | 0 | pass | {'python': '3.11.13', 'packages': {'pytest': '7.4.4', 'setuptools': '80.10.2', 'hypothesis': '5.49.0', 'attrs': '26.1.0', 'boltons': 'missing'}} | warning: `VIRTUAL_ENV=experiments/phase1_compiler/.venv` does not match the project environment path `experiments/phase0_headroom/.venv` and will be ignored; use `--active` to target the active environment instead |
| boltons | 0 | pass | {'python': '3.11.13', 'packages': {'pytest': '8.4.2', 'setuptools': '80.10.2', 'hypothesis': 'missing', 'attrs': 'missing', 'boltons': 'missing'}} | warning: `VIRTUAL_ENV=experiments/phase1_compiler/.venv` does not match the project environment path `experiments/phase0_headroom/.venv` and will be ignored; use `--active` to target the active environment instead |
