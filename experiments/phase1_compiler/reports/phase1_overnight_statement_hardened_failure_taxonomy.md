# Statement-Hardened Failure Taxonomy

Failed cells: `11`. Failed tasks: `6`.

Taxonomy uses committed score tables, inventory statements, and sanitized score/verifier summaries only; raw transcript and hidden verifier material were not inspected.

## Failed Tasks

| Task | Repo split | Failed adapters | Categories | Both failed | Disagreement | Evidence | Inference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| attrs__hist__003 | attrs/B_eval | codex_workspace, kilo_workspace | api_semantics_complexity, source_context_weakness, statement_under_specification | True | False | Sparse PR context titled added first doc stub; both adapters failed a small generated-method introspection change. | The statement is scoreable, but the public context leaves the exact generated method target underdetermined. |
| attrs__hist__012 | attrs/H_future | codex_workspace, kilo_workspace | api_semantics_complexity, edge_case_specification, time_or_version_shift | True | False | Both adapters failed slots=True plus custom __setattr__ semantics in attrs/H_future. | This looks like future-window class-generation complexity rather than a harness or policy problem. |
| attrs__hist__013 | attrs/H_future | codex_workspace, kilo_workspace | api_semantics_complexity, edge_case_specification, time_or_version_shift | True | False | Both adapters failed next-generation frozen subclass/on_setattr behavior in attrs/H_future. | The task combines frozen semantics, subclassing, and next-generation API defaults. |
| boltons__hist__011 | boltons/B_eval | kilo_workspace | adapter_specific_behavior, api_semantics_complexity, edge_case_specification | False | True | Only Kilo failed the iterable strip helper task; Codex passed. | The disagreement suggests adapter-specific execution or solution behavior, not a release-wide scoring defect. |
| boltons__hist__022 | boltons/H_future | codex_workspace, kilo_workspace | api_semantics_complexity, edge_case_specification, time_or_version_shift | True | False | Both adapters failed chunk_ranges in boltons/H_future with overlap/windowing requirements. | The hard part is bounded range generation with invalid-argument and overlap semantics. |
| boltons__hist__027 | boltons/H_future | codex_workspace, kilo_workspace | api_semantics_complexity, edge_case_specification, time_or_version_shift | True | False | Both adapters failed cacheutils mapping view behavior in boltons/H_future. | The task requires preserving cache internals while presenting dict-like user values. |

## Category Counts

| Category | Count |
| --- | --- |
| adapter_specific_behavior | 1 |
| api_semantics_complexity | 11 |
| edge_case_specification | 9 |
| source_context_weakness | 2 |
| statement_under_specification | 2 |
| time_or_version_shift | 8 |

## Concentration

- Failed cells by repo/split: `{'attrs/B_eval': 2, 'attrs/H_future': 4, 'boltons/B_eval': 1, 'boltons/H_future': 4}`.
- Failed cells by module: `{'attr._make': 4, 'attr._next_gen': 2, 'boltons.cacheutils': 2, 'boltons.iterutils': 3}`.
- Adapter disagreement task IDs: `['boltons__hist__011']`.
