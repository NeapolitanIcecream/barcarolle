#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle

codex exec \
  -C /Users/chenmohan/gits/barcarolle \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --dangerously-bypass-approvals-and-sandbox \
  - < .codex-workflows/gh-codex-pr1-local-review/reviewer/recheck-prompt-1.md \
  > .codex-workflows/gh-codex-pr1-local-review/reviewer/cli-recheck-1.log \
  2>&1
