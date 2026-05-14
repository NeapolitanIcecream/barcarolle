# Repository-Local Benchmark Completion Audit

Status: `completed_blocked_before_primary_runs_under_frozen_0514_protocol`

Objective file: `/Users/chenmohan/Downloads/barcarolle-research-0514-1.md`

## Verdict

The 2026-05-14 experiment is complete as a blocked experiment under the frozen 0514 protocol, not as a full C/R/W* primary benchmark run. The completed work is a repository-admission and protocol-gate phase plus Rich W* direct-smoke, Golden-Oracle queue preparation, eleven accepted source-only Golden-Oracle pilots, three accepted replacement-oracle pilots, one accepted direct-without-node Oracle pilot, one Rich R direct-smoke batch with 8 accepted direct tasks, one Rich R Golden-Oracle queue, seventeen accepted Rich R source-only Golden-Oracle pilots, Rich C admission through direct smoke plus all queued C Oracle pilots, Rich A0-A5 intervention manifests, an explicit Rich W* reserve-gate decision, and a terminal blocked-report artifact. Rich now has 20 accepted W* primary candidates, 25 accepted R primary-plus-reserve candidates, 20 accepted C calibration candidates, and Rich-ready A0-A5 ACUT variants. The explicit W* reserve-gate decision blocks primary execution under the frozen 0514 protocol because the scan cannot reach the 5-reserve target or 40-candidate pool target. Role artifacts, primary model runs, and R/W* analysis are therefore not applicable inside this frozen protocol line. Click primary execution remains blocked because Click has only 14 W* task-design candidates in the frozen `2026-02-14` to `2026-05-14` window, below the 20-task gate.

The selected terminal path is to stop before primary runs and report the line as blocked by W* reserve/candidate-pool supply. No further primary-run or analysis work is authorized inside the frozen 0514 protocol. Future work requires a new owner decision: preregister a protocol revision, find additional eligible W* candidates inside the frozen window, or treat the blocked report as the terminal result.

## Prompt-To-Artifact Checklist

