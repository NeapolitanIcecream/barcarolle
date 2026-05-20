from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"


class ValidationError(ValueError):
    pass


@dataclass(frozen=True)
class TaskManifest:
    task_id: str
    repo_id: str
    split: str
    certification_status: str
    module_or_package: list[str]
    task_type_proxy: str
    weight: float = 1.0
    evidence_status: str = "certified"

    def validate(self) -> None:
        if not self.task_id:
            raise ValidationError("task_id is required")
        if not self.repo_id:
            raise ValidationError("repo_id is required")
        if self.split not in {"B_real", "W_real", "G_mini", "dev", "eval", "canary", "holdout"}:
            raise ValidationError(f"unsupported split: {self.split}")
        if self.weight <= 0:
            raise ValidationError("weight must be positive")


@dataclass(frozen=True)
class ReleaseManifest:
    schema_version: str
    release_id: str
    repo_id: str
    source_phase0_release: str
    status: str
    tasks: list[TaskManifest]
    splits: dict[str, list[str]]
    evidence_status: str

    def validate(self) -> None:
        if self.schema_version != "barcarolle.phase1.release_manifest.v1":
            raise ValidationError("unexpected release schema_version")
        if not self.tasks:
            raise ValidationError("release must contain at least one task")
        task_ids = {task.task_id for task in self.tasks}
        for task in self.tasks:
            task.validate()
        for split, ids in self.splits.items():
            missing = [task_id for task_id in ids if task_id not in task_ids]
            if missing:
                raise ValidationError(f"split {split} references missing tasks: {missing}")


@dataclass(frozen=True)
class TargetProfile:
    repo_id: str
    strata: dict[str, dict[str, float]]
    insufficient_evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CertificationReport:
    task_id: str
    gates: dict[str, str]
    status: str


@dataclass(frozen=True)
class AgentRunManifest:
    run_id: str
    acut_id: str
    model: str
    task_ids: list[str]
    measured_cost_usd: float | None


@dataclass(frozen=True)
class ScorecardCell:
    task_id: str
    split: str
    terminal_status: str
    scoreable: bool
    module_or_package: list[str]
    weight: float = 1.0

    @property
    def compatible(self) -> bool:
        return self.scoreable and self.terminal_status in {"verified_pass", "verified_fail"}

    @property
    def score(self) -> float:
        if self.terminal_status == "verified_pass":
            return 1.0
        if self.terminal_status == "verified_fail":
            return 0.0
        raise ValidationError(f"cell is not compatible: {self.task_id}")


@dataclass(frozen=True)
class Scorecard:
    run_id: str
    cells: list[ScorecardCell]


