# M2 Non-Persistent Verifier Channel

Date: 2026-05-10

## Scope

- Follow-up after PR #19 / PR11 unsafe artifact attribution.
- Target cell: `cheap-generic-swe` x `click__rwork__006`.
- Contract: `anchored-search-replace-json-v3`.
- Goal: preserve the no-raw-URL patch artifact policy while making source-derived-overbreadth submissions verifier-attemptable through a non-persistent channel.

## Implementation

- `apply_and_verify.py` can now redact verifier stdout/stderr artifacts when invoked with `--redact-verifier-artifacts`.
- `codex_nfl_experiment_runner.py` now recognizes the narrow source-derived unsafe patch-artifact case:
  - unsafe patch artifact was rejected before raw write;
  - attribution says all unsafe reasons are source-derived;
  - generated full URL count is zero;
  - search/replace edits were already validated and applied in the isolated runner workspace.
- Eligible runs invoke the verifier from that already-applied workspace with `--skip-apply`; metadata records `nonpersistent_preapplied_workspace` and keeps `verifier_ready_patch_available=false`.
- Non-persistent verifier results are scoreable only if transient workspace cleanup records `removed=true`; cleanup exceptions or `removed=false` force `infra_failed` with `failure_class=nonpersistent_transient_workspace_cleanup_failed`.
- `openclaw_direct_runner.py` now preserves the more specific redacted-source placeholder diagnostic when the redacted search text matches raw source.

## Evidence

| Evidence | Mode | Status | Patch-ready | Non-persistent verifier | Model call | Notes |
| --- | --- | --- | ---: | ---: | ---: | --- |
| `m2_nonpersistent_verifier_channel_replay_20260510` | mock replay | `failed` | `False` | `True` | `False` | Source-derived URL overbreadth was verifier-attempted without `submission.patch`; verifier exit code was `1`; transient workspace was removed after verification. |
| `m2_nonpersistent_verifier_channel_live_smoke_20260510` | live | `invalid_submission` | `True` | `False` | `True` | Live model produced a raw-safe patch artifact; clean patch application failed before verifier execution. |

Machine report: `experiments/core_narrative/results/m2_nonpersistent_verifier_channel_20260510.json`.

## Policy Checks

- Source-derived full URL in removed context: verifier attempted through `nonpersistent_preapplied_workspace`; no raw patch artifact was written; transient workspace cleanup recorded `removed=true`.
- Cleanup failure regression: simulated transient workspace cleanup exception produced `infra_failed` and `scoreable=false`.
- Model-generated full URL: remains rejected; verifier not attempted.
- Redaction placeholder persistence: remains rejected; verifier not attempted.
- Metadata separates non-persistent verifier attempts from verifier-ready patch artifacts via `patch_readiness`, `verifier_attempt`, and `nonpersistent_verifier_channel`.
- Raw URL scan over report JSON, normalized JSON, redacted provider responses, redacted previews, and verifier stdout/stderr where present found zero raw URL paths.

## Verification

- `PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments.core_narrative.tools.test_codex_nfl_experiment_runner` passed (`25` tests).
- `PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments.core_narrative.tools.test_openclaw_direct_runner` passed (`38` tests).
- `PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments.core_narrative.tools.test_m2_unsafe_artifact_repair experiments.core_narrative.tools.test_run_task` passed (`4` tests).
- One no-model target replay was regenerated after the cleanup fix.
- The prior bounded cheap live smoke remains attached; it was not rerun for this cleanup-only fix because it used the verifier-ready patch artifact path, not the non-persistent transient-workspace branch. Its ledger appended estimated cost was `0.055751` USD with provider usage reported.

## Claim Boundaries

This package measures verifier-attemptability for the source-derived-overbreadth case. It does not claim M2 passed, ranking reversal, task-solving improvement, capability uplift, G_score predictivity, G0-G5 outcomes, license, admission, or authorization.
