"""Re-run saved native scan+odometry inputs to export an author multi-session prior.

No truth is read. Run in Ubuntu20.04 with the author worker already built.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("run", type=Path)
    args = p.parse_args()
    output = args.run / "native-prior-replay"
    output.mkdir(exist_ok=False)
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/root/srrg-reproduction-ws/devel/lib:/opt/ros/noetic/lib"
    source = args.run / "srrg-inputs.jsonl"
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    wire = output / "inputs.txt"
    with wire.open("w") as f:
        for row in rows:
            x, y, _ = row["laser_tf_xyz"]
            qx, qy, qz, qw = row["laser_tf_xyzw"]
            a = math.atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz))
            r = row["ranges"]
            inc = row["angle_increment"]
            amin = row["angle_min"]
            data = [
                row["stamp_s"],
                *row["wheel_odom"],
                x,
                y,
                a,
                amin,
                amin + (len(r) - 1) * inc,
                inc,
                0.1,
                12.0,
                len(r),
                *r,
            ]
            f.write("S " + " ".join(map(str, data)) + "\n")
        f.write("F\n")
    with (
        wire.open("rb") as i,
        (output / "outputs.jsonl").open("wb") as o,
        (output / "author.log").open("wb") as e,
    ):
        subprocess.run(
            ["/root/srrg-reproduction-ws/srrg_worker"],
            stdin=i,
            stdout=o,
            stderr=e,
            env=env,
            cwd=output,
            check=True,
        )
    assert (output / "prior.g2o").is_file() and list(output.glob("prior-cloud-*.dat"))
    record = {
        "kind": "native_static_prior_replay",
        "source_scan_odom_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "truth_used": False,
        "frames": len(rows),
        "scope": "Saved 2D scan and wheel odometry re-inference; not a new Gazebo run",
        "files": {
            q.name: hashlib.sha256(q.read_bytes()).hexdigest() for q in output.iterdir() if q.is_file()
        },
    }
    (output / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(output)
