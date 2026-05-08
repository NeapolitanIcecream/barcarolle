#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="${BARCAROLLE_REPO_ROOT:-$(cd "$script_dir/../../.." && pwd)}"
prompt_path="$script_dir/recheck-prompt-1.md"
log_path="$script_dir/cli-recheck-1.log"

cd "$repo_root"

codex exec \
  -C "$repo_root" \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --dangerously-bypass-approvals-and-sandbox \
  - < "$prompt_path" \
  > "$log_path" \
  2>&1
