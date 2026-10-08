"""Record a real Linux terminal session from before command start through exit.

Uses a private Xvfb screen, never the user's desktop. No time compression.
The MP4, PTY transcript, timing, exit status and hashes remain local by default.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shlex
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def child(directory):
    spec = json.loads((directory / "command.json").read_text())
    print("SLAM Learning | FULL TERMINAL SESSION | normal elapsed time", flush=True)
    while not (directory / "GO").exists():
        time.sleep(0.1)
    start = time.monotonic()
    print(f"Started UTC: {now()}\nWorking directory: {spec['cwd']}", flush=True)
    print("$ " + shlex.join(spec["command"]), flush=True)
    stop = threading.Event()

    def monitor():
        positions = {}
        last_clock = 0
        watch = Path(spec["cwd"]) / "results/runs"
        while not stop.wait(1):
            elapsed = time.monotonic() - start
            if elapsed - last_clock >= 15:
                print(f"[elapsed {elapsed:.0f}s | UTC {now()}]", flush=True)
                last_clock = elapsed
            for log in watch.glob("**/*.log"):
                relative_parts = log.relative_to(watch).parts
                prefix = spec.get("watch_prefix")
                if not prefix or not relative_parts[0].startswith(prefix):
                    continue
                if log.stat().st_mtime < spec["prepared_epoch"] or "author-code" in log.parts:
                    continue
                offset = positions.get(log, 0)
                with log.open("rb") as stream:
                    stream.seek(offset)
                    data = stream.read()
                    positions[log] = stream.tell()
                if data:
                    print(f"\n[live log: {log.relative_to(watch)}]", flush=True)
                    print(data.decode("utf-8", errors="replace"), end="", flush=True)

    watcher = threading.Thread(target=monitor, daemon=True)
    watcher.start()
    process = subprocess.Popen(spec["command"], cwd=spec["cwd"], env=dict(os.environ, PYTHONUNBUFFERED="1"))
    rc = process.wait()
    stop.set()
    watcher.join(timeout=3)
    result = {
        "command_exit_code": rc,
        "finished_at": now(),
        "command_elapsed_seconds": time.monotonic() - start,
    }
    (directory / "exit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        f"\nCommand finished: exit {rc}; elapsed {result['command_elapsed_seconds']:.2f}s; UTC {now()}",
        flush=True,
    )
    time.sleep(3)  # Retain the exit result visibly at the end of the real recording.
    (directory / "DONE").write_text(now())
    return rc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--fps", type=int, default=5)
    parser.add_argument("--child", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.child:
        return child(args.child)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not args.output or not command or not 1 <= args.fps <= 30:
        parser.error("--output and a command after -- are required; fps must be 1..30")
    directory = args.output.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    spec = {
        "command": command,
        "cwd": str(args.cwd.resolve()),
        "prepared_at": now(),
        "prepared_epoch": time.time(),
        "fps": args.fps,
        "size": [1280, 800],
    }
    spec["recorder_script_sha256"] = sha(__file__)
    spec["watch_prefix"] = None
    if "--method" in command:
        spec["watch_prefix"] = command[command.index("--method") + 1] + "-"
    for method in ("conceptgraphs", "hovsg"):
        if any(Path(part).name == f"run_{method}.py" for part in command):
            spec["watch_prefix"] = method + "-"
    (directory / "command.json").write_text(json.dumps(spec, indent=2) + "\n")
    recorder = terminal = server = None
    capture_stop = threading.Event()
    capture_errors = []
    capture_stats = {"frames": 0, "held_frames": 0}
    capture_thread = None
    try:
        # WSLg's /tmp/.X11-unix is a read-only mount. Use a separate authenticated
        # X server over TCP, without modifying WSLg or the user's display.
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        display_number = port - 6000
        if display_number < 1:
            raise RuntimeError("Unable to reserve an X display port")
        display = f"127.0.0.1:{display_number}"
        authority = directory / "private.Xauthority"
        authority.touch(mode=0o600)
        subprocess.run(
            ["xauth", "-f", str(authority), "add", display, "MIT-MAGIC-COOKIE-1", secrets.token_hex(16)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        server_log = (directory / "xvfb.log").open("w")
        server = subprocess.Popen(
            [
                "Xvfb",
                f":{display_number}",
                "-screen",
                "0",
                "1280x800x24",
                "-nolisten",
                "unix",
                "-listen",
                "tcp",
                "-auth",
                str(authority),
            ],
            stdout=server_log,
            stderr=server_log,
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            with socket.socket() as check:
                if check.connect_ex(("127.0.0.1", port)) == 0:
                    break
            if server.poll() is not None:
                raise RuntimeError("Private X server exited; inspect xvfb.log")
            time.sleep(0.1)
        else:
            raise RuntimeError("Private X screen did not become ready")
        env = dict(os.environ, DISPLAY=display, XAUTHORITY=str(authority))
        child_command = shlex.join([sys.executable, str(Path(__file__).resolve()), "--child", str(directory)])
        terminal = subprocess.Popen(
            [
                "xterm",
                "-hold",
                "-geometry",
                "158x48+0+0",
                "-fa",
                "DejaVu Sans Mono",
                "-fs",
                "10",
                "-bg",
                "#111827",
                "-fg",
                "#e5e7eb",
                "-title",
                "SLAM full session",
                "-e",
                "script",
                "-q",
                "-f",
                "-e",
                "--log-out",
                str(directory / "terminal.raw"),
                "--log-timing",
                str(directory / "terminal.time"),
                "-c",
                child_command,
            ],
            env=env,
        )
        ffmpeg_log = (directory / "ffmpeg.log").open("w")
        recorder = subprocess.Popen(
            [
                "ffmpeg",
                "-nostdin",
                "-y",
                "-f",
                "rawvideo",
                "-pixel_format",
                "rgb24",
                "-framerate",
                str(args.fps),
                "-video_size",
                "1280x800",
                "-i",
                "pipe:0",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-tune",
                "zerolatency",
                "-crf",
                "26",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-progress",
                str(directory / "encoder-progress.txt"),
                str(directory / "full-session.mp4"),
            ],
            stdout=ffmpeg_log,
            stderr=ffmpeg_log,
            env=env,
            stdin=subprocess.PIPE,
        )
        os.environ["XAUTHORITY"] = str(authority)

        def capture():
            from PIL import ImageGrab

            started = time.monotonic()
            last = None
            try:
                while not capture_stop.is_set():
                    # WSL wall time may jump; MP4 timing follows the monotonic clock.
                    # If capture is late, hold the last real frame instead of speeding up.
                    expected = int((time.monotonic() - started) * args.fps)
                    while last is not None and capture_stats["frames"] < expected:
                        recorder.stdin.write(last)
                        capture_stats["frames"] += 1
                        capture_stats["held_frames"] += 1
                    frame = ImageGrab.grab(xdisplay=display).convert("RGB")
                    if frame.size != (1280, 800):
                        raise RuntimeError("Private X capture size changed")
                    last = frame.tobytes()
                    recorder.stdin.write(last)
                    capture_stats["frames"] += 1
                    target = started + capture_stats["frames"] / args.fps
                    capture_stop.wait(max(0, target - time.monotonic()))
            except Exception as error:
                capture_errors.append(str(error))
            finally:
                capture_stats["elapsed_seconds"] = time.monotonic() - started
                recorder.stdin.close()

        capture_thread = threading.Thread(target=capture, daemon=True)
        capture_thread.start()
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            progress = directory / "encoder-progress.txt"
            if progress.exists() and "frame=" in progress.read_text():
                break
            if recorder.poll() is not None or terminal.poll() is not None:
                raise RuntimeError("Recorder or terminal failed before command start")
            if capture_errors:
                raise RuntimeError(str(capture_errors))
            time.sleep(0.1)
        else:
            raise RuntimeError("No encoded frame before command start")
        (directory / "GO").write_text(now())
        print(f"Recording full session locally: {directory}", flush=True)
        while not (directory / "DONE").exists():
            if recorder.poll() is not None:
                terminal.terminate()
                raise RuntimeError("Video encoder stopped during command; session is incomplete")
            if terminal.poll() is not None:
                raise RuntimeError("Terminal closed before the command completion marker")
            if capture_errors:
                raise RuntimeError(str(capture_errors))
            time.sleep(0.5)
        capture_stop.set()
        capture_thread.join(timeout=20)
        if capture_thread.is_alive() or capture_errors:
            raise RuntimeError(f"Capture did not finish cleanly: {capture_errors}")
        recorder.wait(timeout=60)
        result = json.loads((directory / "exit.json").read_text())
        video = directory / "full-session.mp4"
        probe = json.loads(
            subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)],
                text=True,
            )
        )
        duration = float(probe["format"]["duration"])
        if duration < result["command_elapsed_seconds"] + 1:
            raise RuntimeError("Recording duration does not cover the command")
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"], check=True)
        for label, moment in (("start", 1), ("middle", duration / 2), ("end", max(0, duration - 1))):
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-ss",
                    str(moment),
                    "-i",
                    str(video),
                    "-frames:v",
                    "1",
                    str(directory / f"review-{label}.png"),
                ],
                check=True,
            )
            from PIL import Image, ImageStat

            with Image.open(directory / f"review-{label}.png") as review_image:
                if max(ImageStat.Stat(review_image).stddev) < 3:
                    raise RuntimeError(f"Nearly blank {label} review frame; recording not accepted")
        result.update(
            kind="full_terminal_recording",
            status="executed",
            command=spec,
            duration_seconds=duration,
            monotonic_capture=capture_stats,
            scope="Actual private X terminal captured live; no speedup, cuts or desktop capture",
            recorder_script_sha256=spec["recorder_script_sha256"],
            full_video_decoded=True,
            artifacts={
                p.name: {"sha256": sha(p), "bytes": p.stat().st_size}
                for p in directory.iterdir()
                if p.is_file() and p.name not in ("recording.json", "private.Xauthority")
            },
        )
        (directory / "recording.json").write_text(json.dumps(result, indent=2) + "\n")
        print(
            json.dumps(
                {k: result[k] for k in ("command_exit_code", "command_elapsed_seconds", "duration_seconds")}
            )
        )
        return result["command_exit_code"]
    finally:
        capture_stop.set()
        for process in (recorder, terminal, server):
            if process is not None and process.poll() is None:
                process.terminate()
                process.wait(timeout=15)


if __name__ == "__main__":
    raise SystemExit(main())