| Requirement | Status | Evidence | Gap |
|---|---|---|---|
| Pivot main line to repository-local benchmark generation and tuning validation; NFL only bonus | covered | `configs/repository_local_benchmark_20260514.yaml` | none |
| Freeze C/R/W* split at T0 `2026-05-14`; W* fixed to `2026-02-14`..`2026-05-14` | covered | `results/repository_local_benchmark_admission_20260514.json`, `configs/repository_local_benchmark_20260514.yaml` | none |
| Task 1: repository admission for Click/Rich/Black with counts, feasibility, family diversity, dependency risk, recommendation | partially covered | `reports/2026-05-14_repository_local_benchmark_admission.md`, Rich readiness/smoke/oracle artifacts for W*, R, and C | Rich collect-only feasibility, stricter readiness counts, direct-oracle W*, R, and C smoke outcomes, the W*, R, and C Golden-Oracle queues, eleven source-only W* Golden-Oracle admission pilots, seventeen source-only R Golden-Oracle admission pilots, and all queued C Oracle admission pilots are measured. Rich C now has 20 accepted calibration candidates. Full denominator-scale per-task historical smoke and measured test runtime are not yet measured. |
| Task 2: Click C/R/W* construction with no-op/reference/leakage/family/difficulty/digests | completed with terminal W* reserve/candidate-pool gate block | Rich W*/R admission reports plus Rich C readiness, direct-smoke, source-only, replacement, and direct-without-node pilot reports; final blocked report | Click W* supply is below gate. Rich has 20 accepted W* primary candidates, but only 23 stricter W* design candidates, so the explicit W* reserve-gate decision fails the 5-task reserve target and 40-candidate pool target. Rich R has 25 accepted tasks: 8 direct-smoke and 17 source-only Golden-Oracle, satisfying the 20-primary plus 5-reserve count. Rich C has 20 accepted calibration tasks: 3 direct-smoke, 13 source-only Golden-Oracle, 3 replacement-oracle, and 1 direct-without-node Oracle. The final blocked report records that no full C/R/W* denominator or primary run is permitted under the frozen 0514 gate. |
| Task 3: Golden-Selector/Taskwright/Oracle/Auditor role isolation with prompt hashes, artifact digests, admission decisions | specified, not executed | `configs/repository_local_benchmark_20260514.yaml` | No 0514 role-run outputs or prompt hashes exist. |
| Task 4: ACUT/intervention manifests A0-A5, A4 limited to public statement + repo tree/source | covered for Rich execution plan | Rich A1/A2/A3/A4 manifests, generic A0/A5 manifests, Rich context packs, `tools/repository_localization_hints.py` | No primary attempts authorized or run. |
| Task 5: run R and W* one primary attempt per ACUT/task with fixed denominator and hidden verifier | not applicable, blocked before primary runs | Gate report, W* reserve-gate decision, and final blocked report record non-action | Explicit W* reserve-gate decision blocks primary execution under the frozen 0514 protocol; no primary attempts authorized or run. |
| Task 6: analyze R_score, W*_score, paired deltas, R-selected, W*-best, regret, correlation, family effects, ablation | not applicable, no primary results | final blocked report | No primary result table exists because primary runs were not authorized. |
| Output: repository admission report | covered | `reports/2026-05-14_repository_local_benchmark_admission.md` | none |
| Output: task generation validity report | completed with terminal W* gate block | Rich W*/R admission reports plus Rich C readiness, direct-smoke, source-only, replacement, and direct-without-node pilot reports; final blocked report | Rich C has 20 accepted calibration candidates, Rich W* has 20 accepted primary candidates, and Rich R has 25 accepted candidates after 8 direct-smoke acceptances and 17 source-only Golden-Oracle pilots. The final validity conclusion is blocked because the explicit W* reserve-gate decision prevents the frozen 0514 primary run. |
| Output: R/W* primary result report | not applicable, blocked before primary runs | final blocked report | No primary attempts were run or authorized. |
| Output: decision-validity report | not applicable, no primary results | final blocked report | R -> W* decision validity cannot be assessed without primary results. |
| Output: threats-to-validity report | completed for terminal gate result | `reports/2026-05-15_repository_local_benchmark_final_blocked_report.md` | The terminal threat is supply/gate failure before primary execution; full run-level threats are not applicable without primary runs. |
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
- `experiments/core_narrative/results/rich_r_direct_smoke_batch_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_queue_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_split_lines_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_cache_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_traceback_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_progress_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_py38_cache_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_unicode_load_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_unicode_invalid_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_cell_string_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_cell_table_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_split_text_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_pretty_console_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_progress_docstring_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_cells_simplify_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_cells_refine_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_unicode_comment_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_unicode_cell_table_20260515.json`
- `experiments/core_narrative/results/rich_r_source_oracle_pilot_table_doc_20260515.json`
- `experiments/core_narrative/results/rich_c_extended_task_admission_readiness_20260515.json`
- `experiments/core_narrative/results/rich_c_direct_smoke_batch_20260515.json`
- `experiments/core_narrative/results/rich_c_source_oracle_queue_20260515.json`
- Rich C source-only, replacement-oracle, and direct-without-node pilot result artifacts from `2026-05-15`.
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
- `experiments/core_narrative/results/rich_wstar_reserve_gate_decision_20260515.json`
- `experiments/core_narrative/results/repository_local_benchmark_final_blocked_report_20260515.json`
- `experiments/core_narrative/results/rich_replacement_oracle_pilot_20260514.json`
- `experiments/core_narrative/results/rich_replacement_oracle_pilot_zerospan_20260514.json`
- `experiments/core_narrative/results/rich_replacement_oracle_pilot_vs16_20260514.json`
- `experiments/core_narrative/results/rich_direct_without_nodes_oracle_pilot_20260514.json`
- ACUT manifests for Rich A0-A5, including Rich A1 inert, A2 static context, A3 C-derived playbook, and A4 localization-tool variants.
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

