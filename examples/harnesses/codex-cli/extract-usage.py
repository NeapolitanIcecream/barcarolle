#!/usr/bin/env python3
"""Best-effort usage extraction for the Codex CLI harness example."""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Mapping
from typing import Any


INPUT_KEYS = ("input_tokens", "prompt_tokens")
OUTPUT_KEYS = ("output_tokens", "completion_tokens")
TOTAL_KEYS = ("total_tokens",)
USAGE_CONTAINER_KEYS = ("usage", "token_usage", "token_counts")


def main() -> int:
    usage = extract_usage(sys.stdin)
    if not usage:
        print("No usage event found in Codex JSON output.", file=sys.stderr)
    print(json.dumps(usage, sort_keys=True))
    return 0


def extract_usage(lines: Iterable[str]) -> dict[str, int]:
    best: dict[str, int] = {}
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        for candidate in _usage_candidates(event):
            normalized = _normalize_usage(candidate)
            if _candidate_score(normalized) >= _candidate_score(best):
                best = normalized
    return best


def _usage_candidates(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        if _looks_like_usage(value):
            yield value
        for key in USAGE_CONTAINER_KEYS:
            child = value.get(key)
            if isinstance(child, Mapping):
                yield child
        for child in value.values():
            yield from _usage_candidates(child)
    elif isinstance(value, list):
        for child in value:
            yield from _usage_candidates(child)


def _looks_like_usage(value: Mapping[str, Any]) -> bool:
    keys = set(value)
    return bool(keys & set(INPUT_KEYS + OUTPUT_KEYS + TOTAL_KEYS))


def _normalize_usage(value: Mapping[str, Any]) -> dict[str, int]:
    usage: dict[str, int] = {}
    input_tokens = _first_int(value, INPUT_KEYS)
    output_tokens = _first_int(value, OUTPUT_KEYS)
    total_tokens = _first_int(value, TOTAL_KEYS)
    if input_tokens is not None:
        usage["input_tokens"] = input_tokens
    if output_tokens is not None:
        usage["output_tokens"] = output_tokens
    if total_tokens is not None:
        usage["total_tokens"] = total_tokens
    elif input_tokens is not None and output_tokens is not None:
        usage["total_tokens"] = input_tokens + output_tokens
    return usage


def _first_int(value: Mapping[str, Any], keys: tuple[str, ...]) -> int | None:
    for key in keys:
        item = value.get(key)
        if isinstance(item, int) and not isinstance(item, bool) and item >= 0:
            return item
    return None


def _candidate_score(value: Mapping[str, int]) -> tuple[int, int]:
    return (len(value), int(value.get("total_tokens", 0)))


if __name__ == "__main__":
    raise SystemExit(main())
