#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-codex-cli-transport-hardening-reviewer

codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-codex-cli-transport-hardening-reviewer \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/codex-cli-transport-hardening-reviewer/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/codex-cli-transport-hardening-reviewer/cli.log \
  2>&1
