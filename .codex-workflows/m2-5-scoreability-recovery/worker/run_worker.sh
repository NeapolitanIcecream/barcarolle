#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle

codex exec \
  -C /Users/chenmohan/gits/barcarolle \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --dangerously-bypass-approvals-and-sandbox \
  - < /Users/chenmohan/gits/barcarolle/.codex-workflows/m2-5-scoreability-recovery/worker/prompt.md \
  > /Users/chenmohan/gits/barcarolle/.codex-workflows/m2-5-scoreability-recovery/worker/cli.log \
  2>&1
