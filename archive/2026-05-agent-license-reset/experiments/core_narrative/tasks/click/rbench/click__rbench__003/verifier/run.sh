#!/usr/bin/env bash
set -euo pipefail
# Run from the prepared task workspace. The coordinator keeps this script outside ACUT-visible inputs.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
hidden_dir="$script_dir/hidden"
if [ -d "$hidden_dir" ]; then
  while IFS= read -r -d '' file; do
    rel="${file#$hidden_dir/}"
    mkdir -p "$(dirname "$rel")"
    cp "$file" "$rel"
  done < <(find "$hidden_dir" -type f -print0)
fi
exec .venv/bin/python -c 'import click._termui_impl, pytest, sys; sys.exit(pytest.main(["-q", "tests/test_termui.py::test_choices_list_in_prompt"]))' tests/test_termui.py::test_choices_list_in_prompt
