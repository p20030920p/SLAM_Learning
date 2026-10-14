"""Seal live author RViz/terminal recordings, with no saved-result movie as execution."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

from package_session import gif, probe, windows_path
from slam_learning.core.provenance import digest
from slam_learning.runtime.localization_evidence import trajectory_metrics
from slam_learning.runtime.runner import verify_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run, out = args.run, args.output
    native = json.loads((run / "execution.json").read_text(encoding="utf-8"))
    if native["status"] != "executed" or native["exit_code"] != 0:
        raise ValueError("Successful native execution required")
    if (out / "record.json").exists():
        existing = json.loads((out / "record.json").read_text(encoding="utf-8"))
        if existing["source_run"] != str(run.resolve()):
            raise ValueError("Existing package belongs to a different execution; choose a fresh output")
        issues = verify_record(out / "record.json")
        if not issues:
            print(f"Already verified: {out}", flush=True)
            return
        raise ValueError("Existing record needs explicit repair: "+str(issues))
    out.mkdir(parents=True, exist_ok=True)
    for name in ("execution.mp4", "execution.json", "terminal.log", "native-output.log", "capture-filter.txt",
                 "author-live.rviz", "author-rviz.log", "instrumentation.patch"):
        if (run / name).exists():
            shutil.copyfile(run / name, out / name)
    for source, name in ((run / "live/events.jsonl", "live-events.jsonl"), (run / "live-published.jsonl", "live-published.jsonl")):
        shutil.copyfile(source, out / name)
    method = native["method"]
    metrics = native.get("metrics", {})
    if method == "ir-mcl":
        estimate = run / "author-code/results/ipblab/loc_test/test1/IRMCL.txt"
        truth = Path("D:/workspace/be2/tmp/repro/ir-mcl/data/ipblab/loc_test/test1/seq_1_gt_pose.txt")
        metrics, samples = trajectory_metrics(estimate, truth, 20, .01)
        for source, name in ((estimate, "IRMCL.txt"), (truth, "seq_1_gt_pose.txt")):
            shutil.copyfile(source, out / name)
        metrics["scored_poses"] = samples
    else:
        folder = out / "native-run"
        folder.mkdir()
        record = json.loads((run / "native-run/record.json").read_text())
        shutil.copyfile(run / "native-run/record.json", folder / "record.json")
        for name, artifact in record["artifacts"].items():
            if artifact["availability"] == "portable":
                shutil.copyfile(run / "native-run" / name, folder / name)
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(out / "execution.mp4"), "-f", "null", "-"], check=True)
    timing = {"execution": gif(out / "execution.mp4", out / "execution.gif")}
    duration = float(probe(out / "execution.mp4")["format"]["duration"])
    for name, stamp in (("first", 2), ("mid", duration/2), ("last", max(0, duration-3))):
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(stamp), "-i", str(out / "execution.mp4"), "-frames:v", "1", "-y", str(out / f"frame-{name}.png")], check=True)
    for name, value in (("metrics.json", metrics), ("timing.json", timing)):
        (out / name).write_text(json.dumps(value, indent=2)+"\n", encoding="utf-8")
    record = {"schema_version": 1, "kind": "author_desktop_demo", "status": "executed", "exit_code": 0,
              "method": method, "command": native["command"], "scope": native["scope"], "metrics": metrics,
              "source_run": str(run.resolve()), "live_state": {"enabled": True,
              "scope": "Actual RViz+terminal capture during new author execution; read-only current state, display thinning; observer overhead included"},
              "timing": timing, "artifacts": {p.relative_to(out).as_posix(): {"sha256": digest(p), "bytes": p.stat().st_size, "availability": "portable"}
                                              for p in out.rglob("*") if p.is_file()}}
    # Physical inputs and generated full point clouds stay local, while their native hashes remain recorded.
    record["native_output_path"] = str(windows_path(str(run / "native-run/cleaned.pcd"))) if method != "ir-mcl" else "IRMCL.txt"
    (out / "record.json").write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    issues = verify_record(out / "record.json")
    if issues:
        raise ValueError(issues)
    print(json.dumps({"output": str(out), "metrics": metrics}), flush=True)


if __name__ == "__main__":
    main()
