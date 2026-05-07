#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-general-lock

codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-general-lock \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/general-benchmark-lock/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/general-benchmark-lock/cli.log \
  2>&1
