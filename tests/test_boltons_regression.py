from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from examples.boltons_regression import run as boltons_regression  # noqa: E402


EXPECTED_ASSET_DIGESTS = {
    "boltons-cacheutils-lri-keyword-update": (
        "80cae290b78eff22c0db17db517aeadbeabc796599246a55545398c4eab4e6b2",
        "bd4611e34da58e3427936b0da8a06fdd9bf1a4fa24123abb17096b6f5e63d871",
    ),
    "boltons-dictutils-omd-keyword-update": (
        "eedea106f80efb0485f2e932d178d2b7d62e4725a190b197120b4f4af5ca47f7",
        "1bed27ec6e9796d59964d0890ce4c74cf475ff5bb68da6bb759a00373b18f355",
    ),
    "boltons-iterutils-chunked-iter-count": (
        "0abdaf1b1d22b3a5679d8b0faec6c74384952a018ad61299929a62bea38d43f1",
        "c07a789427ba817889297b57cd4eddcdc1e66534b5adee5c210c8d35f7661dae",
    ),
    "boltons-iterutils-windowed-positive-size": (
        "16e955d4ed58a607096d2df591c570368aeca84d7eaba008a294ae952420541e",
        "cab2d6a53cdde53249543d1762bffd8c1b6174188d941632b5df939de8079b00",
    ),
    "boltons-urlutils-parse-qsl-blank-values": (
        "4fc7f5a434110d5571e6c9d49eeed77ba799e428767a98534cf1e2556cb919da",
        "03b5b824839d8dd76b4d183f2392a5e822d9dd14176ea68d8cfa4e314b045665",
    ),
}


def test_boltons_regression_assets_are_complete_and_stable() -> None:
    assert len(boltons_regression.TASK_INPUTS) == 5
    assert {task.source_ref for task in boltons_regression.TASK_INPUTS} == set(
        EXPECTED_ASSET_DIGESTS
    )

    for task in boltons_regression.TASK_INPUTS:
        expected_patch_digest, expected_check_digest = EXPECTED_ASSET_DIGESTS[
            task.source_ref
        ]
        patch = (
            boltons_regression.HERE / "reference-patches" / f"{task.source_ref}.diff"
        )
        hidden_check = (
            boltons_regression.HERE / "hidden-checks" / task.source_ref / "test_task.py"
        )
        assert hashlib.sha256(patch.read_bytes()).hexdigest() == expected_patch_digest
        assert (
            hashlib.sha256(hidden_check.read_bytes()).hexdigest()
            == expected_check_digest
        )
        assert task.solver_material_refs


def test_boltons_regression_cli_identifies_no_paid_scope() -> None:
    completed = subprocess.run(
        [sys.executable, "examples/boltons_regression/run.py", "--help"],
        cwd=REPOSITORY_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    assert "no-paid" in completed.stdout
    assert "--target-repo" in completed.stdout


def test_boltons_real_target_certification_and_scripted_results(tmp_path: Path) -> None:
    configured_target = os.environ.get("BARCAROLLE_BOLTONS_REPO")
    if configured_target is None:
        pytest.skip("set BARCAROLLE_BOLTONS_REPO to opt into the real-target test")
    target_repo = Path(configured_target)

    output_dir = tmp_path / "boltons-regression"
    subprocess.run(
        [
            sys.executable,
            "examples/boltons_regression/run.py",
            "--target-repo",
            str(target_repo),
            "--output-dir",
            str(output_dir),
        ],
        cwd=REPOSITORY_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["certified_base_fail_count"] == 5
    assert summary["certified_reference_pass_count"] == 5
    assert summary["scripted_pass_count"] == 5
    assert summary["scripted_result_count"] == 5
    assert summary["paid_call_count"] == 0
    assert summary["predictive_evidence"] is False

    certification = tuple(
        json.loads(line)
        for line in (output_dir / "records/certification-evidence.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    results = tuple(
        json.loads(line)
        for line in (output_dir / "records/results.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    assert all(record["base_check"][0]["outcome"] == "fail" for record in certification)
    assert all(
        record["reference_patch_check"][0]["outcome"] == "pass"
        for record in certification
    )
    assert all(record["outcome"] == "pass" for record in results)
    assert all(record["cost"]["total_cost"] is None for record in results)
