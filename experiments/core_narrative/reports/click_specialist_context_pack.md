# Click Specialist Context Pack

status: review-ready

## Summary

Generated and wired a task-agnostic Click specialist context pack for the two
Click-specialist ACUTs only:

- `frontier-click-specialist`
- `cheap-click-specialist`

The two generic ACUTs remain free of the pack:

- `frontier-generic-swe`
- `cheap-generic-swe`

No ACUT attempt, retry, second attempt, specialist live run, broad execution,
large batch, live BARCAROLLE model call, or cost-ledger append occurred.

## Pack

- pack id: `click_specialist_context_pack_v1`
- marker: `CLICK_SPECIALIST_CONTEXT_PACK_V1`
- pack hash: `dfb271ad174531a7dd2f00da4cd0486193d87ce33349380982150889ecf84e48`
- locked Click commit: `8bd8b4a074c55c03b6eb5666edc44a9c43df38a2`
- manifest: `experiments/core_narrative/context_packs/click_specialist/manifest.json`
- prompt artifact: `experiments/core_narrative/context_packs/click_specialist/context_prompt.md`

Generated artifacts:

- `repo_map.json`: `f3d9d32bb44801e3dc17326ab448ff8aa14e209c4e9d639ca9c68a3f7026cd93`
- `docs_map.json`: `5c38819cae84353b3cb0ce4f6187d6b15f0b9e6af6985f86c5cc6b844d874f19`
- `symbol_index.json`: `aef8fed0090d6da5a8e450ffe33c9aecc50c8e8730fa00f709c0ce4e876f25a0`
- `convention_playbook.json`: `44f2feceb44def94c047ef229bd306f2b53f85a3b28b2bc0efb08e7e415ca805`
- `retrieval_policy.json`: `0e42f25fc6a70f8123991448214d4d910fb2da93c048b8b4f6a678ce61d98cb8`
- `context_prompt.md`: `7d80f3254695a99ddc2f2f9b8b9a7d97b6fcf5f46922c204e3a9333facde728d`

Generator command recorded in the manifest:

```bash
python3 experiments/core_narrative/tools/build_click_specialist_context_pack.py --click-root experiments/core_narrative/external_repos/click --output-dir experiments/core_narrative/context_packs/click_specialist --generated-at 2026-04-30T09:25:00+08:00
```

## Wiring

`experiments/core_narrative/tools/codex_cli_patch_command.py` now loads the
pack only when `metadata.specialist_context.context_pack` is present and
`click_task_agnostic_context_allowed` is true. Dry-run summaries include
machine-readable context evidence: marker presence, pack id/hash, section IDs,
char counts, hashes, and no-content-recorded booleans.

The specialist ACUT manifests declare the pack path and hash. The generic ACUT
manifests do not declare the pack and the dry-run prompt checks confirm the
pack marker is absent.

## No-Model Smoke

Smoke artifact:
`experiments/core_narrative/results/normalized/click_specialist_context_pack_smoke.json`

Result: passed.

| ACUT | Expected | Marker | Pack hash | Sections | Prompt chars |
| --- | --- | --- | --- | --- | --- |
| `frontier-generic-swe` | absent | false | false | none | 2997 |
| `frontier-click-specialist` | present | true | true | 5/5 | 8500 |
| `cheap-generic-swe` | absent | false | false | none | 2996 |
| `cheap-click-specialist` | present | true | true | 5/5 | 8499 |

The smoke used `codex_cli_patch_command.py --dry-run`; `codex_exec.executed`
is false for all four cells, `model_call_made` is false, and the adapter was
not invoked.

## Checks

- Python syntax: passed for changed Python tools.
- ACUT validator: passed for all four active ACUT manifests.
- YAML parse: passed for updated ACUT manifests and run manifest.
- JSON parse: passed for generated pack and smoke artifacts.
- Reproducibility: rerunning the generator with the recorded command produced
  identical context-pack file hashes.
- No-model injection smoke: passed for all four active ACUTs.
- Leakage/no-secret scan: passed for context pack and smoke artifacts; no full
  URLs, endpoint values, credential values, bearer tokens, hostnames, IP
  addresses, hidden verifier paths, or pilot output paths were recorded.

## Handoff

This branch is ready for focused review. Specialist ACUT execution should stay
blocked until the reviewer accepts the context pack and prompt-injection
evidence.
