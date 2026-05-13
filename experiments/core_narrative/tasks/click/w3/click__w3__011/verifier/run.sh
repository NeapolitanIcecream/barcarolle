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
exec .venv/bin/python -m pytest -q tests/test_termui.py::test_edit tests/test_termui.py::test_editor_path_normalization tests/test_termui.py::test_editor_windows_path_normalization tests/test_termui.py::test_editor_env_passed_through