Rich R direct-smoke batch:

```text
artifact: experiments/core_narrative/results/rich_r_direct_smoke_batch_20260515.json
scope: all 12 current Rich R direct-oracle candidates
accepted: 8
rejected: 4
blocked: 2
no-op statuses: failed=9, passed_unexpected=1, blocked_pytest_collection=2
reference statuses: passed=9, failed=3
model calls: 0
```

This started R task admission but did not complete the R denominator. After this direct batch, Rich R still needed at least 12 more accepted tasks to reach 20 primary and 17 more to reach 20 primary plus 5 reserve.

Rich R Golden-Oracle construction queue:

```text
artifact: experiments/core_narrative/results/rich_r_source_oracle_queue_20260515.json
accepted direct R tasks: 8
oracle work items: 29
composition: source-only=25, direct-smoke replacement=4
additional acceptances needed for 20 R primary: 12
additional acceptances needed for 20 R primary + 5 reserve: 17
maximum admitted design count if all queued oracles pass: 37
can reach 20 R primary if all queued oracles pass: true
can reach 20 R primary + 5 reserve under current design supply: true
40-candidate pool gap: 3
model calls: 0
```

This queue is redacted and machine-readable, but it is not task admission. It identifies the next hidden-verifier construction work after the R direct-smoke batch. Raw commits, raw subjects, source file lists, and private smoke details remain only in ignored private artifacts.

Rich R source-only Golden-Oracle pilot:

```text
artifact: experiments/core_narrative/results/rich_r_source_oracle_pilot_split_lines_20260515.json
scope: one R source-only Golden-Oracle candidate
oracle template: segment_split_lines_terminator
no-op status: failed
reference status: passed
admission decision: accepted
accepted R tasks after pilot: 9
additional acceptances needed for 20 R primary: 11
additional acceptances needed for 20 R primary + 5 reserve: 16
remaining queued R oracle work items: 28
model calls: 0
```

This admits one R source-only candidate through no-op/reference smoke. It does not freeze an R denominator or authorize primary model attempts.

Rich R source-only Golden-Oracle primary-completion batch:

```text
artifacts:
- experiments/core_narrative/results/rich_r_source_oracle_pilot_split_lines_20260515.json
- experiments/core_narrative/results/rich_r_source_oracle_pilot_cache_20260515.json
- experiments/core_narrative/results/rich_r_source_oracle_pilot_traceback_20260515.json
- experiments/core_narrative/results/rich_r_source_oracle_pilot_progress_20260515.json
- experiments/core_narrative/results/rich_r_source_oracle_pilot_py38_cache_20260515.json
- experiments/core_narrative/results/rich_r_source_oracle_pilot_unicode_load_20260515.json
- experiments/core_narrative/results/rich_r_source_oracle_pilot_unicode_invalid_20260515.json
- experiments/core_narrative/results/rich_r_source_oracle_pilot_cell_string_20260515.json
- experiments/core_narrative/results/rich_r_source_oracle_pilot_cell_table_20260515.json
- experiments/core_narrative/results/rich_r_source_oracle_pilot_split_text_20260515.json
- experiments/core_narrative/results/rich_r_source_oracle_pilot_pretty_console_20260515.json
- experiments/core_narrative/results/rich_r_source_oracle_pilot_progress_docstring_20260515.json
oracle templates:
- segment_split_lines_terminator
- cells_cached_len_unicode_version
- traceback_locals_depth_overflow_options
- progress_disabled_stop_no_blank_line
- unicode_data_py38_cache_fallback
- unicode_data_load_latest_table
- unicode_data_invalid_version_fallback
- cell_string_basic_api
- cell_table_metadata_api
- cell_string_split_text
- pretty_ipython_custom_console
- progress_reset_visible_docstring
no-op statuses: failed=12
reference statuses: passed=12
admission decisions: accepted=12
accepted R direct-smoke tasks: 8
accepted R source-only Golden-Oracle tasks: 12
accepted R tasks after pilots: 20
additional acceptances needed for 20 R primary: 0
additional acceptances needed for 20 R primary + 5 reserve: 5
remaining queued R oracle work items: 17
model calls: 0
```

