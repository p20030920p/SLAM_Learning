#!/usr/bin/env python3
"""Check the invariants that make the generated sessions valid ltremovert input.

Three things have to hold or the run is meaningless rather than wrong-looking:

  1. every session directory's scan count equals its pose file's line count
     (`Session.cpp:117` asserts it, and the Release build compiles the assert out);
  2. `000000.pcd` goes with pose line 1 — the directory listing is sorted
     (`Session.cpp:87-93`) and the pose file is read in order (`:104-114`);
  3. the scans are in the **sensor** frame: applying a scan's pose must reproduce
     the benchmark's world-frame cloud it came from, and the sensor must sit at
     the scan's own origin (`precleaningKeyframes(2.5)` at `Session.cpp:506-533`
     carves a ball there, so a world-frame scan would be carved at the origin of
     the *world*, i.e. 20 m away from the sensor).

The round trip is checked against the source clouds, so it also proves the
renumbering (frame N of a session -> its recorded source frame) is right.

Usage:
    python3 work/verify_sessions.py --sessions data/raw/kitti00_two_sessions \
        --bench-seq ../01_dynamicmap_benchmark/data/raw/00
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

import numpy as np

MARK = b"DATA binary\n"


def read_pcd(path: str) -> np.ndarray:
    with open(path, "rb") as fh:
        raw = fh.read()
    i = raw.find(MARK)
    if i < 0:
        raise ValueError(f"{path}: not a binary PCD")
    header = raw[:i].decode("ascii", errors="replace")
    n = int(re.search(r"POINTS (\d+)", header).group(1))
    fields = re.search(r"FIELDS (.*)", header).group(1).split()
    return np.frombuffer(raw[i + len(MARK): i + len(MARK) + n * 4 * len(fields)],
                         dtype=np.float32).reshape(-1, len(fields))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sessions", required=True)
    ap.add_argument("--bench-seq", required=True)
    ap.add_argument("--tol", type=float, default=1e-3,
                    help="max round-trip error, metres (float32 storage ~4e-6)")
    args = ap.parse_args()

    meta = json.load(open(os.path.join(args.sessions, "sessions.json")))
    src = os.path.join(args.bench_seq, "pcd")
    ok = True

    for session in ("central", "query"):
        sdir = os.path.join(args.sessions, session)
        names = sorted(f for f in os.listdir(os.path.join(sdir, "Scans")) if f.endswith(".pcd"))
        poses = np.loadtxt(os.path.join(sdir, "poses.txt"))
        counts_ok = len(names) == len(poses)
        ok &= counts_ok
        print(f"[{session}] {len(names)} scans vs {len(poses)} pose rows "
              f"-> {'ok' if counts_ok else 'MISMATCH'}")
        if not counts_ok:
            continue

        # first, middle and last frame of the session
        worst, worst_name, mean_range = 0.0, "", 0.0
        for k in (0, len(names) // 2, len(names) - 1):
            loc = read_pcd(os.path.join(sdir, "Scans", names[k]))
            R, t = poses[k].reshape(3, 4)[:, :3], poses[k].reshape(3, 4)[:, 3]
            world = loc[:, :3].astype(np.float64) @ R.T + t
            ref_name = meta[session]["src_frames"][k]
            ref = read_pcd(os.path.join(src, ref_name))
            if len(ref) != len(loc):
                print(f"  frame {k}: {ref_name} has {len(ref)} points, scan has {len(loc)}")
                ok = False
                continue
            err = float(np.linalg.norm(world - ref[:, :3], axis=1).max())
            if err > worst:
                worst, worst_name = err, ref_name
            mean_range = float(np.linalg.norm(loc[:, :3], axis=1).mean())
            print(f"  frame {k:>3} = {ref_name}: round-trip max {err:.2e} m, "
                  f"mean |p| {mean_range:.2f} m")
        if worst > args.tol:
            print(f"  [{session}] round-trip error {worst:.2e} m > {args.tol} on {worst_name}")
            ok = False

    print("\nVERIFY " + ("OK" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
