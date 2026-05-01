#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-nonzero-exit-normalization

codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-nonzero-exit-normalization \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/nonzero-exit-normalization/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/nonzero-exit-normalization/cli.log \
  2>&1
