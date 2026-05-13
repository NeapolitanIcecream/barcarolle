#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
hidden_dir="$script_dir/hidden"
if [ -d "$hidden_dir" ]; then
  while IFS= read -r -d '' file; do
    rel="${file#$hidden_dir/}"
    mkdir -p "$(dirname "$rel")"
    cp "$file" "$rel"
  done < <(find "$hidden_dir" -type f -print0)
fi
exec .venv/bin/python -m pytest -q tests/test_commands.py::test_object_propagation tests/test_commands.py::test_other_command_invoke_with_defaults
