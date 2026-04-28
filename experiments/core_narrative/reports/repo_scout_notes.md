# Repo Scout Notes

Updated: 2026-04-28T12:23:52+08:00

## Recommendation

Use `pallets/click` as the primary target repository.

`pallets/click` has the best Phase 1 balance: mature public history, focused
Python code, local pytest verification, no expected external service
dependencies for core tests, permissive BSD-3-Clause licensing, and task
families that can be stated and verified without large fixtures.

Recommended fallbacks, in order:

1. `psf/black`
2. `python-attrs/attrs`
3. `pallets/flask`

The Barcarolle repository was excluded as required.

## Runtime Lock Update

Status: blocked. The pre-run repository lock is not closed because local
runtime verification could not complete in this sandbox.

The runtime-lock worker attempted the primary and every ordered fallback under
the ignored local probe directory `experiments/core_narrative/external_repos/`.
Each clone failed before checkout with DNS resolution failure for `github.com`,
so no repository commit, install timing, smoke timing, or full-suite timing was
available to lock:

| Candidate | Role | Clone target | Clone result | Elapsed |
| --- | --- | --- | --- | --- |
| `pallets/click` | primary | `experiments/core_narrative/external_repos/click` | failed before checkout: could not resolve `github.com` | 0.03s |
| `psf/black` | fallback 1 | `experiments/core_narrative/external_repos/black` | failed before checkout: could not resolve `github.com` | 0.02s |
| `python-attrs/attrs` | fallback 2 | `experiments/core_narrative/external_repos/attrs` | failed before checkout: could not resolve `github.com` | 0.02s |
| `pallets/flask` | fallback 3 | `experiments/core_narrative/external_repos/flask` | failed before checkout: could not resolve `github.com` | 0.02s |

Local checkout/cache search found no existing `click`, `black`, `attrs`, or
`flask` checkout under readable workspace or temp probe roots. Some macOS temp
subdirectories were unreadable due local permission restrictions.

Local tooling observed:

- `python`: not found on `PATH`.
- `python3`: `Python 3.9.6` at `/usr/bin/python3`.
- `uv`: `uv 0.11.1`; with `UV_CACHE_DIR=/tmp/barcarolle-uv-cache`, `uv python
  find 3.12` found `/Users/chenmohan/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12`.
- `git`: `git version 2.50.1 (Apple Git-155)`.

The revised default target remains 8 `RBench` tasks and 6 `RWork` tasks, one
primary attempt each, under the budget-constrained four-core ACUT profile.
`pallets/click` remains the preferred candidate on repo-scout evidence, but it
is not locally locked until a checkout commit can be installed and timed with at
least the smoke command
`pytest -q tests/test_parser.py tests/test_options.py tests/test_shell_completion.py`
and a full-suite or representative command such as `pytest -q`.

## Evidence

### `pallets/click`

- GitHub repository metadata identifies `pallets/click` as public, on default
  branch `main`, and small enough for light worker clones once network is
  available.
- `pyproject.toml` declares `license = "BSD-3-Clause"`, Python `>=3.10`, a
  `pytest` test dependency group, `testpaths = ["tests"]`, and default pytest
  `addopts = "-m 'not stress'"`.
- The test directory is behavior-rich but compact: parser, options, shell
  completion, term UI, CliRunner/testing helpers, defaults, formatting, context,
  and types are all represented by focused test files.
- GitHub issue/PR pages show current activity and a large closed-PR history
  from which to mine anchors. The public listing observed open issue/PR counts
  around 116 to 117 issues and 28 PRs, while search results exposed more than
  1,200 closed PRs.
- Service dependency risk is low because Click is a CLI library. Risk mostly
  comes from platform-sensitive behavior: TTYs, color, locale, streams, and
  Windows-only `colorama`.

### `psf/black`

- Strong fallback because its public history is very large and many formatter
  bug reports include self-contained input/output examples.
- `pyproject.toml` declares `license = "MIT"`, Python `>=3.10`, `pytest`
  with strict markers/config, and test dependencies including `pytest-xdist`.
- Test directory includes formatter, blackd, notebook, schema, tokenize, range,
  and transform tests.
- Risks: fuller suite is heavier than Click, formatter-oracle tasks require
  careful leakage controls, and some style changes are policy decisions rather
  than objective bug fixes.

### `python-attrs/attrs`

