# Phase 1 Canonical Split Repair Process

Generated: `2026-05-25T07:28:37Z`.
Closeout updated: `2026-05-25T07:49:36Z`.

## Step Status

- Step 0 preflight: `completed`.
- Step 1 canonical split map: `completed`.
- Step 2 canonical selected inventory: `completed`.
- Step 3 missing-task Codex loop: `completed`.
- Step 4 deterministic QA and statement merge: `completed`.
- Step 5 canonical split screen: `completed`.
- Step 6 decision: `canonical_split_repair_complete_retry_preregistration`.
- Step 7 closeout: `completed`.

## Commits

```text
8e1831ff Record canonical split repair closeout
09b2cbb9 Decide canonical split repair branch
d0f537da Screen canonical split repaired statements
86fd6194 Run QA for canonical selected statements
ba77efdb Run canonical missing-task Codex statement loop
317fffb2 Build canonical selected task inventory
d3166d77 Build canonical Phase 1 split map
```

Closeout commit: `Record canonical split repair closeout`.

## Results

- Paid ACUT calls made: `false`.
- Codex Subscription statement sessions used: `true`.
- LLM API endpoint used for statement sessions: `false`.
- Raw artifacts committed: `false`.
- Historical pass/fail outcomes used for selection: `false`.
- Previous `boltons/H_future: 0` reclassification: `suspected_inventory_and_split_mapping_bug`.
- Canonical selected tasks: `16`.
- Missing canonical statement packets: `4`.
- Generated missing statements: `4`.
- Review counts: `{'pass': 4}`.
- Deterministic QA counts: `{'pass': 16}`.
- Canonical statements review/QA pass count: `16`.
- Selected counts by repo/split: `{'attrs/B_eval': 4, 'attrs/H_future': 4, 'boltons/B_eval': 4, 'boltons/H_future': 4}`.
- Primary decision: `canonical_split_repair_complete_retry_preregistration`.
- Next runbook path: `docs/experiments/phase-1-statement-hardened-preregistration-after-canonical-split-repair-runbook.md`.

## Guardrails

- Paid solver cells run: `false`.
- Existing scoreable cells rerun: `false`.
- Confirmed `attrs__hist__027` policy-violation cell rerun: `false`.
- Historical score tables rewritten: `false`.
- Predictive validity established: `false`.
- Paid validation completed: `false`.
- Generated statements are scoreable results: `false`.

## Verification

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_canonical_split_statement_repair.py`: `6 passed`.
- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_diff_assisted_codex_loop_statement_regeneration.py experiments/phase1_compiler/tests/test_phase1_statement_hardened_preregistration.py experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py experiments/phase0_headroom/tools/test_workspace_acut_run.py`: `58 passed`.
- `git diff --check`: `passed`.
