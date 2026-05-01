#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-nonzero-exit-normalization-reviewer

codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-nonzero-exit-normalization-reviewer \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/nonzero-exit-normalization-reviewer/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/nonzero-exit-normalization-reviewer/cli.log \
  2>&1
