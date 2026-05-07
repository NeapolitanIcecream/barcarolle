#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-codex-cli-failure-capture-r1-reviewer
codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-codex-cli-failure-capture-r1-reviewer \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --dangerously-bypass-approvals-and-sandbox \
  - < .codex-workflows/core-narrative-experiment/workers/codex-cli-failure-capture-r1-reviewer/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/codex-cli-failure-capture-r1-reviewer/cli.log \
  2>&1
