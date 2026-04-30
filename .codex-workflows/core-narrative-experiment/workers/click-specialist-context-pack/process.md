# Process

status: delivered
updated: 2026-04-30T09:21:32+08:00

## Summary

Focused worker is starting to generate, wire, and smoke-check a task-agnostic
Click specialist context pack before any specialist ACUT execution. The goal is
to strengthen the 2x2 specialist treatment without changing model tier,
runtime budget, retry policy, task slice, or broad execution authorization.

No ACUT attempt, retry, second attempt, specialist ACUT run, broad execution, or
large model-call batch is authorized.

## Owned Paths

- `experiments/core_narrative/context_packs/click_specialist/**`
- `experiments/core_narrative/tools/**` only for context-pack generation,
  loading, and prompt-injection support
- `experiments/core_narrative/configs/acuts/frontier-click-specialist.yaml`
- `experiments/core_narrative/configs/acuts/cheap-click-specialist.yaml`
- `experiments/core_narrative/configs/core_subset_run_manifest.yaml` only for
  context-pack status/metadata
- `experiments/core_narrative/reports/click_specialist_context_pack.md`
- `experiments/core_narrative/results/normalized/click_specialist_context_pack*.json`
- `experiments/core_narrative/results/raw/click_specialist_context_pack*/**`
- `experiments/core_narrative/results/cost_ledger.jsonl` only if a live
  BARCAROLLE model-call smoke is performed and ledgered
- `.codex-workflows/core-narrative-experiment/workers/click-specialist-context-pack/**`

## Branch / Worktree

- Branch: `codex/core-exp-click-specialist-context-pack`
- Worktree: `/Users/chenmohan/gits/barcarolle-wt-click-specialist-context-pack`

## Current Blockers

None.

## Activity Log

- 2026-04-30T09:00:48+08:00: Worker scaffold created by coordinator. Start by
  reading the coordinator, active specialist ACUT manifests, reviewed Codex CLI
  harness adapter process/review summaries, and current context-pack-related
  run-manifest entries. Do not inspect any `cli.log` file.
- 2026-04-30T09:01:29+08:00: Implementation worker started. Read required
  tests-as-specs and observability guidance; next step is manifest and prompt
  construction inspection. No ACUT execution or live BARCAROLLE model call will
  be started.
- 2026-04-30T09:15:44+08:00: Generated deterministic Click specialist
  context pack from locked Click commit `8bd8b4a074c55c03b6eb5666edc44a9c43df38a2`
  after fixing the source allowlist to include direct source/docs/test files.
  Wired pack metadata into the two Click-specialist ACUT manifests only and ran
  the no-model four-ACUT injection smoke through `codex_cli_patch_command.py
  --dry-run`; both specialist prompts include marker/hash/section IDs and both
  generic prompts exclude them. No ACUT adapter run, ledger append, live model
  call, retry, second attempt, specialist live run, broad execution, or batch
  was started.
- 2026-04-30T09:21:32+08:00: Final checks passed. Context pack hash is
  `dfb271ad174531a7dd2f00da4cd0486193d87ce33349380982150889ecf84e48`.
  Delivery is ready for focused review before any specialist ACUT execution.

## Changed Files

