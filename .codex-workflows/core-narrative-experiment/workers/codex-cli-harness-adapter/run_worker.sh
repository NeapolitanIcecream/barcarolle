#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-codex-cli-harness-adapter

exec codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-codex-cli-harness-adapter \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/codex-cli-harness-adapter/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/codex-cli-harness-adapter/cli.log \
  2>&1
