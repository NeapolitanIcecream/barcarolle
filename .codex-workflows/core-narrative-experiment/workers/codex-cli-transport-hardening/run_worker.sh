#!/usr/bin/env bash
set -euo pipefail

cd /Users/chenmohan/gits/barcarolle-wt-codex-cli-transport-hardening

codex exec \
  -C /Users/chenmohan/gits/barcarolle-wt-codex-cli-transport-hardening \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --full-auto \
  - < .codex-workflows/core-narrative-experiment/workers/codex-cli-transport-hardening/prompt.md \
  > .codex-workflows/core-narrative-experiment/workers/codex-cli-transport-hardening/cli.log \
  2>&1
