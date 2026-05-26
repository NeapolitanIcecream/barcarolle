# Phase 1 Historical Environment Profile Catalog

Plain-language summary: the catalog is intentionally small. Each task gets the current-style baseline plus historical Python/pytest fallbacks capped at five profiles.

| profile | python | install mode | deps | why |
| --- | --- | --- | --- | --- |
| `py311_current_editable` | 3.11 | editable | `pytest>=8,<9`, `setuptools<81`, `hypothesis<6` | baseline comparison using current-style dependencies without the Barcarolle project |
| `py310_pytest7_editable` | 3.10 | editable | `pytest>=7,<8`, `setuptools<81`, `hypothesis<6` | newer historical projects |
| `py39_pytest_lt5_pythonpath` | 3.9 | pythonpath_only | `pytest<5`, `setuptools<58` | old pytest cutoff-compatible runs without installing the target project |
| `py38_pytest_lt4_pythonpath` | 3.8 | pythonpath_only | `pytest<4`, `setuptools<58` | old attrs-era pytest configuration compatibility |
| `py37_pytest4_pythonpath` | 3.7 | pythonpath_only | `pytest<5`, `setuptools<58` | optional oldest bounded profile; skipped cleanly if uv cannot provide Python 3.7 |
