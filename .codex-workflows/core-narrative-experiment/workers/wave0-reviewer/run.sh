#!/usr/bin/env bash
set -euo pipefail

COORDINATOR_REPO="${COORDINATOR_REPO:-/Users/chenmohan/gits/barcarolle}"
WORKER_REPO="${WORKER_REPO:-/Users/chenmohan/gits/barcarolle-wt-wave0-reviewer}"
WORKFLOW_ROOT=".codex-workflows/core-narrative-experiment"
PROMPT_PATH="$WORKER_REPO/$WORKFLOW_ROOT/workers/wave0-reviewer/prompt.md"
LOG_PATH="$WORKER_REPO/$WORKFLOW_ROOT/workers/wave0-reviewer/cli.log"

cd "$WORKER_REPO"
exec codex exec \
  -C "$WORKER_REPO" \
  -m gpt-5.5 \
  -c 'model_reasoning_effort="xhigh"' \
  --full-auto \
  - < "$PROMPT_PATH" > "$LOG_PATH" 2>&1
