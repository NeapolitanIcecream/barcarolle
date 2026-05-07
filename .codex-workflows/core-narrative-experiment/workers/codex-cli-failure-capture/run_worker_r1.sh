#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="${BARCAROLLE_REPO_ROOT:-$(cd -- "${script_dir}/../../../.." && pwd)}"

cd "${repo_root}"
codex exec \
  -C "${repo_root}" \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --dangerously-bypass-approvals-and-sandbox \
  - < "${script_dir}/revision-prompt-r1.md" \
  > "${script_dir}/cli-r1.log" \
  2>&1
