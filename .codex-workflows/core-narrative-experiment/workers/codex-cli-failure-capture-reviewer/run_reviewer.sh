#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-codex-cli-failure-capture-reviewer
codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-codex-cli-failure-capture-reviewer \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --dangerously-bypass-approvals-and-sandbox \
  - < .codex-workflows/core-narrative-experiment/workers/codex-cli-failure-capture-reviewer/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/codex-cli-failure-capture-reviewer/cli.log \
  2>&1
