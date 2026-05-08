#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle

codex exec \
  -C /Users/chenmohan/gits/barcarolle \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --dangerously-bypass-approvals-and-sandbox \
  - < /Users/chenmohan/gits/barcarolle/.codex-workflows/barcarolle-nfl-output-contract-replay/reviewer/recheck-prompt-2.md \
  > /Users/chenmohan/gits/barcarolle/.codex-workflows/barcarolle-nfl-output-contract-replay/reviewer/cli-recheck-2.log \
  2>&1
