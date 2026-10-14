"""Package a real RViz map-result review without calling it an inference run."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

from package_session import gif, probe
from slam_learning.core.provenance import digest
from slam_learning.runtime.runner import verify_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    audit = root / "results/reference/robot-3d-map-audit/record.json"
    state = json.loads((args.run / "ready.json").read_text())
    if state["audit_sha256"] != digest(audit) or verify_record(audit):
        raise ValueError("Displayed point decisions differ from the validated map audit")
    args.output.mkdir(parents=True, exist_ok=False)
    for part in [*args.run.glob("view-*.rviz"), *[args.run / name for name in
                 ("ready.json", "capture-filter.txt", "capture.log", "execution.mp4", "review.log", "renderer.txt")]]:
        shutil.copyfile(part, args.output / part.name)
    video = args.output / "execution.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"], check=True)
    timing = gif(video, args.output / "execution.gif")
    duration = float(probe(video)["format"]["duration"])
    for label, stamp in (("first", 2), ("mid", duration/2), ("last", duration-2)):
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(stamp), "-i", str(video), "-frames:v", "1", "-y",
                        str(args.output / ("frame-"+label+".png"))], check=True)
    record = {"schema_version": 1, "kind": "native_3d_map_result_review", "status": "executed", "exit_code": 0,
              "scope": "genuine three-window RViz recording of saved native map results; not live inference or full 3D SLAM",
              "source_audit": "../robot-3d-map-audit/record.json", "source_audit_sha256": digest(audit),
              "metrics": state["metrics"], "display_stride": state["display_stride"], "timing": timing,
              "source_run": str(args.run.resolve()),
              "artifacts": {p.relative_to(args.output).as_posix(): {"sha256": digest(p), "bytes": p.stat().st_size, "availability": "portable"}
                            for p in args.output.rglob("*") if p.is_file()}}
    (args.output / "record.json").write_text(json.dumps(record, indent=2)+"\n")
    print(json.dumps({"output": str(args.output), "duration_s": duration}))


if __name__ == "__main__":
    main()
