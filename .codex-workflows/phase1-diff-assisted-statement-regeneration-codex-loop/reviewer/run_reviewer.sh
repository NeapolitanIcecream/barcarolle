#!/usr/bin/env bash
set -euo pipefail
cd /Users/chenmohan/gits/barcarolle

WORKFLOW=".codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop"
PROCESS=".codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/reviewer/process.md"
LOG=".codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/reviewer/cli.log"

timestamp() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

if ! { test -n "${LLM_BASE_URL:-}" && test -n "${LLM_API_KEY:-}"; }; then
  test -f ~/.zshrc && source ~/.zshrc >/dev/null 2>&1 || true
fi

if ! { test -n "${LLM_BASE_URL:-}" && test -n "${LLM_API_KEY:-}"; }; then
  cat > "$PROCESS" <<EOF
status: blocked
updated: $(timestamp)
summary: Required LLM_BASE_URL or LLM_API_KEY was missing before the external Codex CLI reviewer call.
session: phase1-diffstmt-reviewer
EOF
  exit 2
fi

mkdir -p "$WORKFLOW/reviewer/output"
cat > "$PROCESS" <<EOF
status: working
updated: $(timestamp)
summary: External Codex CLI reviewer wrapper started with required endpoint environment present.
session: phase1-diffstmt-reviewer
EOF

set +e
codex exec \
  --ignore-user-config \
  -C /Users/chenmohan/gits/barcarolle \
  -m gpt-5.5 \
  -c 'model="gpt-5.5"' \
  -c 'model_provider="barcarolle_llm"' \
  -c 'model_providers.barcarolle_llm.name="Barcarolle LLM Endpoint"' \
  -c "model_providers.barcarolle_llm.base_url=\"${LLM_BASE_URL}\"" \
  -c 'model_providers.barcarolle_llm.wire_api="responses"' \
  -c 'model_providers.barcarolle_llm.env_key="LLM_API_KEY"' \
  -c 'model_reasoning_effort="xhigh"' \
  --dangerously-bypass-approvals-and-sandbox \
  - < ".codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/reviewer/prompt.md" \
  > "$LOG" \
  2>&1
rc=$?
set -e

if [ "$rc" -ne 0 ]; then
  cat > "$PROCESS" <<EOF
status: blocked
updated: $(timestamp)
summary: External Codex CLI reviewer exited non-zero. Raw log is intentionally ignored and not committed.
session: phase1-diffstmt-reviewer
exit_code: $rc
EOF
  exit "$rc"
fi

if ! grep -q '^status: delivered' "$PROCESS"; then
  cat >> "$PROCESS" <<EOF
wrapper_status: blocked_after_cli_return
wrapper_updated: $(timestamp)
wrapper_summary: Codex CLI returned zero but the reviewer process file did not report delivered.
EOF
  exit 3
fi
