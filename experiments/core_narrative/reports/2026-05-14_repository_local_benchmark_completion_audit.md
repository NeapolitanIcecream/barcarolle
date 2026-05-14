# Repository-Local Benchmark Completion Audit

Status: `not_complete_blocked_before_task_admission_and_primary_runs`

Objective file: `/Users/chenmohan/Downloads/barcarolle-research-0514-1.md`

## Verdict

The 2026-05-14 experiment is not complete as a full C/R/W* benchmark run. The completed work is a repository-admission and protocol-gate phase plus Rich W* direct-smoke, Golden-Oracle queue preparation, eleven accepted source-only Golden-Oracle pilots, three accepted replacement-oracle pilots, and one accepted direct-without-node Oracle pilot. Rich now has 20 accepted W* primary candidates, but the 5-task W* reserve target, C/R task construction, role artifacts, Rich ACUT variants, primary model runs, and R/W* analysis are still missing. Click primary execution remains blocked because Click has only 14 W* task-design candidates in the frozen `2026-02-14` to `2026-05-14` window, below the 20-task gate.

Do not mark the active goal complete from the current state. The next concrete unblocked step is continued Rich Golden-Oracle verifier construction and no-op/reference admission smoke for the remaining queued W* work items, or a separately preregistered gate revision.

## Prompt-To-Artifact Checklist

