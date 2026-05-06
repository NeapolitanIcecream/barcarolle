#!/usr/bin/env bash
set -euo pipefail
cd /Users/chenmohan/gits/barcarolle-wt-option-c-no-model-reviewer
codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-option-c-no-model-reviewer \
  -m gpt-5.5 \
  -c model_reasoning_effort="xhigh" \
  --dangerously-bypass-approvals-and-sandbox \
  - < .codex-workflows/core-narrative-experiment/workers/option-c-no-model-reviewer/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/option-c-no-model-reviewer/cli.log \
  2>&1
