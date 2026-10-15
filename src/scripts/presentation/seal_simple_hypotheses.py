"""Verify and seal the fresh A/B bundle and register each displayed asset."""

import hashlib
import json
from pathlib import Path
import shutil
import sys

from simple_research_home import ROOT, SUITE
from prepare_simple_media import seal

sys.path.insert(0, str(ROOT / "src"))
from slam_learning.runtime.runner import verify_record  # noqa: E402


def main():
    folder = ROOT / SUITE
    assert (folder / "completed.json").exists()
    assert not (folder / "record.json").exists()
    sources = folder / "sources"
    sources.mkdir(exist_ok=False)
    for name in [
        "run_live.sh",
        "prepare_session.py",
        "observe_session.py",
        "fastlio_study.py",
        "fastlio_transport.py",
        "fastlio_study.launch.py",
        "fastlio_fixed_maps.py",
        "score_fastlio_study.py",
        "score_direction_time_grid.py",
        "score_direction_3d_b.py",
        "compare_corridor_geometry.py",
        "direction_landmarks.py",
        "package_simple_hypotheses.py",
        "package_direction_run.py",
        "freeze_direction_mapping_a.py",
        "audit_fastlio_inputs.py",
    ]:
        shutil.copyfile(Path(__file__).parent / name, sources / name)
    for name in ["live.py", "worker.cpp", "evaluate.py", "export_grid.py"]:
        shutil.copyfile(Path(__file__).parent / "srrg" / name, sources / ("srrg-" + name))
    for name in ["presentation.ps1", "record-methods.ps1", "record-hypotheses.ps1", "srrg.ps1"]:
        shutil.copyfile(ROOT / "demo" / name, sources / name)
    old_sources = ROOT / "results/reference/direction-20261016/sources"
    for name in ["upstream-commit.txt", "build-compatibility.patch", "build_fastlio_study.sh"]:
        shutil.copyfile(old_sources / name, sources / name)
    children = [
        folder / ("2d-" + prefix + scene) / "record.json"
        for scene in ["static", "dynamic", "corridor", "landmark-corridor"]
        for prefix in ["", "A-"]
    ]
    children += [folder / name / "record.json" for name in ["fastlio-motion", "fastlio-B"]]
    for child in children:
        issues = verify_record(child)
        assert not issues, (child, issues)
        source_run = Path(json.loads(child.read_text(encoding="utf-8"))["source_run"])
        assert json.loads((source_run / "session-stopped.json").read_text())["exit_code"] == 0
        assert json.loads((source_run / "metrics.json").read_text())["status"] == "completed"
        capture = folder / "native-capture-metadata" / child.parent.name
        capture.mkdir(parents=True, exist_ok=False)
        for name in [
            "session-stopped.json",
            "video-probe.json",
            "mirror.json",
            "recording.started",
            "recording.stopped",
            "capture-filter.txt",
            "capture-progress.txt",
            "capture.log",
        ]:
            if (source_run / name).exists():
                shutil.copyfile(source_run / name, capture / name)
        for source in (source_run / "executions").glob("*.txt"):
            shutil.copyfile(source, capture / source.name)
    excluded = []
    for name in [
        "20261016-011701-mapping-srrg-corridor-26f670",
        "20261016-011952-mapping-srrg-corridor-31327b",
        "20261016-012606-mapping-srrg-landmark-corridor-dfbda1",
    ]:
        run = ROOT / "results/runs/presentation" / name
        excluded.append(
            {
                "run": str(run),
                "reason": "Capture preflight could not find the WSLg window; no experiment start marker. Excluded."
                if "dfbda1" in name
                else "Native calculation completed, but RViz was minimized and WGC did not record a complete video; excluded from maps, scores and current media.",
                "video_sha256": hashlib.sha256((run / "execution.mp4").read_bytes()).hexdigest(),
                "availability": "local_only",
            }
        )
    (folder / "excluded-attempts.json").write_text(json.dumps(excluded, indent=2) + "\n", encoding="utf-8")
    seal(
        folder,
        kind="fresh_three_hypothesis_ab_experiments",
        scope="Five newly recorded mapping A and five separate localization B sessions on the user's scenes. H1 native Raw/SRRG + AMCL; H2 point-compensation off/on FAST-LIO + independent GICP; H3 original/landmark corridor. Existing 3D Raw/DUFOMap/BeautyMap records are unchanged.",
        hypotheses={
            "H1": ["2d-A-static", "2d-static", "2d-A-dynamic", "2d-dynamic"],
            "H2": ["fastlio-motion", "fastlio-maps", "fastlio-B", "fastlio-input-audit.json"],
            "H3": [
                "2d-A-corridor",
                "2d-corridor",
                "2d-A-landmark-corridor",
                "2d-landmark-corridor",
                "corridor-comparison.json",
            ],
        },
        limits=[
            "One exploratory run per arm; not statistical confirmation",
            "SRRG end-to-end maintenance includes pose optimization; pure deletion at fixed poses is still untested",
            "H3 changes physical geometry; it is not a mirror detector",
            "Mirror physics and identification remain open physical-test problems",
            "FAST-LIO uses three measured time-staggered sectors, not a claimed commercial scanning pattern",
            "Raw ROS2 bags are hash-bound and retained locally",
            "Capture restoration changes window visibility only, never estimator inputs",
        ],
    )
    slots_file = ROOT / "docs/figures/slots.json"
    slots = json.loads(slots_file.read_text(encoding="utf-8"))
    known = {item["path"] for item in slots["slots"]}
    assets = [(p, folder / "record.json") for p in folder.rglob("*.gif")]
    for relative in [
        "docs/media/robot/20261016",
        "docs/media/related-pointcloud/20261016",
        "docs/assets/related/20261016-pointcloud",
    ]:
        parent = ROOT / relative
        assets.extend((p, parent / "record.json") for p in parent.iterdir() if p.suffix in [".gif", ".png"])
    for asset, record in assets:
        path = asset.relative_to(ROOT).as_posix()
        if path not in known:
            slots["slots"].append(
                {
                    "id": "simple-hypotheses-" + hashlib.sha256(path.encode()).hexdigest()[:12],
                    "status": "published",
                    "path": path,
                    "caption": {
                        "zh": asset.stem + " · 实验画面或原文点云图",
                        "en": asset.stem + " · experiment capture or original point-cloud figure",
                    },
                    "source_records": [record.relative_to(ROOT).as_posix()],
                    "source_artifact": asset.relative_to(record.parent).as_posix(),
                }
            )
    slots_file.write_text(
        json.dumps(slots, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Verified {len(children)} native A/B records and registered {len(assets)} assets")


if __name__ == "__main__":
    main()
