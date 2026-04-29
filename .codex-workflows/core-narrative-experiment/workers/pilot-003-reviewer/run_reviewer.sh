#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-pilot-003-reviewer

codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-pilot-003-reviewer \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/pilot-003-reviewer/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/pilot-003-reviewer/cli.log \
  2>&1
