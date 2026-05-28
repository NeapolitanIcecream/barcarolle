# Three-Repo Paid Result Diagnostics Split Balance

Status: `complete`.

What happened: the paid subset is exactly balanced by repo and split, but some task-family and source-context strata differ inside repos.
Why it matters: imbalance can make per-repo gaps look larger even when the pooled design passes.
Action suggested next: use future preregistered blocked randomization if another paid run is bought.

- Measured factors: `task_family, task_time_bucket, source_context_class, source_context_quality, public_context_ref_count, implementation_file_count, test_file_count`.
- Unavailable factors: `statement_length_chars, context_length_chars, patch_size_proxy, changed_path_count_proxy, hidden_test_count_proxy`.
- Split imbalance status: `partially_supported`.
- Source-context thinness status: `partially_supported`.

## Repo Notes

- `attrs`: split counts `{'B_eval': 10, 'H_future': 10}`; largest categorical imbalance `task_family` with max count delta `2`.
- `boltons`: split counts `{'B_eval': 10, 'H_future': 10}`; largest categorical imbalance `task_family` with max count delta `2`.
- `click`: split counts `{'B_eval': 10, 'H_future': 10}`; largest categorical imbalance `task_family` with max count delta `1`.

## Click Title-Only Check

- Title-only tasks: `20/20`.
- Title-only split counts: `{'B_eval': 10, 'H_future': 10}`.
- Failed click cells with title-only context: `18/40`.

The completed split is not reinterpreted or changed by this audit.
