#!/usr/bin/env python3
"""Extract usage from the documented Codex CLI completion event."""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Mapping
from math import isfinite
from typing import Any


def main() -> int:
    usage = extract_usage(sys.stdin)
    if not usage:
        print("No usage event found in Codex JSON output.", file=sys.stderr)
    print(json.dumps(usage, sort_keys=True))
    return 0


def extract_usage(lines: Iterable[str]) -> dict[str, int | float]:
    usage: dict[str, int | float] = {}
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, Mapping) or event.get("type") != "turn.completed":
            continue
        candidate = event.get("usage")
        if isinstance(candidate, Mapping):
            usage = _normalize_usage(candidate)
    return usage


def _normalize_usage(value: Mapping[str, Any]) -> dict[str, int | float]:
    usage = {
        key: item
        for key, item in value.items()
        if isinstance(key, str) and _is_nonnegative_number(item)
    }
    input_tokens = usage.get("input_tokens")
    cached_input_tokens = usage.get("cached_input_tokens")
    if input_tokens is not None and cached_input_tokens is not None and cached_input_tokens <= input_tokens:
        usage["uncached_input_tokens"] = input_tokens - cached_input_tokens
    return usage


def _is_nonnegative_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return value >= 0
    return isinstance(value, float) and isfinite(value) and value >= 0


if __name__ == "__main__":
    raise SystemExit(main())