- `.codex-workflows/core-narrative-experiment/workers/click-specialist-context-pack/process.md`
- `experiments/core_narrative/configs/acuts/frontier-click-specialist.yaml`
- `experiments/core_narrative/configs/acuts/cheap-click-specialist.yaml`
- `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- `experiments/core_narrative/context_packs/click_specialist/context_prompt.md`
- `experiments/core_narrative/context_packs/click_specialist/convention_playbook.json`
- `experiments/core_narrative/context_packs/click_specialist/docs_map.json`
- `experiments/core_narrative/context_packs/click_specialist/manifest.json`
- `experiments/core_narrative/context_packs/click_specialist/repo_map.json`
- `experiments/core_narrative/context_packs/click_specialist/retrieval_policy.json`
- `experiments/core_narrative/context_packs/click_specialist/symbol_index.json`
- `experiments/core_narrative/reports/click_specialist_context_pack.md`
- `experiments/core_narrative/results/normalized/click_specialist_context_pack_smoke.json`
- `experiments/core_narrative/results/raw/click_specialist_context_pack_smoke/**`
- `experiments/core_narrative/tools/build_click_specialist_context_pack.py`
- `experiments/core_narrative/tools/click_specialist_context.py`
- `experiments/core_narrative/tools/codex_cli_patch_command.py`
- `experiments/core_narrative/tools/smoke_click_specialist_context_pack.py`

## Inspected Files

- `.codex-workflows/core-narrative-experiment/coordinator.md`
- `experiments/core_narrative/configs/acuts/frontier-generic-swe.yaml`
- `experiments/core_narrative/configs/acuts/frontier-click-specialist.yaml`
- `experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml`
- `experiments/core_narrative/configs/acuts/cheap-click-specialist.yaml`
- `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- `experiments/core_narrative/configs/target_repositories.yaml`
- `experiments/core_narrative/tools/codex_cli_patch_command.py`
- `experiments/core_narrative/tools/barcarolle_patch_command.py`
- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/tools/_common.py`
- `experiments/core_narrative/tools/validate_acut_manifest.py`
- locked Click checkout at `experiments/core_narrative/external_repos/click`
  commit `8bd8b4a074c55c03b6eb5666edc44a9c43df38a2`

## Checks Run

- `PYTHONPYCACHEPREFIX=/tmp/barcarolle-pycache python3 -m py_compile experiments/core_narrative/tools/build_click_specialist_context_pack.py experiments/core_narrative/tools/click_specialist_context.py experiments/core_narrative/tools/smoke_click_specialist_context_pack.py experiments/core_narrative/tools/codex_cli_patch_command.py`
- `python3 experiments/core_narrative/tools/validate_acut_manifest.py experiments/core_narrative/configs/acuts/frontier-click-specialist.yaml experiments/core_narrative/configs/acuts/cheap-click-specialist.yaml experiments/core_narrative/configs/acuts/frontier-generic-swe.yaml experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml`
- YAML parse check for `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
  and all four active ACUT manifests using `_common.load_manifest`
- JSON parse check for `experiments/core_narrative/context_packs/click_specialist/*.json`,
  `experiments/core_narrative/results/raw/click_specialist_context_pack_smoke/**/*.json`,
  and `experiments/core_narrative/results/normalized/click_specialist_context_pack_smoke.json`
- Reproducibility check: reran
  `python3 experiments/core_narrative/tools/build_click_specialist_context_pack.py --click-root experiments/core_narrative/external_repos/click --output-dir experiments/core_narrative/context_packs/click_specialist --generated-at 2026-04-30T09:25:00+08:00`
  and diffed before/after artifact hashes; no changes.
- No-model injection smoke:
  `PYTHONPYCACHEPREFIX=/tmp/barcarolle-pycache python3 experiments/core_narrative/tools/smoke_click_specialist_context_pack.py --repo-root . --raw-dir experiments/core_narrative/results/raw/click_specialist_context_pack_smoke --normalized-output experiments/core_narrative/results/normalized/click_specialist_context_pack_smoke.json`
- Scoped no-secret/leakage scan over process file, context pack, report, raw smoke
  artifacts, and normalized smoke artifact for full URLs, endpoint values,
  credential assignments, bearer tokens, IP addresses, hidden verifier paths,
  and pilot output paths.
- Generic-negative evidence scan: no pack marker/hash/section marker in
  `frontier-generic-swe` or `cheap-generic-swe` raw dry-run artifacts.
- `rg -n '"(content_recorded|endpoint_value_recorded|credential_value_recorded|model_call_made|executed)": true' experiments/core_narrative/results/raw/click_specialist_context_pack_smoke experiments/core_narrative/results/normalized/click_specialist_context_pack_smoke.json || true`
- `git diff --check`

## Live Call And Ledger

- live BARCAROLLE model call occurred: false
- main experiment cost ledger appended: false
- ledger event appended: none

## Handoff

Focused reviewer handoff:

- Review `experiments/core_narrative/reports/click_specialist_context_pack.md`.
- Review generated manifest
  `experiments/core_narrative/context_packs/click_specialist/manifest.json`
  and no-model smoke
  `experiments/core_narrative/results/normalized/click_specialist_context_pack_smoke.json`.
- The specialist ACUT dry-run summaries include marker, pack id/hash, and all
  five section IDs. The generic ACUT dry-run artifacts contain none of the pack
  marker, pack hash, or section markers.
- No live BARCAROLLE call occurred; no cost ledger event was appended.
- Keep specialist ACUT execution blocked until this delivery is reviewed.