- Strong small fallback for fast local execution and low service risk.
- `pyproject.toml` declares `license = "MIT"`, Python `>=3.9`, no runtime
  dependencies, pytest testpaths, strict pytest config, and test dependencies
  including Hypothesis.
- The test directory covers converters, validators, generated dunders, slots,
  forward references, pattern matching, next-gen APIs, and packaging.
- GitHub shows hundreds of closed PRs and over one hundred open issues; a
  third-party issue index reported 295 merged PRs. That should be enough for a
  smaller task pack after filtering docs/packaging churn, but supply is tighter
  than Click or Black.

### `pallets/flask`

- Good high-supply fallback, especially if the experiment wants web-framework
  tasks after a first CLI/library run.
- `pyproject.toml` declares `license = "BSD-3-Clause"`, Python `>=3.10`,
  pytest tests, and a standard Pallets tox setup.
- GitHub merged-PR search exposed 1,619 total merged PR results, and the test
  directory covers app/request context, CLI, config, JSON, sessions, templating,
  views, blueprints, async, and signals.
- Risks: broader dependency graph and more integration-style behavior than
  Click; some tasks may need related Pallets packages or careful dependency
  pinning.

## Light Probe Results

- Created ignored directory `experiments/core_narrative/external_repos/`.
- Verified `.gitignore` ignores `experiments/core_narrative/external_repos/`.
- Attempted a shallow filtered clone of `pallets/click` into that directory.
- Clone failed before checkout with `Could not resolve host: github.com`, so no
  local full-suite timing was collected in this worker sandbox.
- GitHub connector and browser reads were used instead for pyproject, license,
  test-directory, and issue/PR evidence.

## Primary Self-Check

`pallets/click` can plausibly provide:

- RBench: 20 to 40 tasks, recommended target 30.
- RWork: 10 to 20 tasks, recommended target 12.

Suggested split:

- Use temporal split with cutoff around `2024-01-01`.
- RBench: merged PRs and linked issues before cutoff.
- RWork: later merged PRs plus selected still-open maintainer-style issues.
- Keep source anchors disjoint by PR/issue number and by target commit.

Likely task families:

- parser and option parsing edge cases
- default and flag value semantics
- shell completion behavior
- terminal UI, prompts, and color behavior
- `CliRunner` and testing helper behavior
- type annotation and metadata regressions
- help text and formatting regressions

Filtering required:

- Exclude docs-only, dependency-only, release-only, CI-only, and pure workflow
  maintenance PRs unless they exercise repository behavior with deterministic
  tests.
- Prefer anchors with existing regression tests or compact reproduction cases.
- Avoid or explicitly pin platform-specific anchors when behavior depends on
  Windows, terminal state, locale, or shell.

## Unresolved Questions

- Exact `pallets/click` full-suite runtime on the experiment machine.
- Best cutoff date after task-builder inspects actual merged PR density by
  task family.
- Whether to include still-open issues in RWork or use only post-cutoff merged
  PRs for stronger reference patches.
- Whether ACUT workspaces should use plain `pip install -e . pytest` or the
  repository's `tox`/`tox-uv` path for higher maintainer fidelity.

## Sources Consulted

- https://github.com/pallets/click
- https://github.com/pallets/click/blob/main/pyproject.toml
- https://github.com/pallets/click/blob/main/LICENSE.txt
- https://github.com/pallets/click/tree/main/tests
- https://github.com/pallets/click/issues
- https://github.com/pallets/click/pulls
- https://github.com/psf/black
- https://github.com/psf/black/blob/main/pyproject.toml
- https://github.com/psf/black/blob/main/LICENSE
- https://github.com/psf/black/tree/main/tests
- https://github.com/psf/black/issues
- https://github.com/psf/black/pulls
- https://github.com/python-attrs/attrs
- https://github.com/python-attrs/attrs/blob/main/pyproject.toml
- https://github.com/python-attrs/attrs/blob/main/LICENSE
- https://github.com/python-attrs/attrs/tree/main/tests
- https://github.com/python-attrs/attrs/issues
- https://github.com/python-attrs/attrs/pulls
- https://github.com/pallets/flask
- https://github.com/pallets/flask/blob/main/pyproject.toml
- https://github.com/pallets/flask/blob/main/LICENSE.txt
- https://github.com/pallets/flask/tree/main/tests
- https://github.com/pallets/flask/pulls?q=is%3Apr+is%3Amerged
- https://issues.ecosyste.ms/hosts/GitHub/repositories/python-attrs%2Fattrs
