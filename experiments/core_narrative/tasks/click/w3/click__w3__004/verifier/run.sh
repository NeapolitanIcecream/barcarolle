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
exec .venv/bin/python -m pytest -q tests/test_defaults.py::test_shared_param_prefers_first_default tests/test_defaults.py::test_lookup_default_returns_hides_sentinel tests/test_defaults.py::test_lookup_default_callable_in_default_map tests/test_defaults.py::test_default_map_source
