# Weighted Design Paid Pilot Baseline Comparison

Status: `complete`.

- Best pilot design(s) by max gap: `['repo_stratified_by_target_profile', 'repo_unweighted_same_budget']`.
- Historical reference rerun: `false`.
- Hidden oracle or raw transcript material used: `False`.

## Gap Summary

- `barcarolle_weighted_time_family_matched`: max gap `0.7481`, per repo `{'attrs': 0.3148, 'boltons': 0.7481}`.
- `repo_unweighted_same_budget`: max gap `0.25`, per repo `{'attrs': 0.25, 'boltons': 0.125}`.
- `repo_stratified_by_target_profile`: max gap `0.25`, per repo `{'attrs': 0.25, 'boltons': 0.125}`.

## Failure Buckets

- `repo_id`: `{'attrs': 8, 'boltons': 7}`.
- `task_family_label`: `{'attrs:validators': 4, 'boltons:funcutils': 2, 'attrs:_make': 2, 'attrs:converters': 2, 'boltons:ioutils': 2, 'boltons:iterutils': 2, 'boltons:fileutils:multi_file': 1}`.
- `source_kind`: `{'issue': 8, 'pull_request': 7}`.
- `adapter_id`: `{'kilo_workspace': 8, 'codex_workspace': 7}`.
