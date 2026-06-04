# Phase 0 Preflight

- Branch: `codex/restart-benchmark-compiler`
- HEAD: `6a2d3a7893e69bde700aaad4e7e867c1947de459`
- Generated UTC: `2026-05-20T07:39:13+00:00`
- Shell: `/bin/zsh`
- Python: `3.11.13` at `/Users/chenmohan/gits/barcarolle/experiments/phase0_headroom/.venv/bin/python3`
- Phase 0 Python command: `/opt/homebrew/bin/uv run --project experiments/phase0_headroom python`
- Disk:

```text
Filesystem      Size    Used   Avail Capacity iused ifree %iused  Mounted on
/dev/disk3s5   926Gi   552Gi   347Gi    62%     13M  3.6G    0%   /System/Volumes/Data
```

## Ignore Checks

- `workspaces`: pass
- `external_repos`: pass
- `cache`: pass
- `large_artifacts`: pass
- `raw_results`: pass

## Archive Reuse Inventory

- Archived core-narrative files seen at max depth 3: `6298`
- Active `experiments/core_narrative` tracked files: `0`
- Reuse policy: reference archived Click manifests, release metadata, verifier discipline, and score taxonomy; do not copy raw outputs.

## Budget

- Ledger path: `experiments/phase0_headroom/results/cost_ledger.jsonl`
- Cumulative estimated LLM API spend: `$0.00`
- Paid model calls during this run: `0`

Acceptance: process log exists, budget ledger exists, no paid model call has been made, ignored raw paths are configured, and active `experiments/core_narrative` remains absent from tracked files.
