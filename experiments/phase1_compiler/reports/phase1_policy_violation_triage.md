# Phase 1 Policy Violation Triage

Status: facts recorded, classification deferred.

## Cell

- Original result prefix: `phase1_two_repo_future_holdout_attrs_h_future`.
- Repo: `attrs`.
- Split: `H_future`.
- Task: `attrs__hist__027`.
- Adapter: `kilo_workspace`.
- ACUT: `kilo_workspace_gpt_5_4_mini`.
- Score-table terminal status: `policy_violation`.
- Verifier harness error: `submission_edited_out_of_scope_paths`.

## Scope Evidence

Certified task metadata lists these changed files:

- `changelog.d/774.change.rst`
- `conftest.py`
- `src/attr/__init__.pyi`
- `src/attr/_funcs.py`
- `tests/test_hooks.py`

Certified test files:

- `tests/test_hooks.py`

Allowed context refs:

- `issue:766`

The target commit diff from `ad59a62cae7f1f5355fb121d77eda5d5d1aa0cbd` to `ce8bb4ffa9d4b4c3cc034e497be6809840c2a53a` changes the same five paths listed in the certified metadata. It does not change `src/attr/_make.py`.

The current package metadata allows these code paths:

- `changelog.d/774.change.rst`
- `conftest.py`
- `src/attr/__init__.pyi`
- `src/attr/_funcs.py`

## Submission Evidence

The captured submission changed:

- `conftest.py`
- `src/attr/_make.py`

The verifier reports the violating path as:

- `src/attr/_make.py`

The solver did not edit the certified test file `tests/test_hooks.py`. It did edit `conftest.py`, which is allowed by the current package metadata and target-commit path evidence. It also edited `src/attr/_make.py`, which is outside the certified changed files, outside the allowed code paths, and outside the target-commit changed files.

Raw patch evidence is recorded only as a digest and diffstat:

- SHA256: `fa4d16b4cde49b507aced1ca7a65177a3d3fe96a56698a2f87ee63a12b7a3dab`
- Diffstat:
  - `conftest.py       |    1 -`
  - `src/attr/_make.py |    6 +++++-`
  - `2 files changed, 5 insertions(+), 2 deletions(-)`

## Reporting Repair Check

After repairing the metrics join, `phase1_two_repo_future_holdout_prediction_metrics.json` preserves the verifier detail:

- `harness_error`: `submission_edited_out_of_scope_paths`
- `changed_paths`: `["src/attr/_make.py"]`

## Boundary

This report uses score, submission, verifier policy detail, certified task metadata, package inspection metadata, target-commit path evidence, and raw patch hash/diffstat only. It does not include raw prompts, raw completions, ACUT transcripts, raw patch bodies, or hidden verifier outcome material. Classification is recorded separately.
