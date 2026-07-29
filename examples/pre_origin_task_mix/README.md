# Pre-Origin Task-Mix Kill Test

This source-specific research layer tests `THY-001R` without Agent outcomes or
paid calls. It compares a fixed one-year Git module-commit forecast with
cutoff-safe Task-history and Git-history controls on Multi-SWE-bench and
SWE-bench Full.

The study is explicitly counterfactual:

- Multi-SWE uses projected pull-request creation time.
- SWE-bench Full uses its pull-request `created_at` field and removes the 500
  exact SWE-bench Verified Task IDs from its primary robustness frame.
- Each Origin snapshot is the latest first-parent commit on the pinned current
  default-branch history whose committer time is no later than the cutoff.
- A Task's module label is scored retrospectively from its reference fix patch.
  That patch is never a forecast input.

This makes the experiment suitable for algorithm falsification and transfer
development. It does not turn patch-derived labels into native Task-arrival
evidence.

The fixed repositories are cloned as blobless bare repositories under an
ignored cache:

```bash
uv run python examples/pre_origin_task_mix/study.py prepare-repositories \
  --repository-cache outputs/research/2026-07-29-pre-origin-task-mix/repositories
```

Run the frozen study with DuckDB available for the local SWE-bench parquet:

```bash
uv run --with duckdb python examples/pre_origin_task_mix/study.py run \
  --repository-cache outputs/research/2026-07-29-pre-origin-task-mix/repositories \
  --output outputs/research/2026-07-29-pre-origin-task-mix/task-mix-results.json
```

`verify` reloads the plan and checks the raw artifact digest:

```bash
uv run python examples/pre_origin_task_mix/study.py verify \
  --result outputs/research/2026-07-29-pre-origin-task-mix/task-mix-results.json
```

The committed compact evidence is generated only after the frozen gate runs.
It omits per-Origin rows but binds their digest and the exact source, plan,
repository, and result identities.
