#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-repo-runtime-lock

codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-repo-runtime-lock \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/repo-runtime-lock/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/repo-runtime-lock/cli.log \
  2>&1
