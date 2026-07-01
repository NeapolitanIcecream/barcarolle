#!/usr/bin/env zsh
set -euo pipefail

task_file="${BARCAROLLE_TASK_FILE:-.barcarolle/TASK.md}"

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

mkdir -p "$BARCAROLLE_CODEX_HOME"
export CODEX_HOME="$BARCAROLLE_CODEX_HOME"

if [[ -z "${LLM_BASE_URL:-}" || -z "${LLM_API_KEY:-}" ]]; then
  if [[ -f "$HOME/.zshrc" ]]; then
    set +u
    source "$HOME/.zshrc"
    set -u
  fi
fi

if [[ -z "${LLM_BASE_URL:-}" ]]; then
  fail "LLM_BASE_URL is required for benchmark Codex calls" 65
fi

if [[ -z "${LLM_API_KEY:-}" ]]; then
  fail "LLM_API_KEY is required for benchmark Codex calls" 65
fi

if [[ -z "${BARCAROLLE_CODEX_MODEL:-}" ]]; then
  BARCAROLLE_CODEX_MODEL="gpt-5.4"
fi

export LLM_BASE_URL
export LLM_API_KEY
export BARCAROLLE_CODEX_MODEL

unset OPENAI_API_KEY
unset OPENAI_BASE_URL
unset OPENROUTER_API_KEY
unset ANTHROPIC_API_KEY
unset GOOGLE_API_KEY
unset GEMINI_API_KEY

typeset -a provider_config
provider_config=(
  -c 'model_provider="barcarolle_llm"'
  -c 'model_providers.barcarolle_llm.name="Barcarolle LLM"'
  -c "model_providers.barcarolle_llm.base_url=$(toml_string "$LLM_BASE_URL")"
  -c 'model_providers.barcarolle_llm.env_key="LLM_API_KEY"'
  -c 'model_providers.barcarolle_llm.wire_api="responses"'
)

{
  print -- "You are running inside a Barcarolle solver workspace."
  print -- "Read .barcarolle/TASK.md and make the requested code change in this repository."
  print -- "Use only solver-visible task material. Do not look for verifier-only checks, hidden material, parent-run logs, or output directories."
  print -- "Keep the change focused. Run relevant local checks if practical, then stop."
  print -- ""
  print -- "<barcarolle_task>"
  cat "$task_file"
  print -- "</barcarolle_task>"
} | codex \
  --ask-for-approval never \
  exec \
  --json \
  --disable plugins \
  --ignore-user-config \
  --ignore-rules \
  --cd "$PWD" \
  --sandbox workspace-write \
  --model "$BARCAROLLE_CODEX_MODEL" \
  "${provider_config[@]}" \
  -
