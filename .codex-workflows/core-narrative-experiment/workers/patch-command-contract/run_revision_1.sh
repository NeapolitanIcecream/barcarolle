#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-patch-command-contract

exec codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-patch-command-contract \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/patch-command-contract/revision-prompt-1.md \
  > .codex-workflows/core-narrative-experiment/workers/patch-command-contract/cli-revision-1.log \
  2>&1
