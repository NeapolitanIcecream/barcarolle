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
exec .venv/bin/python -m pytest -q tests/test_basic.py::test_boolean_conversion tests/test_options.py::test_type_from_flag_value tests/test_options.py::test_invalid_flag_definition tests/test_options.py::test_custom_type_flag_value_standalone_option tests/test_termui.py::test_false_show_default_cause_no_default_display_in_prompt tests/test_termui.py::test_flag_value_prompt
