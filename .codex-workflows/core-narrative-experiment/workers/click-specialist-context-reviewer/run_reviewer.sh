#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-click-specialist-context-reviewer

exec codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-click-specialist-context-reviewer \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/click-specialist-context-reviewer/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/click-specialist-context-reviewer/cli.log \
  2>&1
