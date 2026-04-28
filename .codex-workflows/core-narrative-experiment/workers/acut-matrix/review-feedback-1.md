# Review Feedback 1

status: issues_found
review_source: /Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/reviews/wave0-review.md

## Required Closure

Address the Wave 0 review finding owned by `acut-matrix`:

The seven ACUT manifests do not satisfy the delivered ACUT schema. Normalize all seven manifests to the canonical ACUT manifest contract:

- top-level `provider`;
- top-level string `model`;
- `prompt_policy_digest`;
- `frozen_at` as date-time;
- string `operator`;
- keep richer structured details under clear optional fields such as `model_parameters`, `tool_permissions`, `retrieval_context_strategy`, `runtime_budget`, `network_policy`, `execution_mode`, `adapter_or_harness_basis`, and `metadata`;
- keep score fields null or in metadata; do not claim public benchmark scores.

Coordinate by contract, not by editing the schema worker's branch. You may inspect `/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/schemas/acut.schema.json`, but your deliverable is the manifest side of the alignment.

## Self-Check Expectations

- Parse every ACUT manifest as YAML.
- Check every manifest has the canonical top-level keys and expected scalar types.
- If a schema validation command is available in the schema-toolsmith worktree, run it against all seven manifests; otherwise record that the schema-side validator is pending.
- Run `git diff --check`.

Do not edit paths outside your owned ACUT manifest/report files and your worker process/revision files.
