"""Verify new runs, seal portable artifacts and bind the published recordings."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from summarize_map_hypotheses import summarize

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))


def seal(folder):
    from slam_learning.core.provenance import digest
    from slam_learning.runtime.runner import verify_record

    if (folder / "record.json").exists():
        raise ValueError("Already sealed; retain the existing batch")
    checked = []
    for scene in ("static", "dynamic", "corridor"):
        for stage in ("mapping-a", "localization-3d"):
            record = folder / scene / stage / "record.json"
            errors = verify_record(record)
            if errors:
                raise ValueError(errors)
            checked.append(record.relative_to(ROOT).as_posix())
        terminal = json.loads((folder / scene / "map-processing/recording.json").read_text())
        assert terminal["command_exit_code"] == 0 and terminal["full_video_decoded"]
        assert not (folder / scene / "map-processing/private.Xauthority").exists()
    verified = json.loads((folder / "map-score-verification.json").read_text())
    assert all(row["all_reported_metrics_recomputed"] for row in verified.values())
    summary = summarize(folder)
    for name in ("current_hypothesis_practice.py", "summarize_map_hypotheses.py",
                 "package_hypothesis_scores.py", "seal_map_hypotheses.py"):
        shutil.copyfile(Path(__file__).with_name(name), folder / "sources" / name)
    record = {
        "schema_version": 1, "kind": "map_hypothesis_simulation_batch", "status": "executed", "exit_code": 0,
        "scope": "Provided-pose map-quality intervention followed by fresh held-out GICP localization; static/dynamic/corridor, one session each. No autonomous SLAM, hardware or mirror claim.",
        "checked_native_records": checked, "truth_input_to_localizers": False,
        "trials_per_scene": 1, "limitations": summary["limitations"],
        "artifacts": {p.relative_to(folder).as_posix(): {"sha256": digest(p), "bytes": p.stat().st_size,
                                                       "availability": "portable"}
                      for p in folder.rglob("*") if p.is_file()},
    }
    (folder / "record.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    assert not verify_record(folder / "record.json", full=True)
    registry_path = ROOT / "docs/figures/slots.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    prefix = folder.relative_to(ROOT).as_posix()
    for scene, cn, en in (("static", "静态", "Static"), ("dynamic", "动态", "Dynamic"),
                          ("corridor", "长廊", "Corridor")):
        assets = [("mapping-a/execution.gif", "A采集", "mapping-A acquisition"),
                  ("map-processing/full-session.gif", "三方法实际处理终端", "actual map-processing terminal"),
                  *[(f"localization-3d/executions/{method}.gif", method + "独立B定位", method + " held-out B")
                    for method in ("raw", "dufomap", "beautymap")]]
        for path, title_cn, title_en in assets:
            target = prefix + "/" + scene + "/" + path
            identity = "map-hypotheses-20261015-" + scene + "-" + path.replace("/", "-").replace(".gif", "")
            assert not any(item["id"] == identity for item in registry["slots"])
            registry["slots"].append({
                "id": identity, "status": "published", "path": target,
                "caption": {"zh": cn + " · " + title_cn, "en": en + " · " + title_en},
                "source_records": [prefix + "/record.json"], "source_artifact": scene + "/" + path,
            })
    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Sealed {len(record['artifacts'])} artifacts; registered 15 new recording previews")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    seal(parser.parse_args().folder.resolve())
