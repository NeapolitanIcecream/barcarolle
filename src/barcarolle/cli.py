"""Minimal command-line entry points for offline Barcarolle records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping, Sequence, TypeVar

from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    EvaluationCellSet,
    FeatureSnapshotRecord,
    MetricRecord,
    ResultMatrix,
    ResultRecord,
    RollingOriginRecord,
    SelectorInput,
    SelectorRecord,
    TaskPoolRecord,
    canonical_json,
    load_jsonl_records,
)
from barcarolle.runner import ReportConfig, write_report


_REPORT_PATH_KEYS = (
    "task_pool",
    "future_task_pools",
    "agents",
    "selectors",
    "origins",
    "feature_snapshots",
    "selector_inputs",
    "selections",
    "results",
    "evaluation_cell_sets",
    "result_matrices",
    "metrics",
    "artifact_root",
    "output_dir",
)
_REQUIRED_REPORT_PATH_KEYS = ("task_pool", "output_dir")
_RecordT = TypeVar("_RecordT")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        summary = _write_report_from_config(args.config)
    except (OSError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    print(canonical_json(summary))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="barcarolle")
    commands = parser.add_subparsers(dest="command", required=True)
    report = commands.add_parser(
        "report", help="write a report from existing JSONL records"
    )
    report.add_argument("config", type=Path, help="path to the report JSON config")
    return parser


def _write_report_from_config(config_path: Path) -> Mapping[str, object]:
    config = _load_report_config(config_path)
    task_pools = load_jsonl_records(config["task_pool"], TaskPoolRecord)
    if len(task_pools) != 1:
        raise ValueError("task_pool must contain exactly one TaskPoolRecord")
    agents = tuple(_load_optional_records(config, "agents", AgentRecord))
    return write_report(
        task_pools[0],
        _load_optional_records(config, "selections", BenchmarkSelectionRecord),
        _load_optional_records(config, "results", ResultRecord),
        _load_optional_records(config, "evaluation_cell_sets", EvaluationCellSet),
        _load_optional_records(config, "result_matrices", ResultMatrix),
        _load_optional_records(config, "metrics", MetricRecord),
        ReportConfig(
            output_dir=config["output_dir"],
            agents=agents,
            artifact_root=config.get("artifact_root", config_path.resolve().parent),
        ),
        selectors=_load_optional_records(config, "selectors", SelectorRecord),
        origins=_load_optional_records(config, "origins", RollingOriginRecord),
        feature_snapshots=_load_optional_records(
            config,
            "feature_snapshots",
            FeatureSnapshotRecord,
        ),
        selector_inputs=_load_optional_records(
            config, "selector_inputs", SelectorInput
        ),
        future_task_pools=_load_optional_records(
            config,
            "future_task_pools",
            TaskPoolRecord,
        ),
    )


def _load_report_config(config_path: Path) -> dict[str, Path]:
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("report config must be a JSON object")
    missing = tuple(key for key in _REQUIRED_REPORT_PATH_KEYS if key not in raw)
    unknown = tuple(sorted(set(raw) - set(_REPORT_PATH_KEYS)))
    if missing:
        raise ValueError(f"report config is missing: {', '.join(missing)}")
    if unknown:
        raise ValueError(f"report config has unknown keys: {', '.join(unknown)}")
    base_dir = config_path.resolve().parent
    paths: dict[str, Path] = {}
    for key, value in raw.items():
        if not isinstance(value, str) or not value:
            raise ValueError(f"report config {key} must be a non-empty path string")
        path = Path(value)
        paths[key] = path if path.is_absolute() else base_dir / path
    return paths


def _load_optional_records(
    config: Mapping[str, Path], key: str, record_type: type[_RecordT]
) -> list[_RecordT]:
    path = config.get(key)
    return [] if path is None else load_jsonl_records(path, record_type)
