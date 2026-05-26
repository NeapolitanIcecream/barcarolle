# Phase 1 Reference-Pass Replay Matrix

Plain-language summary: each sampled task was replayed with the current command and three command variants. Raw stdout and stderr were written only to ignored scratch paths; this report keeps hashes, command shapes, and short bounded error labels.

## Classification Counts

| classification | count |
| --- | ---: |
| dependency_or_python_version_failure | 12 |

## Sampled Tasks

| repo | task | classification | current error | variant result summary |
| --- | --- | --- | --- | --- |
| attrs | `attrs__supply_expansion_20260526__030` | dependency_or_python_version_failure | dependency_version_drift | A_current_barcarolle_command=1:dependency_version_drift, B_workspace_cwd_same_command=1:dependency_version_drift, C_no_editable_pythonpath=1:nonzero_unknown, D_pytest_config_visible=1:dependency_version_drift |
| attrs | `attrs__supply_expansion_20260526__037` | dependency_or_python_version_failure | pytest_collection_or_config_error | A_current_barcarolle_command=1:pytest_collection_or_config_error, B_workspace_cwd_same_command=1:pytest_collection_or_config_error, C_no_editable_pythonpath=1:pytest_collection_or_config_error, D_pytest_config_visible=1:pytest_collection_or_config_error |
| attrs | `attrs__supply_expansion_20260526__039` | dependency_or_python_version_failure | pytest_collection_or_config_error | A_current_barcarolle_command=1:pytest_collection_or_config_error, B_workspace_cwd_same_command=1:pytest_collection_or_config_error, C_no_editable_pythonpath=1:pytest_collection_or_config_error, D_pytest_config_visible=1:pytest_collection_or_config_error |
| attrs | `attrs__supply_expansion_20260526__042` | dependency_or_python_version_failure | pytest_collection_or_config_error | A_current_barcarolle_command=1:pytest_collection_or_config_error, B_workspace_cwd_same_command=1:pytest_collection_or_config_error, C_no_editable_pythonpath=1:pytest_collection_or_config_error, D_pytest_config_visible=1:pytest_collection_or_config_error |
| attrs | `attrs__supply_expansion_20260526__043` | dependency_or_python_version_failure | pytest_collection_or_config_error | A_current_barcarolle_command=1:pytest_collection_or_config_error, B_workspace_cwd_same_command=1:pytest_collection_or_config_error, C_no_editable_pythonpath=1:pytest_collection_or_config_error, D_pytest_config_visible=1:pytest_collection_or_config_error |
| attrs | `attrs__supply_expansion_20260526__044` | dependency_or_python_version_failure | pytest_collection_or_config_error | A_current_barcarolle_command=1:pytest_collection_or_config_error, B_workspace_cwd_same_command=1:pytest_collection_or_config_error, C_no_editable_pythonpath=1:pytest_collection_or_config_error, D_pytest_config_visible=1:pytest_collection_or_config_error |
| boltons | `boltons__supply_expansion_20260526__086` | dependency_or_python_version_failure | python_version_drift | A_current_barcarolle_command=2:python_version_drift, B_workspace_cwd_same_command=2:python_version_drift, C_no_editable_pythonpath=2:python_version_drift, D_pytest_config_visible=2:python_version_drift |
| boltons | `boltons__supply_expansion_20260526__090` | dependency_or_python_version_failure | python_version_drift | A_current_barcarolle_command=1:python_version_drift, B_workspace_cwd_same_command=1:python_version_drift, C_no_editable_pythonpath=1:python_version_drift, D_pytest_config_visible=1:python_version_drift |
| boltons | `boltons__supply_expansion_20260526__091` | dependency_or_python_version_failure | python_version_drift | A_current_barcarolle_command=1:python_version_drift, B_workspace_cwd_same_command=1:python_version_drift, C_no_editable_pythonpath=1:python_version_drift, D_pytest_config_visible=1:python_version_drift |
| boltons | `boltons__supply_expansion_20260526__096` | dependency_or_python_version_failure | python_version_drift | A_current_barcarolle_command=2:python_version_drift, B_workspace_cwd_same_command=2:python_version_drift, C_no_editable_pythonpath=2:python_version_drift, D_pytest_config_visible=2:python_version_drift |
| boltons | `boltons__supply_expansion_20260526__097` | dependency_or_python_version_failure | python_version_drift | A_current_barcarolle_command=2:python_version_drift, B_workspace_cwd_same_command=2:python_version_drift, C_no_editable_pythonpath=2:python_version_drift, D_pytest_config_visible=2:python_version_drift |
| boltons | `boltons__supply_expansion_20260526__098` | dependency_or_python_version_failure | python_version_drift | A_current_barcarolle_command=2:python_version_drift, B_workspace_cwd_same_command=2:python_version_drift, C_no_editable_pythonpath=2:python_version_drift, D_pytest_config_visible=2:python_version_drift |
