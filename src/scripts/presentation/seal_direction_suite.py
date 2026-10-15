"""Bind published Q1/Q2/Q3 media to native records and final score sidecars."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SUITE = ROOT / "results/reference/direction-20261016"


def seal():
    path = SUITE / "record.json"
    if path.exists():
        raise ValueError("The published experiment bundle is already sealed")
    files = [
        p for p in SUITE.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    ]
    artifacts = {
        p.relative_to(SUITE).as_posix(): {
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "bytes": p.stat().st_size,
            "availability": "portable",
        }
        for p in files
    }
    report = {
        "schema_version": 1,
        "kind": "three_direction_question_experiments",
        "status": "executed",
        "exit_code": 0,
        "scope": "Exploratory single runs on the user's Gazebo scenes; native 2D Raw/SRRG and fixed AMCL B, FAST-LIO2 point-compensation ablation and separate GICP B, corridor environment intervention, controlled missing-return replay. Original 3D Raw/DUFOMap/BeautyMap tests remain unchanged. Not an original-paper benchmark reproduction.",
        "hypotheses": {
            "H1": ["2d-A-static", "2d-A-dynamic", "2d-A-corridor", "2d-static", "2d-dynamic", "2d-corridor"],
            "H2": ["fastlio-motion", "fastlio-maps", "fastlio-B", "fastlio-input-audit.json"],
            "H3": [
                "mirror-control",
                "corridor-landmark-mapping",
                "2d-landmark-corridor",
                "corridor-comparison.json",
            ],
        },
        "fastlio_author_source": "https://github.com/hku-mars/FAST_LIO/tree/ROS2",
        "fastlio_author_commit": (SUITE / "sources/upstream-commit.txt").read_text().strip(),
        "implementation_changes": "C++17 build compatibility and Livox message-only dependency; disclosed environment switch skips point correction only. Native scan adapter filters nonfinite points and gates synchronized IMU/scans until t>=3s. No truth supplied to estimators; a single initial-pose anchor is used when freezing/scoring FAST-LIO registered clouds.",
        "limits": [
            "Single exploratory runs; no statistical significance claim",
            "2D native mapping estimates poses, so it does not isolate point removal",
            "Fresh-update coverage is not a tracking-loss rate",
            "E3a is a fixed-pose missing-return semantics control, not a mirror detector, reflection simulator or localization test",
            "H3 corridor intervention changes physical geometry",
            "Raw ROS2 input bags are retained locally and hash-identified in child records",
        ],
        "artifacts": artifacts,
    }
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    slots_path = ROOT / "docs/figures/slots.json"
    data = json.loads(slots_path.read_text(encoding="utf-8"))
    existing = {slot["id"] for slot in data["slots"]}
    assets = [(p, "results/reference/direction-20261016/record.json") for p in files if p.suffix == ".gif"]
    for folder in [ROOT / "docs/assets/related/20261016", ROOT / "docs/media/direction/20261016-user"]:
        assets += [(p, (folder / "record.json").relative_to(ROOT).as_posix()) for p in folder.glob("*.png")]
    for p, source in assets:
        relative = p.relative_to(ROOT).as_posix()
        key = "direction-20261016-" + hashlib.sha256(relative.encode()).hexdigest()[:12]
        if key in existing:
            continue
        artifact = p.relative_to((ROOT / source).parent).as_posix()
        data["slots"].append(
            {
                "id": key,
                "status": "published",
                "path": relative,
                "caption": {"zh": p.stem + " · 当前方向证据", "en": p.stem + " · current direction evidence"},
                "source_records": [source],
                "source_artifact": artifact,
            }
        )
    slots_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Sealed {len(artifacts)} portable artifacts; registered {len(assets)} images/GIFs.")


if __name__ == "__main__":
    seal()