| Requirement | Status | Evidence | Gap |
|---|---|---|---|
| Pivot main line to repository-local benchmark generation and tuning validation; NFL only bonus | covered | `configs/repository_local_benchmark_20260514.yaml` | none |
| Freeze C/R/W* split at T0 `2026-05-14`; W* fixed to `2026-02-14`..`2026-05-14` | covered | `results/repository_local_benchmark_admission_20260514.json`, `configs/repository_local_benchmark_20260514.yaml` | none |
| Task 1: repository admission for Click/Rich/Black with counts, feasibility, family diversity, dependency risk, recommendation | partially covered | `reports/2026-05-14_repository_local_benchmark_admission.md`, `results/rich_task_admission_feasibility_20260514.json`, `results/rich_task_admission_readiness_20260514.json`, `results/rich_direct_smoke_batch_20260514.json`, `results/rich_source_oracle_queue_20260514.json`, `results/rich_source_oracle_pilot_20260514.json`, `results/rich_source_oracle_pilot_emoji_20260514.json`, `results/rich_source_oracle_pilot_linkids_20260514.json`, `results/rich_source_oracle_pilot_drop38_20260514.json`, `results/rich_source_oracle_pilot_svg_hash_20260514.json`, `results/rich_source_oracle_pilot_currentframe_20260514.json`, `results/rich_source_oracle_pilot_lazy_expandable_20260514.json`, `results/rich_source_oracle_pilot_emoji_main_20260514.json`, `results/rich_source_oracle_pilot_fix_docstring_20260514.json`, `results/rich_source_oracle_pilot_spelling_20260514.json`, `results/rich_source_oracle_pilot_remove_comments_20260514.json`, `results/rich_replacement_oracle_pilot_20260514.json`, `results/rich_replacement_oracle_pilot_zerospan_20260514.json`, `results/rich_replacement_oracle_pilot_vs16_20260514.json`, `results/rich_direct_without_nodes_oracle_pilot_20260514.json` | Rich collect-only feasibility, stricter readiness counts, direct-oracle W* smoke outcomes, the W* Golden-Oracle queue, eleven source-only W* Golden-Oracle admission pilots, three replacement-oracle admission pilots, and one direct-without-node Oracle pilot are measured; full denominator-scale per-task historical smoke and measured test runtime are not. |
| Task 2: Click C/R/W* construction with no-op/reference/leakage/family/difficulty/digests | partially covered for Rich W* primary only | `reports/2026-05-14_repository_local_benchmark_gate.md`, `reports/2026-05-14_rich_task_admission_readiness.md`, `reports/2026-05-14_rich_direct_smoke_batch.md`, `reports/2026-05-14_rich_source_oracle_queue.md`, `reports/2026-05-14_rich_source_oracle_pilot.md`, `reports/2026-05-14_rich_source_oracle_pilot_emoji.md`, `reports/2026-05-14_rich_source_oracle_pilot_linkids.md`, `reports/2026-05-14_rich_source_oracle_pilot_drop38.md`, `reports/2026-05-14_rich_source_oracle_pilot_svg_hash.md`, `reports/2026-05-14_rich_source_oracle_pilot_currentframe.md`, `reports/2026-05-14_rich_source_oracle_pilot_lazy_expandable.md`, `reports/2026-05-14_rich_source_oracle_pilot_emoji_main.md`, `reports/2026-05-14_rich_source_oracle_pilot_fix_docstring.md`, `reports/2026-05-14_rich_source_oracle_pilot_spelling.md`, `reports/2026-05-14_rich_source_oracle_pilot_remove_comments.md`, `reports/2026-05-14_rich_replacement_oracle_pilot.md`, `reports/2026-05-14_rich_replacement_oracle_pilot_zerospan.md`, `reports/2026-05-14_rich_replacement_oracle_pilot_vs16.md`, `reports/2026-05-14_rich_direct_without_nodes_oracle_pilot.md`, `reports/2026-05-14_rich_wstar_reserve_feasibility.md` | Click W* supply is below gate. Rich has 20 accepted W* primary candidates, but only 23 stricter W* design candidates, so the 5-task reserve target and 40-candidate pool target remain unmet. C and R task sets are not constructed, and no full denominator is frozen. |
| Task 3: Golden-Selector/Taskwright/Oracle/Auditor role isolation with prompt hashes, artifact digests, admission decisions | specified, not executed | `configs/repository_local_benchmark_20260514.yaml` | No 0514 role-run outputs or prompt hashes exist. |
| Task 4: ACUT/intervention manifests A0-A5, A4 limited to public statement + repo tree/source | partially covered | A0/A2/A3/A5 existing, A1/A4 Click variants added, `tools/repository_localization_hints.py` | Rich execution needs Rich or repository-neutral intervention variants. |
| Task 5: run R and W* one primary attempt per ACUT/task with fixed denominator and hidden verifier | not done | Gate report records non-action | No denominator was admitted; no primary attempts authorized or run. |
| Task 6: analyze R_score, W*_score, paired deltas, R-selected, W*-best, regret, correlation, family effects, ablation | not done | none | No primary result table exists. |
| Output: repository admission report | covered | `reports/2026-05-14_repository_local_benchmark_admission.md` | none |
| Output: task generation validity report | partial W* smoke only | `reports/2026-05-14_rich_direct_smoke_batch.md`, `reports/2026-05-14_rich_source_oracle_queue.md`, `reports/2026-05-14_rich_source_oracle_pilot.md`, `reports/2026-05-14_rich_source_oracle_pilot_emoji.md`, `reports/2026-05-14_rich_source_oracle_pilot_linkids.md`, `reports/2026-05-14_rich_source_oracle_pilot_drop38.md`, `reports/2026-05-14_rich_source_oracle_pilot_svg_hash.md`, `reports/2026-05-14_rich_source_oracle_pilot_currentframe.md`, `reports/2026-05-14_rich_source_oracle_pilot_lazy_expandable.md`, `reports/2026-05-14_rich_source_oracle_pilot_emoji_main.md`, `reports/2026-05-14_rich_source_oracle_pilot_fix_docstring.md`, `reports/2026-05-14_rich_source_oracle_pilot_spelling.md`, `reports/2026-05-14_rich_source_oracle_pilot_remove_comments.md`, `reports/2026-05-14_rich_replacement_oracle_pilot.md`, `reports/2026-05-14_rich_replacement_oracle_pilot_zerospan.md`, `reports/2026-05-14_rich_replacement_oracle_pilot_vs16.md`, `reports/2026-05-14_rich_direct_without_nodes_oracle_pilot.md`, `reports/2026-05-14_rich_wstar_reserve_feasibility.md` | Rich W* now has 20 accepted primary candidates through no-op/reference admission smoke: 5 direct-smoke, 11 source-only Golden-Oracle, 3 replacement-oracle, and 1 direct-without-node Oracle. Full C/R/W* task generation validity is not produced because W* reserve, R, and C task sets are missing. |
| Output: R/W* primary result report | not done | none | No primary attempts were run. |
| Output: decision-validity report | gate only | `reports/2026-05-14_repository_local_benchmark_gate.md` | R -> W* decision validity cannot be assessed without runs. |
| Output: threats-to-validity report | gate only | `reports/2026-05-14_repository_local_benchmark_gate.md` | Full experiment threats remain pending. |
| Prohibitions: do not use W* results to modify R, ACUT outputs to choose W*, old M5/M6 denominator mixing, post-hoc gate lowering, W* freshness overclaiming | covered for actions taken | Gate and protocol artifacts | Verified only for repository-admission/gate phase because no primary results exist. |