Together with the R direct-smoke batch, these admit enough R tasks for the 20-primary target. They do not complete the 5-task R reserve target, freeze a full denominator, or authorize primary model attempts.

Rich R source-only Golden-Oracle reserve-completion batch:

```text
artifacts:
- experiments/core_narrative/results/rich_r_source_oracle_pilot_cells_simplify_20260515.json
- experiments/core_narrative/results/rich_r_source_oracle_pilot_cells_refine_20260515.json
- experiments/core_narrative/results/rich_r_source_oracle_pilot_unicode_comment_20260515.json
- experiments/core_narrative/results/rich_r_source_oracle_pilot_unicode_cell_table_20260515.json
- experiments/core_narrative/results/rich_r_source_oracle_pilot_table_doc_20260515.json
oracle templates:
- cells_variation_selector_branch_simplified
- cells_binary_search_entry_unpack
- unicode_data_fallback_comment_completed
- unicode_data_cell_table_type_import
- table_column_expand_doc_removed
no-op statuses: failed=5
reference statuses: passed=5
admission decisions: accepted=5
accepted R direct-smoke tasks: 8
accepted R source-only Golden-Oracle tasks: 17
accepted R tasks after reserve pilots: 25
additional acceptances needed for 20 R primary + 5 reserve: 0
remaining queued R oracle work items: 12
model calls: 0
```

Together with the R direct-smoke and primary source-only pilots, these five reserve pilots satisfy Rich R's 20-primary plus 5-reserve count. They do not freeze a full C/R/W* denominator or authorize primary model attempts.

Rich C extended task-admission readiness:

```text
artifact: experiments/core_narrative/results/rich_c_extended_task_admission_readiness_20260515.json
C scan: 2025-04-14..2025-11-13
design candidates: 20
direct smoke-ready candidates: 6
source-only requiring Golden-Oracle: 13
direct tests without extractable nodes: 1
families: 6
can form 20 C primary from design candidates: true
40-candidate pool gap: 20
model calls: 0
```

This extends C earlier only because calibration supply is thin, reaching the 20-task calibration design-candidate floor without borrowing from R or W*. It is readiness evidence only and does not freeze a C denominator.

Rich C direct-smoke batch:

```text
artifact: experiments/core_narrative/results/rich_c_direct_smoke_batch_20260515.json
scope: all 6 extended-C direct-oracle candidates
accepted: 3
rejected: 3
blocked: 0
no-op statuses: failed=3, passed_unexpected=3
reference statuses: passed=6
model calls: 0
```

Three C direct candidates passed no-op/reference admission smoke. The rejected direct candidates need replacement hidden verifiers before they can be admitted.

Rich C Golden-Oracle construction queue:

```text
artifact: experiments/core_narrative/results/rich_c_source_oracle_queue_20260515.json
accepted direct C tasks: 3
oracle work items: 17
composition: source-only=13, direct-tests-without-nodes=1, direct-smoke replacement=3
additional acceptances needed for 20 C primary: 17
additional acceptances needed for 20 C primary + 5 reserve: 22
maximum admitted design count if all queued oracles pass: 20
can reach 20 C primary if all queued oracles pass: true
can reach 20 C primary + 5 reserve under current design supply: false
40-candidate pool gap: 20
model calls: 0
```

This queue is redacted and machine-readable. Subsequent C Oracle pilots admitted all 17 queued verifier-construction items.

Rich C source-only Golden-Oracle admission batch:

```text
accepted C direct-smoke tasks: 3
accepted C source-only Golden-Oracle tasks: 13
accepted C tasks after source-only pilots: 16
additional acceptances needed for 20 C primary after source-only pilots: 4
no-op statuses: failed=13
reference statuses: passed=13
admission decisions: accepted=13
model calls: 0
```

