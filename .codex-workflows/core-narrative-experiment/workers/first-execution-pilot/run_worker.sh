#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-first-execution-pilot

exec codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-first-execution-pilot \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/first-execution-pilot/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/first-execution-pilot/cli.log \
  2>&1