## Evidence Inspected

- `experiments/core_narrative/results/repository_local_benchmark_admission_20260514.json`
- `experiments/core_narrative/reports/2026-05-14_repository_local_benchmark_admission.md`
- `experiments/core_narrative/reports/2026-05-14_repository_local_benchmark_gate.md`
- `experiments/core_narrative/configs/repository_local_benchmark_20260514.yaml`
- `experiments/core_narrative/results/rich_task_admission_feasibility_20260514.json`
- `experiments/core_narrative/results/rich_task_admission_readiness_20260514.json`
- `experiments/core_narrative/results/rich_direct_smoke_pilot_20260514.json`
- `experiments/core_narrative/results/rich_direct_smoke_batch_20260514.json`
- `experiments/core_narrative/results/rich_direct_smoke_batch_diagnostics_20260514.json`
- `experiments/core_narrative/results/rich_source_oracle_queue_20260514.json`
- `experiments/core_narrative/results/rich_source_oracle_pilot_20260514.json`
- `experiments/core_narrative/results/rich_source_oracle_pilot_emoji_20260514.json`
- `experiments/core_narrative/results/rich_source_oracle_pilot_linkids_20260514.json`
- `experiments/core_narrative/results/rich_source_oracle_pilot_drop38_20260514.json`
- `experiments/core_narrative/results/rich_source_oracle_pilot_svg_hash_20260514.json`
- `experiments/core_narrative/results/rich_source_oracle_pilot_currentframe_20260514.json`
- `experiments/core_narrative/results/rich_source_oracle_pilot_lazy_expandable_20260514.json`
- `experiments/core_narrative/results/rich_source_oracle_pilot_emoji_main_20260514.json`
- `experiments/core_narrative/results/rich_source_oracle_pilot_fix_docstring_20260514.json`
- `experiments/core_narrative/results/rich_source_oracle_pilot_spelling_20260514.json`
- `experiments/core_narrative/results/rich_source_oracle_pilot_remove_comments_20260514.json`
- `experiments/core_narrative/results/rich_wstar_reserve_feasibility_20260514.json`
- `experiments/core_narrative/results/rich_replacement_oracle_pilot_20260514.json`
- `experiments/core_narrative/results/rich_replacement_oracle_pilot_zerospan_20260514.json`
- `experiments/core_narrative/results/rich_replacement_oracle_pilot_vs16_20260514.json`
- `experiments/core_narrative/results/rich_direct_without_nodes_oracle_pilot_20260514.json`
- ACUT manifests for A0-A5, including the newly added A1 and A4 Click variants.
- `experiments/core_narrative/tools/repository_local_benchmark_admission.py`
- `experiments/core_narrative/tools/repository_localization_hints.py`

## Additional Feasibility Observation

Rich ambient collect-only check:

```text
cwd: experiments/core_narrative/external_repos/rich
command: python3 -m pytest -q --collect-only tests
exit_code: 2
observed: 919 tests collected before 4 collection errors
missing imports: markdown_it, attr
```

`pyproject.toml` declares `markdown-it-py` as a project dependency and `attrs` as a dev dependency, so Rich task admission should use an isolated install that includes project and dev/test dependencies. This does not block Rich repository admission, but it remains a concrete dependency-readiness task before smoke-tested task admission.

Follow-up isolated check:

