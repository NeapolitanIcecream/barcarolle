#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-pilot-002-execution

exec codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-pilot-002-execution \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/pilot-002-execution/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/pilot-002-execution/cli.log \
  2>&1
