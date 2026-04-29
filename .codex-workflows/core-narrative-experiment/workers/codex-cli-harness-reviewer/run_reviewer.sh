#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-codex-cli-harness-reviewer

exec codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-codex-cli-harness-reviewer \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/codex-cli-harness-reviewer/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/codex-cli-harness-reviewer/cli.log \
  2>&1
