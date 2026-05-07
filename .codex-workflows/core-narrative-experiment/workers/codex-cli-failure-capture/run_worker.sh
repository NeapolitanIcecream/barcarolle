#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-codex-cli-failure-capture
codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-codex-cli-failure-capture \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --dangerously-bypass-approvals-and-sandbox \
  - < .codex-workflows/core-narrative-experiment/workers/codex-cli-failure-capture/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/codex-cli-failure-capture/cli.log \
  2>&1
