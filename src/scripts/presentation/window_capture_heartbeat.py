"""Keep real native window captions repainting for event-driven WGC capture.

This only updates X11 window titles; no rendered sensor/map pixels or estimator
inputs are replaced. A static capture source must not stall the other two.
"""
import json
import subprocess
import sys
import time
from pathlib import Path


def main():
    run = Path(sys.argv[1])
    titles = {}
    started = time.monotonic()
    with (run / "window-capture-heartbeat.jsonl").open("w") as log:
        while not (run / "session-stopped.json").exists():
            result = subprocess.run(["xdotool", "search", "--name", "Gazebo Sim|SLAM LIVE - probe |SLAM LIVE - RViz2 - mapping-srrg-"], text=True, capture_output=True, check=False)
            for identity in result.stdout.splitlines():
                name = subprocess.run(["xdotool", "getwindowname", identity], text=True, capture_output=True, check=False)
                title = name.stdout.strip()
                if title.startswith(("Gazebo Sim", "SLAM LIVE - probe ", "SLAM LIVE - RViz2 - mapping-srrg-")):
                    titles.setdefault(identity, title.split(" | capture clock")[0])
            elapsed = int(time.monotonic() - started)
            for identity, title in titles.items():
                subprocess.run(["xdotool", "set_window", "--name", f"{title} | capture clock {elapsed}s", identity], capture_output=True, check=False)
            log.write(json.dumps({"wall_elapsed_s": elapsed, "native_windows": titles}) + "\n")
            log.flush()
            time.sleep(.5)


if __name__ == "__main__":
    main()
