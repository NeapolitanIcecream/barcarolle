#!/usr/bin/env zsh
set -euo pipefail

task_file="${BARCAROLLE_TASK_FILE:-.barcarolle/TASK.md}"
script_dir="${0:A:h}"
events_file=".barcarolle/codex-events.jsonl"
usage_file=".barcarolle/usage.json"

fail() {
  print -u2 -- "codex-cli harness: $1"
  exit "${2:-1}"
}

toml_string() {
  local value="$1"
  if [[ "$value" == *$'\n'* || "$value" == *$'\r'* ]]; then
    fail "config values must be single-line strings" 64
  fi
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  print -r -- "\"$value\""
}

if [[ ! -f "$task_file" ]]; then
  fail "missing solver-visible task file: $task_file" 64
fi

if [[ -z "${BARCAROLLE_CODEX_HOME:-}" ]]; then
  fail "BARCAROLLE_CODEX_HOME must point to an isolated Codex home" 64
fi

if [[ "$BARCAROLLE_CODEX_HOME" != /* ]]; then
  fail "BARCAROLLE_CODEX_HOME must be an absolute path" 64
fi

isolated_codex_home="$BARCAROLLE_CODEX_HOME"
mkdir -p "$isolated_codex_home"

if [[ -z "${OPENAI_BASE_URL:-}" || -z "${OPENAI_API_KEY:-}" ]]; then
  if [[ -f "$HOME/.zshrc" ]]; then
    set +u
    source "$HOME/.zshrc"
    set -u
  fi
fi

if [[ -z "${OPENAI_BASE_URL:-}" ]]; then
  fail "OPENAI_BASE_URL is required for benchmark Codex calls" 65
fi

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  fail "OPENAI_API_KEY is required for benchmark Codex calls" 65
fi

if [[ -z "${BARCAROLLE_CODEX_MODEL:-}" ]]; then
  BARCAROLLE_CODEX_MODEL="gpt-5.4"
fi
reasoning_effort="${BARCAROLLE_CODEX_REASONING_EFFORT:-}"
if [[ -n "$reasoning_effort" && "$reasoning_effort" != (none|low|medium|high|xhigh) ]]; then
  fail "BARCAROLLE_CODEX_REASONING_EFFORT must be none, low, medium, high, or xhigh" 64
fi

export CODEX_HOME="$isolated_codex_home"
export OPENAI_BASE_URL
export OPENAI_API_KEY
export BARCAROLLE_CODEX_MODEL

unset OPENAI_MODEL
unset BARCAROLLE_CODEX_REASONING_EFFORT
unset LLM_API_KEY
unset LLM_BASE_URL
unset OPENROUTER_API_KEY
unset ANTHROPIC_API_KEY
unset GOOGLE_API_KEY
unset GEMINI_API_KEY

typeset -a provider_config
provider_config=(
  -c 'model_provider="barcarolle_openai"'
  -c 'model_providers.barcarolle_openai.name="Barcarolle OpenAI endpoint"'
  -c "model_providers.barcarolle_openai.base_url=$(toml_string "$OPENAI_BASE_URL")"
  -c 'model_providers.barcarolle_openai.env_key="OPENAI_API_KEY"'
  -c 'model_providers.barcarolle_openai.wire_api="responses"'
  -c 'model_providers.barcarolle_openai.request_max_retries=0'
  -c 'model_providers.barcarolle_openai.stream_max_retries=0'
  -c 'shell_environment_policy.exclude=["OPENAI_API_KEY","OPENAI_BASE_URL"]'
)
if [[ -n "$reasoning_effort" ]]; then
  provider_config+=( -c "model_reasoning_effort=$(toml_string "$reasoning_effort")" )
fi

rm -f "$events_file" "$usage_file"

set +e
{
  print -- "You are running inside a Barcarolle solver workspace."
  print -- "The complete solver-visible task from .barcarolle/TASK.md is included below; do not reread that file."
  print -- "Make the requested code change in this repository."
  print -- "Use only solver-visible task material. Do not look for verifier-only checks, hidden material, parent-run logs, or output directories."
  print -- "Keep the change focused. Run relevant local checks if practical, then stop."
  print -- ""
  print -- "<barcarolle_task>"
  cat "$task_file"
  print -- "</barcarolle_task>"
} | codex \
  --ask-for-approval never \
  exec \
  --strict-config \
  --ephemeral \
  --json \
  --disable plugins \
  --disable multi_agent \
  --ignore-user-config \
  --ignore-rules \
  --cd "$PWD" \
  --sandbox workspace-write \
  --model "$BARCAROLLE_CODEX_MODEL" \
  "${provider_config[@]}" \
  - > "$events_file"
codex_status=$?
set -e

cat "$events_file"
"$script_dir/extract-usage.py" < "$events_file" > "$usage_file"
rm -f "$events_file"
exit "$codex_status"