@dataclass(frozen=True)
class WeightedScoreSummary:
    schema_version: str
    run_id: str
    weighted_score: float | None
    evidence_status: str
    stratum_scores: dict[str, dict[str, Any]]
    insufficient_evidence: list[str]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_modules(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if isinstance(raw, str):
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            return [part.strip(" '\"") for part in stripped.strip("[]").split(",") if part.strip()]
        return [stripped] if stripped else ["unknown"]
    return ["unknown"]


def task_from_phase0(row: dict[str, Any], repo_id: str) -> TaskManifest:
    counts = row.get("counts_toward_benchmark_grade")
    certified = row.get("certification_status") == "certified" and counts is True
    evidence_status = "certified" if certified else "insufficient_evidence"
    return TaskManifest(
        task_id=str(row["task_id"]),
        repo_id=repo_id if row.get("split") != "G_mini" else "click",
        split=str(row["split"]),
        certification_status=str(row["certification_status"]),
        module_or_package=normalize_modules(row.get("module_or_package")),
        task_type_proxy=str(row.get("task_type_proxy") or "unknown"),
        weight=float(row.get("weight") or 1.0),
        evidence_status=evidence_status,
    )


def import_phase0_release(phase0_root: Path = PHASE0_ROOT) -> ReleaseManifest:
    source = read_json(phase0_root / "releases" / "toolz_phase0_mini_release.json")
    tasks = [task_from_phase0(row, source["repo_id"]) for row in source["tasks"]]
    release = ReleaseManifest(
        schema_version="barcarolle.phase1.release_manifest.v1",
        release_id=f"{source['release_id']}-phase1-draft",
        repo_id=source["repo_id"],
        source_phase0_release=str((phase0_root / "releases" / "toolz_phase0_mini_release.json").relative_to(REPO_ROOT)),
        status="draft_imported_from_phase0",
        tasks=tasks,
        splits={split: list(ids) for split, ids in source["splits"].items()},
        evidence_status="insufficient_evidence",
    )
    release.validate()
    return release


def load_target_profile(phase0_root: Path = PHASE0_ROOT) -> TargetProfile:
    profile = read_json(phase0_root / "target_profiles" / "toolz_target_profile.json")
    return TargetProfile(
        repo_id=profile["repo_id"],
        strata={
            "module_or_package": {key: float(value) for key, value in profile["overall_distributions"]["module_or_package"].items()},
            "task_type_proxy": {key: float(value) for key, value in profile["overall_distributions"]["task_type_proxy"].items()},
        },
        insufficient_evidence=list(profile.get("missing_data_labels", {}).keys()),
    )


def scorecard_from_phase0(release: ReleaseManifest, phase0_root: Path = PHASE0_ROOT) -> Scorecard:
    rows = read_csv(phase0_root / "results" / "headroom_score_table.csv")
    task_by_id = {task.task_id: task for task in release.tasks}
    cells = []
    for row in rows:
        task = task_by_id.get(row["task_id"])
        if task is None:
            continue
        cells.append(
            ScorecardCell(
                task_id=row["task_id"],
                split=row["split"],
                terminal_status=row["terminal_status"],
                scoreable=row["scoreable_cell"] == "True",
                module_or_package=task.module_or_package,
                weight=task.weight,
            )
        )
    return Scorecard(run_id="phase0_headroom_matrix", cells=cells)


def compute_weighted_score(scorecard: Scorecard, target_profile: TargetProfile) -> WeightedScoreSummary:
    module_weights = target_profile.strata.get("module_or_package", {})
    cells_by_module: dict[str, list[ScorecardCell]] = {}
    for cell in scorecard.cells:
        module = cell.module_or_package[0] if cell.module_or_package else "unknown"
        cells_by_module.setdefault(module, []).append(cell)

    stratum_scores: dict[str, dict[str, Any]] = {}
    insufficient: list[str] = []
    weighted_total = 0.0
    weight_total = 0.0
    for module, weight in sorted(module_weights.items()):
        cells = cells_by_module.get(module, [])
        compatible = [cell for cell in cells if cell.compatible]
        incompatible = [cell for cell in cells if not cell.compatible]
        if not compatible or incompatible:
            insufficient.append(module)
            stratum_scores[module] = {
                "target_weight": weight,
                "evidence_status": "insufficient_evidence",
                "compatible_cell_count": len(compatible),
                "incompatible_cell_count": len(incompatible),
                "score": None,
            }
            continue
        score = sum(cell.score for cell in compatible) / len(compatible)
        weighted_total += score * weight
        weight_total += weight
        stratum_scores[module] = {
            "target_weight": weight,
            "evidence_status": "compatible",
            "compatible_cell_count": len(compatible),
            "incompatible_cell_count": 0,
            "score": round(score, 6),
        }

    weighted_score = None if insufficient or weight_total == 0 else round(weighted_total / weight_total, 6)
    return WeightedScoreSummary(
        schema_version="barcarolle.phase1.weighted_score_summary.v1",
        run_id=scorecard.run_id,
        weighted_score=weighted_score,
        evidence_status="compatible" if weighted_score is not None else "insufficient_evidence",
        stratum_scores=stratum_scores,
        insufficient_evidence=insufficient,
    )


def run_import_phase0(args: argparse.Namespace) -> None:
    phase0_root = Path(args.phase0_root).resolve()
    release = import_phase0_release(phase0_root)
    target_profile = load_target_profile(phase0_root)
    scorecard = scorecard_from_phase0(release, phase0_root)
    weighted = compute_weighted_score(scorecard, target_profile)
    output_dir = Path(args.output_dir)
    write_json(output_dir / "toolz_phase1_draft_release.json", asdict(release))
    write_json(output_dir / "toolz_phase1_weighted_score.json", asdict(weighted))


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1 benchmark compiler skeleton.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    import_parser = subcommands.add_parser("import-phase0", help="Import the current Phase 0 toolz release.")
    import_parser.add_argument("--phase0-root", default=str(PHASE0_ROOT))
    import_parser.add_argument("--output-dir", default=str(ROOT / "results"))
    args = parser.parse_args()
    if args.command == "import-phase0":
        run_import_phase0(args)
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
