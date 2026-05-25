#!/usr/bin/env bash
set -euo pipefail
cd /Users/chenmohan/gits/barcarolle

WORKFLOW=".codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop"
PROCESS=".codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/generator/process.md"
LOG=".codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/generator/cli.log"

timestamp() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

mkdir -p "$WORKFLOW/generator/output"
cat > "$PROCESS" <<EOF
status: working
updated: $(timestamp)
summary: External Codex CLI generator wrapper started using local Codex Subscription auth with API endpoint environment variables unset.
session: phase1-diffstmt-generator
llm_api_endpoint_used: false
EOF

set +e
env -u LLM_BASE_URL -u LLM_API_KEY -u OPENAI_API_KEY -u OPENROUTER_API_KEY \
codex exec \
  -C /Users/chenmohan/gits/barcarolle \
  -m gpt-5.5 \
  -c 'model_reasoning_effort="xhigh"' \
  --dangerously-bypass-approvals-and-sandbox \
  - < ".codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/generator/prompt.md" \
  > "$LOG" \
  2>&1
rc=$?
set -e

if [ "$rc" -ne 0 ]; then
  cat > "$PROCESS" <<EOF
status: blocked
updated: $(timestamp)
summary: External Codex CLI generator exited non-zero. Raw log is intentionally ignored and not committed.
session: phase1-diffstmt-generator
exit_code: $rc
EOF
  exit "$rc"
fi

if ! grep -q '^status: delivered' "$PROCESS"; then
  cat >> "$PROCESS" <<EOF
wrapper_status: blocked_after_cli_return
wrapper_updated: $(timestamp)
wrapper_summary: Codex CLI returned zero but the generator process file did not report delivered.
EOF
  exit 3
fi
