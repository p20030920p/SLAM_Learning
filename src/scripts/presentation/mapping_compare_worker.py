"""Run author cleaners on immutable live snapshots, in their Ubuntu-22.04 runtime."""

import argparse
import json
import os
import subprocess
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("methods")
    args = parser.parse_args()
    environment = {**os.environ, "OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "2", "MKL_NUM_THREADS": "2"}
    seen = None
    deadline = time.monotonic() + 240
    while not (args.run / "session-stopped.json").exists() and not (args.run / "STOP").exists():
        marker = args.run / "compare-input.json"
        if not marker.exists():
            if time.monotonic() > deadline:
                raise TimeoutError("No live mapping snapshot arrived")
            time.sleep(1)
            continue
        item = json.loads(marker.read_text())
        if item["version"] == seen:
            time.sleep(1)
            continue
        source = Path(item["path"])
        output = args.run / f"compare-result-{item['version']:04d}"
        with (args.run / "logs" / f"compare-{item['version']:04d}.log").open("w") as log:
            subprocess.run(
                [
                    "/home/qzl/projects/SLAM_Author_Originals/envs/lidar/bin/python",
                    "-u",
                    str(Path(__file__).with_name("build_maps.py")),
                    "--recording",
                    str(source),
                    "--output",
                    str(output),
                    "--max-scans",
                    "60",
                    "--methods",
                    *args.methods.split(","),
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
                env=environment,
            )
        payload = {**item, "output": str(output), "methods": args.methods.split(",")}
        temporary = args.run / "compare-result.tmp"
        temporary.write_text(json.dumps(payload, indent=2) + "\n")
        temporary.replace(args.run / "compare-result.json")
        seen = item["version"]


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        import sys

        run = Path(sys.argv[1])
        (run / "compare-failed.json").write_text(json.dumps({"error": str(error)}))
        raise