```text
setup: python3 -m venv /tmp/barcarolle-rich-feasibility-venv
setup: pip install -e . pytest attrs
command: /tmp/barcarolle-rich-feasibility-venv/bin/python -m pytest -q --collect-only tests
exit_code: 0
observed: 981 tests collected in 0.52s
```

This narrows the dependency-feasibility gap for Rich. It is still not task admission, because no historical base workspaces, no hidden verifiers, no no-op failures, and no reference-patch passes were checked.

Rich task-admission readiness:

```text
artifact: experiments/core_narrative/results/rich_task_admission_readiness_20260514.json
R: 37 design candidates, 12 direct smoke-ready, 3 short of the 40-candidate pool target
W*: 23 design candidates, 8 direct smoke-ready, 14 source-only requiring Golden-Oracle, 17 short of the 40-candidate pool target
```

This is stricter than repository admission because it deduplicates normalized subjects and requires extractable pytest nodes for direct smoke readiness. It still does not admit tasks.

Rich direct-smoke pilot:

```text
artifact: experiments/core_narrative/results/rich_direct_smoke_pilot_20260514.json
scope: one W* direct-oracle candidate
no-op status: failed
reference status: passed
admission decision: accepted
model calls: 0
```

This admits one pilot candidate only. It does not freeze a denominator or authorize any primary model attempt.

Rich direct-smoke batch:

```text
artifact: experiments/core_narrative/results/rich_direct_smoke_batch_20260514.json
scope: all 8 current Rich W* direct-oracle candidates
accepted: 5
rejected: 3
blocked: 1
no-op statuses: failed=5, passed_unexpected=2, blocked_timeout=1
reference statuses: passed=8
model calls: 0
```

This advances task admission for the direct-oracle subset only. It remains below the 20-primary denominator target and does not include source-only candidates requiring Golden-Oracle construction.

Rejected direct-smoke diagnostics:

```text
artifact: experiments/core_narrative/results/rich_direct_smoke_batch_diagnostics_20260514.json
non-discriminating existing tests: 2
no-op timeout or hanging verifier: 1
```

The next admission step is to build replacement Golden-Oracle verifiers for no-op-passing tests and prune or replace the timeout verifier. This still remains short of a denominator.

Rich Golden-Oracle construction queue:

```text
artifact: experiments/core_narrative/results/rich_source_oracle_queue_20260514.json
accepted direct W* tasks: 5
oracle work items: 18
composition: source-only=14, direct-tests-without-nodes=1, direct-smoke replacement=3
additional acceptances needed for 20 primary: 15
maximum admitted design count if all queued oracles pass: 23
can reach 20 primary if all queued oracles pass: true
can reach 20 primary + 5 reserve under current design supply: false
40-candidate pool gap: 17
```

This queue is redacted and machine-readable, but it is not task admission. It identifies the next hidden-verifier construction work after the direct-smoke batch and keeps raw commits, raw subjects, source file lists, and private smoke details in ignored private artifacts.

Rich source-only Golden-Oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_source_oracle_pilot_20260514.json
scope: one W* source-only Golden-Oracle candidate
oracle template: markdown_inline_kbd_html
no-op status: failed
reference status: passed
admission decision: accepted
accepted W* tasks after pilot: 6
additional acceptances needed for 20 primary: 14
model calls: 0
```

Emoji source-only Golden-Oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_source_oracle_pilot_emoji_20260514.json
scope: one W* source-only Golden-Oracle candidate
oracle template: emoji_code_table_lazy_import
no-op status: failed
reference status: passed
admission decision: accepted
accepted W* tasks after pilot: 7
additional acceptances needed for 20 primary: 13
model calls: 0
```

Link-ID source-only Golden-Oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_source_oracle_pilot_linkids_20260514.json
scope: one W* source-only Golden-Oracle candidate
oracle template: style_link_id_counter_sequence
no-op status: failed
reference status: passed
admission decision: accepted
accepted W* tasks after pilot: 8
additional acceptances needed for 20 primary: 12
model calls: 0
```

Replacement-oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_replacement_oracle_pilot_20260514.json
scope: one rejected W* direct-smoke candidate
oracle template: split_graphemes_leading_zero_width_timeout
prior no-op status: passed_unexpected
replacement no-op status: failed
reference status: passed
admission decision: accepted
accepted W* tasks after pilot: 9
additional acceptances needed for 20 primary: 11
model calls: 0
```

