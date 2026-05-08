#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle

codex exec \
  -C /Users/chenmohan/gits/barcarolle \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --dangerously-bypass-approvals-and-sandbox \
  - < .codex-workflows/barcarolle-nfl-output-contract-replay/reviewer/recheck-prompt-5.md \
  > .codex-workflows/barcarolle-nfl-output-contract-replay/reviewer/recheck-5-cli.log \
  2>&1
