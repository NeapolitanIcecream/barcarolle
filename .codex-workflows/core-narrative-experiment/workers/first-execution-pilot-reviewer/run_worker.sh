#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-first-execution-pilot-reviewer

exec codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-first-execution-pilot-reviewer \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/first-execution-pilot-reviewer/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/first-execution-pilot-reviewer/cli.log \
  2>&1
