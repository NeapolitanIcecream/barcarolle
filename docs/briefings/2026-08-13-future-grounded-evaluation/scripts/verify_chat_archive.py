#!/usr/bin/env python3
"""Verify the code-extracted ChatGPT share archive without browser screenshots/OCR."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "raw" / "chatgpt-share-messages.json"
MARKDOWN_PATH = ROOT / "raw" / "chatgpt-share-transcript.md"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    payload = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    markdown = MARKDOWN_PATH.read_text(encoding="utf-8")
    messages = payload["messages"]

    assert payload["expected_turns"] == 11
    assert payload["message_count"] == len(messages) == 22
    assert payload["user_message_count"] == 11
    assert payload["assistant_message_count"] == 11

    expected_roles = [role for _ in range(11) for role in ("user", "assistant")]
    assert [message["role"] for message in messages] == expected_roles
    assert [message["turn"] for message in messages] == [
        turn for turn in range(1, 12) for _ in range(2)
    ]

    for message in messages:
        assert message["character_count"] == len(message["text"])
        if message["role"] == "assistant":
            assert message["channel"] == "final"
        heading = f"## 第 {message['turn']} 轮 · {message['role']}"
        assert heading in markdown
        assert message["text"] in markdown

    report = {
        "status": "pass",
        "verification_method": "structured payload + exact text assertions; no OCR",
        "turn_count": 11,
        "message_count": 22,
        "role_sequence": "user,assistant repeated 11 times",
        "text_character_count": sum(len(message["text"]) for message in messages),
        "json_sha256": digest(JSON_PATH),
        "markdown_sha256": digest(MARKDOWN_PATH),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
