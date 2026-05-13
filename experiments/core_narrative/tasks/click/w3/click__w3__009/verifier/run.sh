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
exec .venv/bin/python -m pytest -q tests/test_options.py::test_show_default_string tests/test_options.py::test_string_show_default_shows_custom_string_in_prompt tests/test_termui.py::test_false_show_default_cause_no_default_display_in_prompt tests/test_termui.py::test_string_show_default_shows_custom_string_in_prompt
