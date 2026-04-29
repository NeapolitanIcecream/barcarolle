#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-acut-adapter-smoke-reviewer

codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-acut-adapter-smoke-reviewer \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/acut-adapter-smoke-reviewer/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/acut-adapter-smoke-reviewer/cli.log \
  2>&1
