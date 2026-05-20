# Unsafe Generated Text Triage Report

Date: 2026-05-09

## Research Question

For the four M1.1 `unsafe_generated_text` cells, did the failure represent a safety-policy true positive, a safety-policy false positive, prompt/applicator overbreadth, provider/artifact ambiguity, or another explicitly justified category?

This report is no-model triage. It makes no task-solving improvement claim, no capability uplift claim, no G-score predictivity claim, and no ranking reversal claim.

## Method

Inputs:

- `experiments/core_narrative/results/codex_nfl_m1_1_structured_20260509.json`
- Per-cell normalized M1.1 artifacts under `experiments/core_narrative/results/normalized/`
- Per-cell redacted raw artifacts under `experiments/core_narrative/results/raw/`
- M1.1 and M2 reports/results from 2026-05-09
- `/Users/chenmohan/Documents/barcarolle-agent-license-research-report-2026-05-09-v4.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0509-2.md`

Scope:

- ACUTs: `cheap-generic-swe`, `cheap-click-specialist`
- Tasks: `click__rwork__004`, `click__rwork__006`
- Fixed denominator: 4 cells

The triage tooling read only existing batch JSON, normalized JSON, runner-result metadata, redacted provider-response artifacts, and workspace status metadata. It did not call any model or provider API. It reports counts, booleans, contract markers, safe relative paths, and changed path names only. It does not copy unsafe spans, credentials, or full URLs.

## Artifact

Machine-readable output:

- `experiments/core_narrative/results/unsafe_generated_text_triage_20260509.json`

Tooling and tests:

- `experiments/core_narrative/tools/unsafe_generated_text_triage.py`
- `experiments/core_narrative/tools/test_unsafe_generated_text_triage.py`

The output leakage guard reports `contains_raw_unsafe_text: false`.

## Results

| Task | ACUT | Classification | Reason counts | Redacted provider URL markers | Patch written | Workspace mutation | Enough redacted evidence |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| `click__rwork__004` | `cheap-generic-swe` | `prompt_or_applicator_overbreadth` | `full_url`: 3 | 3 | no | yes | yes |
| `click__rwork__004` | `cheap-click-specialist` | `prompt_or_applicator_overbreadth` | `full_url`: 3 | 3 | no | yes | yes |
| `click__rwork__006` | `cheap-generic-swe` | `prompt_or_applicator_overbreadth` | `full_url`: 36 | 0 | no | yes | yes |
| `click__rwork__006` | `cheap-click-specialist` | `prompt_or_applicator_overbreadth` | `full_url`: 36 | 0 | no | yes | yes |

Aggregate:

- Classification counts: `prompt_or_applicator_overbreadth`: 4
- Total unsafe reason counts: `full_url`: 78
- Secret/credential reason counts: none
- Patch files written: 0
- Workspace mutations observed before rejection: 4
- Contract markers: all target cells consistently report `structured-files-json-v1`
- Fixed denominator: 4/4 cells present, 0 missing, 0 duplicate target rows

## Interpretation

All four cells were rejected after model output had already mutated the temporary workspace but before `submission.patch` was written. The only positive safety reason was `full_url`; there were no resolved environment values, Authorization-header credential strings, provider-token patterns, or credential-literal findings in the recorded reason counts.

The safest interpretation is that these four M1.1 failures are scoreability and artifact-policy failures, not evidence of dangerous credential leakage. The current pipeline labels them as `unsafe_generated_text` because the patch artifact safety check rejects full URL-like text while collecting a diff. In these cells, the useful classification is therefore `prompt_or_applicator_overbreadth`: the prompt/applicator/patch-artifact boundary is too broad for scoreability because it can reject generated patch artifacts after workspace mutation without producing a verifier-ready patch.

For `click__rwork__004`, the redacted provider artifacts contain redacted URL markers and the rejected patch path was never written. For `click__rwork__006`, the redacted provider artifacts contain no URL markers, yet the runner metadata counted many `full_url` findings during patch-artifact collection. That pattern is especially consistent with patch/diff collection overbreadth rather than a provider-response safety issue.

## Implications

For M2 scoreability:

- This triage does not make the M1.1 cells scoreable. They remain `invalid_submission` because no safe patch artifact was written and no verifier ran.
- The M1.1 structured path's `unsafe_generated_text` count should be treated as an output-contract/artifact-policy blocker when comparing scoreability paths.
- M2's live scoreability gate remains not met. This triage narrows one failure source but does not improve live patch-ready coverage by itself.

For M3:

- Proceeding to M3 predictivity work should still require a live path with adequate scoreability, or an explicit scoreability-normalized analysis plan that keeps these invalid cells separate from verifier failures.
- These four cells should not be reinterpreted as task failures, passes, model capability evidence, or ranking evidence.
- A follow-up fix should separate provider-response safety checks from patch-artifact safety checks, and should preserve the no-raw-URL/no-secret artifact policy.

## Reproduction

Generate the triage JSON:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/unsafe_generated_text_triage.py \
  --batch experiments/core_narrative/results/codex_nfl_m1_1_structured_20260509.json \
  --output experiments/core_narrative/results/unsafe_generated_text_triage_20260509.json
```

Focused tests:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/core_narrative/tools python3 -B -m unittest \
  experiments.core_narrative.tools.test_unsafe_generated_text_triage
```

Compile check:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 -m py_compile \
  experiments/core_narrative/tools/unsafe_generated_text_triage.py \
  experiments/core_narrative/tools/test_unsafe_generated_text_triage.py
```

## Limitations

The report intentionally does not publish exact unsafe spans or full URLs. The classification is based on redacted provider artifacts, runner metadata, and workspace status metadata. It can distinguish category-level failure source, but it should not be used to recover the original unsafe text or to claim that a candidate patch would have passed verification.