Zero-width-span replacement-oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_replacement_oracle_pilot_zerospan_20260514.json
scope: one rejected W* direct-smoke candidate
oracle template: split_graphemes_leading_zero_width_span
prior no-op status: blocked_timeout
replacement no-op status: failed
reference status: passed
admission decision: accepted
accepted W* tasks after pilot: 10
additional acceptances needed for 20 primary: 10
model calls: 0
```

VS16 replacement-oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_replacement_oracle_pilot_vs16_20260514.json
scope: one rejected W* direct-smoke candidate
oracle template: split_graphemes_leading_zero_width_variation_selector
prior no-op status: passed_unexpected
replacement no-op status: failed
reference status: passed
admission decision: accepted
accepted W* tasks after pilot: 11
additional acceptances needed for 20 primary: 9
model calls: 0
```

Direct-without-node Oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_direct_without_nodes_oracle_pilot_20260514.json
scope: one W* direct-tests-without-extractable-nodes candidate
oracle template: import_side_effects_lazy_inspect_console
no-op status: failed
reference status: passed
admission decision: accepted
accepted W* tasks after pilot: 12
additional acceptances needed for 20 primary: 8
model calls: 0
```

Drop-3.8 source-only Golden-Oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_source_oracle_pilot_drop38_20260514.json
scope: one W* source-only Golden-Oracle candidate
oracle template: console_save_pathlike_str_annotations
no-op status: failed
reference status: passed
admission decision: accepted
accepted W* tasks after pilot: 13
additional acceptances needed for 20 primary: 7
model calls: 0
```

SVG-hash source-only Golden-Oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_source_oracle_pilot_svg_hash_20260514.json
scope: one W* source-only Golden-Oracle candidate
oracle template: console_dead_svg_hash_removed
no-op status: failed
reference status: passed
admission decision: accepted
accepted W* tasks after pilot: 14
additional acceptances needed for 20 primary: 6
model calls: 0
```

Currentframe source-only Golden-Oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_source_oracle_pilot_currentframe_20260514.json
scope: one W* source-only Golden-Oracle candidate
oracle template: console_caller_frame_currentframe_none
no-op status: failed
reference status: passed
admission decision: accepted
accepted W* tasks after pilot: 15
additional acceptances needed for 20 primary: 5
model calls: 0
```

Lazy-expandable source-only Golden-Oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_source_oracle_pilot_lazy_expandable_20260514.json
scope: one W* source-only Golden-Oracle candidate
oracle template: console_collect_renderables_lazy_pretty_import
no-op status: failed
reference status: passed
admission decision: accepted
accepted W* tasks after pilot: 16
additional acceptances needed for 20 primary: 4
model calls: 0
```

Emoji-main source-only Golden-Oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_source_oracle_pilot_emoji_main_20260514.json
scope: one W* source-only Golden-Oracle candidate
oracle template: emoji_module_main_lazy_codes_import
no-op status: failed
reference status: passed
admission decision: accepted
accepted W* tasks after pilot: 17
additional acceptances needed for 20 primary: 3
model calls: 0
```

Fix-docstring source-only Golden-Oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_source_oracle_pilot_fix_docstring_20260514.json
scope: one W* source-only Golden-Oracle candidate
oracle template: console_caller_frame_docstring_none_default
no-op status: failed
reference status: passed
admission decision: accepted
accepted W* tasks after pilot: 18
additional acceptances needed for 20 primary: 2
model calls: 0
```

Spelling source-only Golden-Oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_source_oracle_pilot_spelling_20260514.json
scope: one W* source-only Golden-Oracle candidate
oracle template: cells_split_graphemes_docstring_spelling
no-op status: failed
reference status: passed
admission decision: accepted
accepted W* tasks after pilot: 19
additional acceptances needed for 20 primary: 1
model calls: 0
```

