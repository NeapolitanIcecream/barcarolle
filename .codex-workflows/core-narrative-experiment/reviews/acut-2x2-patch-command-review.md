# ACUT 2x2 And Patch Command Review

status: issues_found
reviewed_redesign_commit: 9409244
reviewed_patch_command_commit: db68a50
updated: 2026-04-29T11:33:04+08:00

## Summary

The 2x2 ACUT redesign at `9409244` is internally consistent. The active ACUTs are exactly `frontier-generic-swe`, `frontier-click-specialist`, `cheap-generic-swe`, and `cheap-click-specialist`; the three deferred ACUTs remain deferred; the previous active ACUTs are retired for new execution; the default pilot is 28 primary attempts; and the full 80-attempt core remains gated on pilot review plus explicit coordinator promotion. The four active ACUT manifests share harness basis, task budget, turn cap, test cap, retry policy, network policy, and one-primary-attempt policy. Same-tier generic-vs-Click pairs keep the same provider/model/model parameters and differ only in policy/context specialization.

The patch command implementation in `db68a50` adds a custom `barcarolle_patch_command.py` path intended to run behind `acut_patch_adapter.py`. The code uses only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL` for live LLM access, rejects unsafe command arguments, records prompt hashes rather than prompt content, and has no scoped `codex exec` patch-generation command reference.

One compatibility issue remains: the patch-command handoff and no-model smoke artifacts still use retired pre-redesign ACUT IDs, so the delivered patch-command contract is not yet ready to be promoted with the new 2x2 active ACUT IDs.

## Findings

1. High - Patch-command delivery still targets retired ACUT IDs instead of the 2x2 active IDs. The live review template passes `--acut .../configs/acuts/lower-budget-fast-path.yaml` to both `acut_patch_adapter.py` and `barcarolle_patch_command.py` (`/Users/chenmohan/gits/barcarolle-wt-patch-command-contract/experiments/core_narrative/reports/patch_command_contract.md:36`, `/Users/chenmohan/gits/barcarolle-wt-patch-command-contract/experiments/core_narrative/reports/patch_command_contract.md:47`; duplicated in `/Users/chenmohan/gits/barcarolle-wt-patch-command-contract/.codex-workflows/core-narrative-experiment/workers/patch-command-contract/process.md:79` and `/Users/chenmohan/gits/barcarolle-wt-patch-command-contract/.codex-workflows/core-narrative-experiment/workers/patch-command-contract/process.md:90`). The committed no-model adapter evidence also records `acut_id: lower-budget-fast-path`, and adapter payloads still list the old core ACUTs as the execution profile. Under the redesign, `lower-budget-fast-path`, `general-benchmark-optimized`, `repo-context-heavy`, and `retrieval-sparse-symbolic` are retired for new execution. This leaves the command contract evidence and handoff incompatible with the required 2x2 active set, even though the command path itself appears custom and BARCAROLLE-env-only.

## Required Closure

Refresh the patch-command delivery against the 2x2 redesign before execution-start promotion:

- Replace executable command templates and handoff text with one of the active 2x2 ACUT manifests: `frontier-generic-swe`, `frontier-click-specialist`, `cheap-generic-swe`, or `cheap-click-specialist`.
- Rerun the no-model adapter dry-run/mock probe behind the post-redesign `acut_patch_adapter.py`/`_llm_budget.py` so the structured evidence records active 2x2 ACUT IDs and the 28-attempt pilot profile.
- Keep retired ACUT IDs only as historical redesign notes, not as executable templates, current smoke evidence, default core IDs, or new-execution ACUT references.

## Checks Run

- `PYTHONPYCACHEPREFIX=/tmp/acut-2x2-patch-reviewer-pycache python3 experiments/core_narrative/tools/validate_acut_manifest.py experiments/core_narrative/configs/acuts --output /tmp/acut-2x2-patch-reviewer-validation.json` in the coordinator repo: passed; 7 manifests valid, 0 invalid.
- Structured YAML invariant check against `9409244`: passed for active/deferred/retired ACUT sets, 28-attempt pilot, budget-tight fallback, full-core promotion gate, shared active runtime controls, same-tier model equality, Click-specialist allowed sources, and leakage forbids.
- `git diff --check 9409244^ 9409244 -- . ':(exclude)**/cli.log'`: passed.
- `PYTHONPYCACHEPREFIX=/tmp/acut-2x2-patch-reviewer-pycache python3 -m py_compile experiments/core_narrative/tools/barcarolle_patch_command.py experiments/core_narrative/tools/acut_patch_adapter.py` in the patch-command worktree: passed.
- Structured JSON/JSONL parse over patch-command result, adapter result, normalized result, and ledger artifacts: passed for 10 files.
- Static scan over patch-command report/results for credential values, bearer values, provider-token patterns, and full URLs: passed.
- Scoped `rg` over patch-command delivery for retired/new ACUT IDs: found retired executable/evidence references listed in the finding.
- Scoped `rg` over patch-command delivery for `codex exec`: no matches.
- `git diff --check db68a50^ db68a50 -- . ':(exclude)**/cli.log'`: passed.
