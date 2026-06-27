# Phase 0 Repository Selection

Primary selected repository: `toolz`.

Selection used deterministic local evidence: reachable clone, Python compatibility, no external service requirement, changed-test smoke execution, and code-plus-test anchor count.

## Primary Probe

- Local path: `experiments/phase0_headroom/external_repos/toolz`
- Remote: `https://github.com/pytoolz/toolz.git`
- HEAD: `568c2b8393973cd172a466546c9d95779c452438`
- Smoke command: `PYTHONPATH=. /opt/homebrew/bin/uv run --project experiments/phase0_headroom python -m pytest toolz/tests -q --ignore=toolz/tests/test_package.py`
- Smoke exit code: `0`
- Smoke tail: `........................................................................ [ 80%] | ....................................                                     [100%] | 180 passed in 0.08s`
- Code-plus-test history anchors since 2016-01-01: `50`
- Code-plus-test anchors since 2018-01-01: `23`

## Shortlist

| repo_id | selected role | local-risk note | candidate supply |
|---|---|---|---:|
| `click_archive_smoke` | smoke | low: selected as smoke and generic comparator only; not used as primary target because runbook keeps archived Click material out of active target selection. | 14 |
| `toolz` | primary | low: selected primary: supports local Python 3.11.13, has 50 code-plus-test history anchors since 2016-01-01, and smoke command exited 0. | 50 |
| `humanize` | rejected_or_backup | low: backup only: observed supply is promising, but switching primary after toolz passed the local buildability and supply gates would expand Phase 0 scope. | 117 path-touching commits observed; code-plus-test count not fully certified |
| `itsdangerous` | rejected_or_backup | low: rejected for Phase 0 primary because task surface is smaller than toolz and overlaps Pallets/Click archive style. | medium |
| `boltons` | rejected_or_backup | low: backup candidate; broader utility surface but less immediately probed in this run. | medium |
| `attrs` | rejected_or_backup | low: rejected for Phase 0 primary because the test/dependency matrix is broader than needed for the smallest evidence chain. | high |
| `rich` | rejected_or_backup | medium: rejected for Phase 0 primary because terminal rendering snapshots and dependency breadth increase oracle flakiness risk. | high |
| `requests` | rejected_or_backup | medium: rejected for Phase 0 primary because HTTP integration history risks external-service assumptions. | high |

Acceptance: the primary target has deterministic local commands, low external-service risk, and enough mined anchors to attempt the 12-20 executable candidate target without model calls.
