#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-model-route-reviewer

codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-model-route-reviewer \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/model-route-fix-reviewer/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/model-route-fix-reviewer/cli.log \
  2>&1
