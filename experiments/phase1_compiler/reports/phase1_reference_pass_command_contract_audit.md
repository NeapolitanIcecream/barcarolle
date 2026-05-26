# Phase 1 Reference-Pass Command Contract Audit

Plain-language summary: the current replay code archives the target commit, installs that workspace editably, sets `PYTHONPATH` to that workspace, and runs the changed tests. The main weakness is classification: setup, import, collection, and assertion failures are all stored as `reference_pass` failures.

## Findings

- reference replay uses the target workspace and editable install (local_validation_bug_not_found)
- reference replay records every nonzero target command as reference_pass failure without separating install or collection failures (historical_environment_model_gap)
- command_template contains a repo-root-relative --project path, so cwd variants must absolutize --project before they are meaningful (command_contract_cwd_coupling)

## Command Shape

| repo | cwd | test paths | editable | classification gap |
| --- | --- | --- | --- | --- |
| attrs | repo_root | absolute_workspace_paths | uv_run_gets_with_editable_workspace | install, collection, import, and assertion failures are all nonzero command results under reference_pass |
| boltons | repo_root | absolute_workspace_paths | uv_run_gets_with_editable_workspace | install, collection, import, and assertion failures are all nonzero command results under reference_pass |
