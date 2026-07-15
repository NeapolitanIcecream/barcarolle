#!/usr/bin/env python3
"""Apply the known-good patch for the current boltons regression Task."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


PATCH_BY_TITLE = {
    "Add count support to chunked_iter": "boltons-iterutils-chunked-iter-count.diff",
    "Reject non-positive window sizes": "boltons-iterutils-windowed-positive-size.diff",
    "Preserve explicitly blank query values": "boltons-urlutils-parse-qsl-blank-values.diff",
    "Allow keyword-only OrderedMultiDict.update": "boltons-dictutils-omd-keyword-update.diff",
    "Allow keyword-only LRI and LRU updates": "boltons-cacheutils-lri-keyword-update.diff",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch-dir", type=Path, required=True)
    args = parser.parse_args()

    task_lines = (
        (Path.cwd() / ".barcarolle" / "TASK.md")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    try:
        title = next(line for line in task_lines[1:] if line.strip())
        patch_name = PATCH_BY_TITLE[title]
    except (KeyError, StopIteration) as exc:
        raise RuntimeError("scripted Agent received an unknown Task") from exc

    subprocess.run(
        (
            "git",
            "apply",
            "--whitespace=nowarn",
            str(args.patch_dir.resolve() / patch_name),
        ),
        cwd=Path.cwd(),
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