Remove-comments source-only Golden-Oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_source_oracle_pilot_remove_comments_20260514.json
scope: one W* source-only Golden-Oracle candidate
oracle template: markdown_tabledata_stale_comments_removed
no-op status: failed
reference status: passed
admission decision: accepted
accepted W* tasks after pilot: 20
additional acceptances needed for 20 primary: 0
model calls: 0
```

Together these admit eleven source-only Rich W* tasks, three replacement-oracle W* tasks, and one direct-without-node W* task through no-op/reference smoke. Rich W* has 20 accepted primary candidates, but it still lacks the 5 reserve tasks and does not freeze a full C/R/W* denominator or authorize any primary model attempt.

Rich W* reserve feasibility:

```text
artifact: experiments/core_narrative/results/rich_wstar_reserve_feasibility_20260514.json
accepted W* primary candidates: 20
remaining unadmitted W* design candidates: 3
maximum possible W* admissions under current scan: 23
reserve gap even if all remaining are admitted: 2
candidate-pool gap: 17
primary runs authorized: false
```

## Verification Commands

Completed during the gate, queue, and pilot phases:

```text
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments/core_narrative/tools/test_repository_local_benchmark_admission.py experiments/core_narrative/tools/test_repository_localization_hints.py
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments/core_narrative/tools/test_rich_task_admission_readiness.py experiments/core_narrative/tools/test_rich_direct_smoke_pilot.py
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments/core_narrative/tools/test_rich_source_oracle_pilot.py experiments/core_narrative/tools/test_rich_source_oracle_queue.py experiments/core_narrative/tools/test_rich_direct_smoke_batch.py experiments/core_narrative/tools/test_rich_direct_smoke_pilot.py experiments/core_narrative/tools/test_rich_task_admission_readiness.py experiments/core_narrative/tools/test_repository_local_benchmark_admission.py experiments/core_narrative/tools/test_repository_localization_hints.py experiments/core_narrative/tools/test_m6_w3_task_admission.py experiments/core_narrative/tools/test_workspace_mode_runner.py experiments/core_narrative/tools/test_rgw_status_semantics.py
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments/core_narrative/tools/test_m6_w3_freeze_integrity_audit.py experiments/core_narrative/tools/test_m6_w3_task_admission.py
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments/core_narrative/tools/test_apply_source_derived_url_policy.py experiments/core_narrative/tools/test_workspace_mode_runner.py experiments/core_narrative/tools/test_rgw_status_semantics.py
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/validate_acut_manifest.py experiments/core_narrative/configs/acuts/cheap-click-inert-control-v1.yaml experiments/core_narrative/configs/acuts/cheap-click-localization-tool-v1.yaml
python3 -m json.tool experiments/core_narrative/results/repository_local_benchmark_gate_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_source_oracle_queue_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_source_oracle_pilot_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_source_oracle_pilot_emoji_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_source_oracle_pilot_linkids_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_source_oracle_pilot_drop38_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_source_oracle_pilot_svg_hash_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_source_oracle_pilot_currentframe_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_source_oracle_pilot_lazy_expandable_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_source_oracle_pilot_emoji_main_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_source_oracle_pilot_fix_docstring_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_source_oracle_pilot_spelling_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_source_oracle_pilot_remove_comments_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_wstar_reserve_feasibility_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_replacement_oracle_pilot_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_replacement_oracle_pilot_zerospan_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_replacement_oracle_pilot_vs16_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_direct_without_nodes_oracle_pilot_20260514.json
python3 -m json.tool experiments/core_narrative/results/repository_local_benchmark_completion_audit_20260514.json
git diff --check
```

These commands verify the committed gate and queue tools and manifests. They do not verify the missing task admission, model runs, or R/W* analysis because those phases have not been executed.

## Next Work

Proceed with Rich reserve feasibility review or R/C task construction only after an explicit decision on the reserve gate. Rich currently has 20 accepted W* primary candidates: 5 direct-smoke tasks, 11 source-only Golden-Oracle pilots, 3 replacement-oracle pilots, and 1 direct-without-node Oracle pilot. The 5-reserve target, 40-candidate pool target, C/R task sets, role artifacts, Rich ACUT variants, primary runs, and analysis remain unmet.