The accepted C source-only templates were text docstring typo, logging type hint, console size lookup, main sponsor message, syntax docstring indent, three traceback source checks, three live-stack checks, spinner main group, and progress no-cover pragma.

Rich C replacement and direct-without-node admission batch:

```text
accepted C replacement-oracle tasks: 3
accepted C direct-without-node Oracle tasks: 1
accepted C tasks after all C pilots: 20
additional acceptances needed for 20 C primary: 0
additional acceptances needed for 20 C primary + 5 reserve: 5
no-op statuses: failed=4
reference statuses: passed=4
admission decisions: accepted=4
model calls: 0
```

Together with the direct-smoke batch, these pilots satisfy the Rich C 20-task calibration floor. They do not add a C reserve, solve the W* reserve/gate issue, or authorize primary model attempts.

## Rich ACUT Variants

Rich intervention readiness:

```text
A0 generic baseline: existing
A1 inert control: created
A2 static Rich context: created
A3 C-derived Rich playbook: created
A4 public-statement/source-only localization tool: created
A5 frontier generic reference: existing
model calls: 0
primary runs authorized: false
```

The A3 context pack uses admitted Rich C outcomes only as abstract calibration. It does not include raw commits, raw subjects, reference patch text, hidden verifier implementation, W* material, R scores, W* results, or ACUT outputs.

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

Explicit W* reserve-gate decision:

```text
artifact: experiments/core_narrative/results/rich_wstar_reserve_gate_decision_20260515.json
decision: w_star_primary_reached_but_reserve_and_pool_gates_failed
accepted W* primary candidates: 20
target primary + reserve count: 25
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
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments/core_narrative/tools/test_rich_acut_intervention_readiness.py experiments/core_narrative/tools/test_rich_wstar_reserve_gate_decision.py
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments/core_narrative/tools/test_repository_local_benchmark_final_blocked_report.py
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
python3 -m json.tool experiments/core_narrative/results/rich_r_direct_smoke_batch_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_queue_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_split_lines_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_cache_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_traceback_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_progress_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_py38_cache_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_unicode_load_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_unicode_invalid_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_cell_string_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_cell_table_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_split_text_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_pretty_console_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_progress_docstring_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_cells_simplify_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_cells_refine_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_unicode_comment_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_unicode_cell_table_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_r_source_oracle_pilot_table_doc_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_c_extended_task_admission_readiness_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_c_direct_smoke_batch_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_c_source_oracle_queue_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_c_source_oracle_pilot_text_typos_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_c_replacement_oracle_pilot_style_hash_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_c_direct_without_nodes_oracle_pilot_py38_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_acut_intervention_readiness_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_wstar_reserve_gate_decision_20260515.json
python3 -m json.tool experiments/core_narrative/results/repository_local_benchmark_final_blocked_report_20260515.json
python3 -m json.tool experiments/core_narrative/results/rich_replacement_oracle_pilot_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_replacement_oracle_pilot_zerospan_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_replacement_oracle_pilot_vs16_20260514.json
python3 -m json.tool experiments/core_narrative/results/rich_direct_without_nodes_oracle_pilot_20260514.json
python3 -m json.tool experiments/core_narrative/results/repository_local_benchmark_completion_audit_20260514.json
git diff --check
```

These commands verify the committed gate, queue, pilot, C-readiness, representative C-admission, Rich ACUT readiness, W* reserve-gate decision, and final blocked-report tools and manifests. They do not verify model runs or R/W* analysis because those phases are not applicable after the terminal W* supply gate failure.

## Next Work

No further work is authorized inside the frozen 0514 protocol. The stop-before-primary-runs path has been executed and recorded in `experiments/core_narrative/reports/2026-05-15_repository_local_benchmark_final_blocked_report.md`. Future work requires a new owner decision: preregister a protocol revision, find additional eligible W* candidates inside the frozen window without using ACUT outputs or W* results, or publish the blocked line as the terminal result.
