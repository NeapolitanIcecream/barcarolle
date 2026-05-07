#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-empty-patch-gate-reviewer

codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-empty-patch-gate-reviewer \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/empty-patch-gate-reviewer/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/empty-patch-gate-reviewer/cli.log \
  2>&1
