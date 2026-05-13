# M5-W2 Repository-Specific Advantage Stress Test

## Objective

Test whether stronger Click-specific task-agnostic context improves held-out Click work performance. This phase is W-only unless the W2 gate passes.

M5-W2 does not try to salvage `RGW-full-workspace-v1`. It treats v1 as a negative / neutral baseline and starts a new primary denominator.

## Primary ACUTs

| ACUT | Role |
|---|---|
| `cheap-generic-swe` | Cheap generic baseline |
| `cheap-click-specialist` | Existing Click specialist baseline |
| `cheap-click-deep-specialist-v2` | New stronger Click context treatment |
| `frontier-generic-swe` | High-capability generic contrast |

`frontier-click-specialist` is not primary for W2. It may be added later as a secondary analysis only after the primary W2 gate is understood.

## Task Denominator

Use `RWork-v2`: 10 new held-out Click work tasks, plus 4 preregistered reserves. The old six RWork tasks are not part of the M5-W2 denominator.

Family quotas:

| Family | Primary tasks |
|---|---:|
| option/default/envvar/flag_value semantics | 3 |
| CliRunner/testing/input-output isolation | 2 |
| prompt/termui/output rendering | 2 |
| type conversion / parameter normalization | 2 |
| mixed integration | 1 |

Each admitted task must satisfy:

- reference patch passes;
- no-op fails;
- anchor is disjoint from existing RBench/RWork anchors;
- statement gives enough behavior or minimal reproduction to solve without showing the final implementation;
- verifier checks behavior rather than incidental reference implementation details;
- source-derived URL-only material does not trigger primary USV under the repaired policy.

## Execution

Run one primary attempt per ACUT/task cell:

```text
4 ACUTs x 10 RWork-v2 tasks = 40 primary attempts
```

No best-of-N, retries, or post-hoc denominator mixing. Use deterministic shuffled order and record the exact order in the results bundle.

Primary score:

```text
W2_verified_score = verified_pass / 10
```

Secondary metrics:

- paired wins vs `cheap-generic-swe`;
- paired wins vs `frontier-generic-swe`;
- `no_diff_count`;
- `true_unsafe_count`;
- `policy_hold_count`;
- blind review score, recorded as interpretation only and never replacing verifier score.

## Gates

Context-effect gate:

```text
cheap-click-deep-specialist-v2 W2_score >= cheap-generic-swe W2_score + 2 tasks
```

NFL-candidate gate:

```text
cheap-click-deep-specialist-v2 W2_score > frontier-generic-swe W2_score
```

If the context-effect gate fails, stop and report that stronger Click context did not produce W separation.

If W2 passes, then design R2. ACUT G remains no-model readiness only until W2 and R2 produce a credible pairwise reversal candidate.

## Policy Repair

M5-W2 uses `source-derived-url-only-v1`:

- model-generated URL/secret/credential -> `unsafe_or_scope_violation`;
- ambiguous unsafe content -> `unsafe_or_scope_violation`;
- source-derived URL-only diff context or removed lines -> public redacted preview plus private verifier replay patch;
- raw URL-bearing replay patch stays in ignored local workspace artifacts, not public result artifacts.
