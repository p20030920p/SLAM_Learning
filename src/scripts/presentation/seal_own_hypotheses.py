"""Verify paired frozen maps, native captures and source identity, then seal."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal(suite):
    assert not (suite / "record.json").exists(), "Evidence already sealed"
    sources = set()
    children, bindings = [], []
    (suite / "native-capture-metadata").mkdir()
    for scene in ("static", "dynamic", "motion", "corridor"):
        a, b = suite / (scene + "-A"), suite / (scene + "-B")
        for folder in (a, b):
            record = folder / "record.json"
            data = json.loads(record.read_text())
            assert data["status"] == "executed" and data["exit_code"] == 0
            for name, info in data["artifacts"].items():
                assert sha(folder / name) == info["sha256"], str(folder / name)
            children.append(record.relative_to(suite).as_posix())
            source_run = Path(data["source_run"])
            stop = json.loads((source_run / "session-stopped.json").read_text())
            assert stop["exit_code"] == 0 and (source_run / "recording.started").is_file()
            metadata_dir = suite / "native-capture-metadata" / folder.name
            metadata_dir.mkdir()
            metadata = [source_run / name for name in ("recording.started", "recording.stopped", "session-stopped.json", "capture-filter.txt", "capture-progress.txt", "capture.log")]
            metadata += [p for p in (source_run / "executions").glob("*") if p.suffix != ".mp4"]
            for file in metadata:
                if file.is_file():
                    shutil.copyfile(file, metadata_dir / file.name)
        assert json.loads((a / "own-finished.json").read_text())["truth_used"] is False
        assert json.loads((a / "session.json").read_text())["provided_mapping_poses"] is False
        for case, settings in json.loads((b / "cases.json").read_text()).items():
            method = settings["method"]
            left, right = a / "maps" / method / "map.pgm", b / "maps" / case / "map.pgm"
            assert sha(left) == sha(right)
            bindings.append({"scene": scene, "case": case, "mapping_method": method, "map_sha256": sha(left)})
        assert json.loads((a / "runtime.json").read_text())["world_sha256"] == json.loads((b / "runtime.json").read_text())["world_sha256"]
        for video in [*a.glob("*.mp4"), *b.glob("executions/*.mp4")]:
            metadata = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=nb_frames,width,height", "-of", "json", str(video)], text=True))
            assert float(metadata["format"]["duration"]) > 40
            assert video.with_suffix(".gif").is_file()
            assert int(metadata["streams"][0]["nb_frames"]) > 100
        sources.add((sha(a / "source/own_mapping.py"), sha(a / "source/own_live.py")))
    assert len(sources) == 1, "Algorithm changed between scenes"
    exclusions = []
    for run_id, reason in [
        ("20261016-020423-mapping-own-motion-6e5d5d", "Capture preflight produced no frames; formal motion experiment never started"),
        ("20261016-020910-mapping-own-corridor-07e361", "User stopped Computer Use with Escape; corridor capture aborted and excluded"),
    ]:
        excluded = ROOT / "results/runs/presentation" / run_id
        exclusions.append({"run": str(excluded), "reason": reason,
            "recording_started": (excluded / "recording.started").exists(),
            "session_sha256": sha(excluded / "session.json"),
            "scope": "Excluded attempt, not completed experimental evidence"})
    (suite / "excluded-attempts.json").write_text(json.dumps(exclusions, indent=2) + "\n")
    (suite / "protocol-source").mkdir()
    for name in ("demo/record-own-hypotheses.ps1", "demo/presentation.ps1", "demo/record-methods.ps1", "src/scripts/presentation/run_live.sh", "src/scripts/presentation/prepare_session.py", "src/scripts/presentation/score_direction_time_grid.py", "src/scripts/presentation/own_research_home.py"):
        shutil.copyfile(ROOT / name, suite / "protocol-source" / Path(name).name)
    earlier = ROOT / ".cache/own-recorded-run_live.sh"
    shutil.copyfile(earlier, suite / "protocol-source/run_live-before-caption-heartbeat.sh")
    launcher_hashes = {sha(earlier), sha(ROOT / "src/scripts/presentation/run_live.sh")}
    for scene in ("static", "dynamic", "motion", "corridor"):
        assets = json.loads((suite / (scene + "-A") / "session.json").read_text())["assets"]
        assert next(value for key, value in assets.items() if key.endswith("/run_live.sh")) in launcher_hashes
    record = {"schema_version": 1, "kind": "project_written_hypothesis_experiments", "status": "executed", "exit_code": 0,
        "scope": "Four new A sessions and four separate B sessions; own temporal cleaning, wheel-odometry deskew and weak-axis retention; native AMCL is common evaluation localizer, not the intervention. One exploratory trial each, no claim that every hypothesis is supported. Physical mirror behavior not reproduced.",
        "source_base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=ROOT).strip(),
        "records": children, "frozen_map_bindings": bindings,
        "algorithm_source_sha256": list(sources)[0],
        "artifacts": {p.relative_to(suite).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size, "availability": "portable"} for p in sorted(suite.rglob("*")) if p.is_file()}}
    (suite / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    path = ROOT / "docs/figures/slots.json"
    slots = json.loads(path.read_text(encoding="utf-8"))
    for gif in sorted(suite.rglob("*.gif")):
        relative = gif.relative_to(suite).as_posix()
        slots["slots"].append({"id": "own-20261016-" + relative.replace("/", "-").replace(".gif", ""), "status": "published", "path": gif.relative_to(ROOT).as_posix(),
            "caption": {"zh": relative + " · 自写方法实录", "en": relative + " · own-method recording"},
            "source_records": [(suite / "record.json").relative_to(ROOT).as_posix()], "source_artifact": relative})
    path.write_text(json.dumps(slots, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Sealed {len(children)} native records, {len(bindings)} frozen-map bindings")


if __name__ == "__main__":
    seal((ROOT / sys.argv[1]).resolve())
