# G-score Gold-Patch Smoke

Status: `gold_patch_smoke_passed`
Generated at: `2026-05-13T06:32:37.428702Z`
Config: `/Users/chenmohan/gits/barcarolle/experiments/core_narrative/configs/general_benchmark.yaml`

## Scope

This is a no-model smoke for the pinned six-task SWE-Bench Pro general benchmark basis. It checks the locked denominator, pinned dataset/evaluator metadata, selection keys, gold-patch input path, evaluator artifact layout, Docker/backend readiness, and score parser expectations.

It is not ACUT scoring. ACUT patch-generation attempted: `False`. ACUT G_score available: `False`. Public leaderboard proxy used: `False`.

## Outcome

- Gold-patch execution requested: `True`
- Gold-patch path ran: `True`
- Gold-patch basis proven: `True`
- Dataset cache status: `passed` at `/Users/chenmohan/gits/barcarolle/experiments/core_narrative/cache/swebench_pro/test-00000-of-00001.parquet`
- Evaluator checkout status: `passed` at `/Users/chenmohan/gits/barcarolle/experiments/core_narrative/external_repos/SWE-bench_Pro-os`
- Docker status: `passed`
- Artifact layout status: `passed` under `/Users/chenmohan/gits/barcarolle/experiments/core_narrative/large_artifacts/m5_w2_g6_gold_patch_smoke_20260513_executed_abs_python`

## Blockers

- None.

## Score Parser

- Score parser status: `parsed`
- Proof eligible: `True`
- Resolved count: `6` / `6`
- Missing expected instances: `[]`
- Unexpected instances: `[]`

The parser keeps the denominator fixed at six pinned tasks. Missing expected task ids, unexpected task ids, or non-boolean resolved statuses invalidate the score artifact instead of shrinking the denominator.

## Claim Boundary

No G_score is claimed by this report. A passing gold-patch smoke would prove only that the pinned evaluator basis can score known-good patches; it would still not be an ACUT result. If this report is blocked, G_score remains unavailable, not zero and not replaced by a public leaderboard score.

## Reproduction

```bash
python3 experiments/core_narrative/tools/codex_nfl_gscore_gold_patch_smoke.py \
  --output experiments/core_narrative/results/gscore_gold_patch_smoke_20260509.json \
  --report experiments/core_narrative/reports/gscore_gold_patch_smoke_20260509.md
```

After the pinned dataset cache and evaluator checkout are present, run the evaluator path deliberately:

```bash
python3 experiments/core_narrative/tools/codex_nfl_gscore_gold_patch_smoke.py \
  --execute-gold-patch \
  --output experiments/core_narrative/results/gscore_gold_patch_smoke_20260509.json \
  --report experiments/core_narrative/reports/gscore_gold_patch_smoke_20260509.md
```
