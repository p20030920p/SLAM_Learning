"""Verify local full-session recordings and export small portable evidence only."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from slam_learning.core.provenance import digest, utc_now, write_json
from slam_learning.runtime.runner import export_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recordings", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    accepted = {}
    for path in sorted(args.recordings.glob("final-*/recording.json")):
        data = json.loads(path.read_text())
        command = data["command"]["command"]
        method = (
            command[command.index("--method") + 1]
            if "--method" in command
            else next(
                name
                for name in ("conceptgraphs", "hovsg")
                if any(Path(p).name == f"run_{name}.py" for p in command)
            )
        )
        if data["command_exit_code"] != 0 or not data["full_video_decoded"]:
            raise ValueError("Rejected command/video: " + str(path))
        for name, info in data["artifacts"].items():
            if digest(path.parent / name) != info["sha256"]:
                raise ValueError("Recording artifact changed: " + name)
        accepted[method] = (path, data)
    if set(accepted) != {"dufomap", "beautymap", "conceptgraphs", "hovsg"}:
        raise ValueError("Four accepted final method recordings required")
    args.output.mkdir(parents=True, exist_ok=False)
    summaries = []
    lines = [
        "# 完整复现录制 / Full reproduction sessions",
        "",
        "正常速度、完整命令执行；含终端日志、时间与退出码。不是算法 FPS 或实时三维导航录屏。",
        "",
        "| 方法 | 时长（秒） | 本地视频 | 日志 |",
        "| --- | ---: | --- | --- |",
    ]
    for method in ("dufomap", "beautymap", "conceptgraphs", "hovsg"):
        path, data = accepted[method]
        target = args.output / "sessions" / method
        target.mkdir(parents=True)
        for name in data["artifacts"]:
            shutil.copy2(path.parent / name, target / name)
        shutil.copy2(path, target / "recording.json")
        transcript = (path.parent / "terminal.raw").read_text(errors="replace")
        candidates = re.findall(
            r"(?:record:|->|record:)\s*(/home/[^\s;]+/results/runs/[^\s;]+/record.json)", transcript
        )
        if not candidates:
            raise ValueError("No completed native run record in session " + method)
        native = Path(candidates[-1])
        native_data = json.loads(native.read_text())
        if native_data["status"] != "executed":
            raise ValueError("Native command did not execute successfully")
        export_record(native, args.output / "native" / method)
        item = {
            "method": method,
            "folder": path.parent.name,
            "duration_seconds": data["duration_seconds"],
            "command_elapsed_seconds": data["command_elapsed_seconds"],
            "video_sha256": data["artifacts"]["full-session.mp4"]["sha256"],
            "native_record_sha256": digest(native),
            "native_run_id": native.parent.name,
            "monotonic_capture": data.get("monotonic_capture"),
            "scope": "Live private terminal capture from command startup through exit; not online map rendering",
        }
        summaries.append(item)
        folder = path.parent.name
        lines.append(
            f'| {method} | {data["duration_seconds"]:.1f} | [MP4]({folder}/full-session.mp4) | [终端]({folder}/terminal.raw) |'
        )
    lines.extend(
        [
            "",
            "只使用以上通过检查的 final 版本。初次连接失败、日志范围错误、时钟检查未通过的尝试留在本地，未列为交付。",
            "",
        ]
    )
    (args.recordings / "VIDEO_INDEX.md").write_text("\n".join(lines), encoding="utf-8")
    write_json(args.recordings / "video-index.json", {"sessions": summaries})
    write_json(
        args.output / "summary.json",
        {
            "sessions": summaries,
            "videos_stay_local": True,
            "local_windows_directory": "D:/workspace/be2/SLAM_Recordings/2026-10-08",
            "scope": "Four complete measured author-core reruns, terminal capture; large MP4 files are not published to Git",
        },
    )
    record = {
        "schema_version": 1,
        "kind": "full_terminal_recordings",
        "status": "executed",
        "finished_at": utc_now(),
        "exit_code": 0,
        "script_sha256": digest(Path(__file__)),
        "summary": {"sessions": summaries},
        "artifacts": {},
    }
    for path in args.output.rglob("*"):
        if not path.is_file() or path == args.output / "record.json":
            continue
        record["artifacts"][path.relative_to(args.output).as_posix()] = {
            "sha256": digest(path),
            "bytes": path.stat().st_size,
            "availability": "local_only" if path.suffix == ".mp4" else "portable",
        }
    write_json(args.output / "record.json", record)
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
