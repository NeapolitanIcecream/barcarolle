#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-task-manifests-reviewer

codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-task-manifests-reviewer \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/task-manifests-reviewer/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/task-manifests-reviewer/cli.log \
  2>&1

