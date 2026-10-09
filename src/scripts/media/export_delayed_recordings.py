"""Publish small audit artifacts while retaining full experiment videos locally."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.core.provenance import digest, utc_now, write_json
from slam_learning.runtime.runner import verify_record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("recordings", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/reference/delayed-recordings"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    bindings = [("frontend", "delayed-room1-frontend-v1", "delayed-pose/inputs/frontend-record.json"),
                ("primary", "delayed-room1-suite-attempt2", "delayed-pose/inputs/record.json"),
                ("followup", "delayed-room1-support-followup-v1", "delayed-support-control/inputs/record.json")]
    for kind in ("delayed-pose", "delayed-support-control"):
        if verify_record(root / "results/reference" / kind / "record.json"):
            raise ValueError("Scientific evidence changed")
    args.output.mkdir(parents=True, exist_ok=False)
    entries = []
    artifacts = {}
    for label, folder, bound in bindings:
        source = args.recordings / folder
        record = json.loads((source / "recording.json").read_text())
        if record["status"] != "executed" or record["command_exit_code"] != 0 or not record["full_video_decoded"]:
            raise ValueError(f"Incomplete recording: {source}")
        for name, info in record["artifacts"].items():
            if not (source / name).is_file() or digest(source / name) != info["sha256"]:
                raise ValueError(f"Changed local recording artifact: {source / name}")
        dest = args.output / label
        dest.mkdir()
        for name in ("recording.json", "command.json", "exit.json", "terminal.raw", "terminal.time",
                     "review-start.png", "review-middle.png", "review-end.png"):
            shutil.copy2(source / name, dest / name)
        scientific = root / "results/reference" / bound
        entry = {"id": label, "folder": folder, "duration_seconds": record["duration_seconds"],
                 "command_elapsed_seconds": record["command_elapsed_seconds"],
                 "held_frames": record["monotonic_capture"]["held_frames"],
                 "scientific_record": bound, "scientific_record_sha256": digest(scientific),
                 "video_sha256": digest(source / "full-session.mp4"),
                 "scope": "Complete real-time private terminal execution; no live 3D inference"}
        entries.append(entry)
        artifacts[f"{label}/full-session.mp4"] = {**record["artifacts"]["full-session.mp4"],
                                                  "availability": "local_only"}
    shutil.copy2(Path(__file__), args.output / "executed-export.py")
    shutil.copy2(root / "src/scripts/media/record_session.py", args.output / "record-session-source.py")
    for entry in entries:
        rec = json.loads((args.output / entry["id"] / "recording.json").read_text())
        if rec["recorder_script_sha256"] != digest(args.output / "record-session-source.py"):
            raise ValueError("Recorder source differs from actual executed version")
    write_json(args.output / "summary.json", entries)
    for path in args.output.rglob("*"):
        if path.is_file():
            artifacts[path.relative_to(args.output).as_posix()] = {
                "sha256": digest(path), "bytes": path.stat().st_size, "availability": "portable"}
    write_json(args.output / "record.json", {"schema_version": 1, "kind": "delayed_experiment_recordings",
               "status": "executed", "exit_code": 0, "finished_at": utc_now(), "recordings": entries,
               "scope": "Full videos stay local; portable hashes, logs and review frames only",
               "artifacts": artifacts})
    lines = ["# 迟到位姿修正实验完整录像", "", "均为实际运行的实时终端录像，未经加速或剪辑；不是实时三维推理。", "",
             "| 阶段 | 时长（秒） | 命令耗时（秒） | 画面保持次数 | 本地视频 |", "| --- | ---: | ---: | ---: | --- |"]
    for entry in entries:
        video = (args.recordings / entry["folder"] / "full-session.mp4").resolve().as_posix()
        lines.append(f"| {entry['id']} | {entry['duration_seconds']} | {entry['command_elapsed_seconds']:.3f} | "
                     f"{entry['held_frames']} | [播放]({video}) |")
    lines.extend(["", "每段同目录含 command.json、exit.json、recording.json、终端日志及首／中／尾检查图。",
                  "完整视频已解码检查；MP4 SHA-256：", ""])
    lines.extend(f"- {e['id']}: `{e['video_sha256']}`" for e in entries)
    (args.recordings / "DELAYED_VIDEO_INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(entries, indent=2))


if __name__ == "__main__":
    main()
