#!/usr/bin/env python3
"""Check a split-screen recording: export first/mid/last frames and measure both halves.

The left half must not be black (the simulator really rendered something) and the
right half must not be black *and* must change between frames (the map is growing).
Statistics are printed so the README can quote measured numbers rather than claims.

Splits at x = 960 by default.  Frames are exported as:
  <outdir>/<stem>_frame-first.png / -mid.png / -last.png
and the two halves of each as <stem>_frame-<tag>_L.png / _R.png.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,nb_frames,duration",
         "-show_entries", "format=duration,size",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    info = json.loads(out)
    st = info["streams"][0]
    fmt = info.get("format", {})
    num, _, den = (st.get("avg_frame_rate") or "0/1").partition("/")
    fps = float(num) / float(den) if float(den or 0) else 0.0
    return {
        "width": st["width"],
        "height": st["height"],
        "fps": round(fps, 4),
        "nb_frames": int(st.get("nb_frames") or 0),
        "duration_s": round(float(fmt.get("duration") or st.get("duration") or 0.0), 3),
        "bytes": int(fmt.get("size") or path.stat().st_size),
    }


def grab(path: Path, t: float) -> Image.Image:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path),
         "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True,
    ).stdout
    meta = probe(path)
    return Image.frombytes("RGB", (meta["width"], meta["height"]), raw)


def stats(arr: np.ndarray) -> dict:
    lum = arr.max(axis=2)
    return {
        "mean": round(float(arr.mean()), 2),
        "std": round(float(arr.std()), 2),
        "nonblack_frac": round(float((lum > 16).mean()), 4),
        "distinct_rows": int(len(np.unique(arr.reshape(-1, 3), axis=0))),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--stem", required=True)
    ap.add_argument("--split", type=int, default=960)
    ap.add_argument("--grow-pair", default="0.2,0.8",
                    help="two normalised times to compare for right-half change")
    args = ap.parse_args()

    video = Path(args.video).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    meta = probe(video)
    dur = meta["duration_s"]

    tags = {"first": 0.02, "mid": 0.50, "last": 0.98}
    report: dict = {"video": str(video), "probe": meta, "frames": {}}
    halves: dict[str, np.ndarray] = {}

    for tag, frac in tags.items():
        t = max(0.0, min(dur - 1e-3, frac * dur))
        img = grab(video, t)
        arr = np.asarray(img)
        left = arr[:, : args.split]
        right = arr[:, args.split:]
        halves[tag] = right
        img.save(outdir / f"{args.stem}_frame-{tag}.png")
        Image.fromarray(left).save(outdir / f"{args.stem}_frame-{tag}_L.png")
        Image.fromarray(right).save(outdir / f"{args.stem}_frame-{tag}_R.png")
        report["frames"][tag] = {
            "t_s": round(t, 3),
            "left": stats(left),
            "right": stats(right),
        }

    a, b = (float(v) for v in args.grow_pair.split(","))
    ra = np.asarray(grab(video, max(0.0, a * dur)), dtype=np.float64)[:, args.split:]
    rb = np.asarray(grab(video, min(dur - 1e-3, b * dur)), dtype=np.float64)[:, args.split:]
    diff = np.abs(ra - rb).max(axis=2)
    changed = float((diff > 24).mean())
    report["right_half_change"] = {
        "t_a_s": round(a * dur, 3),
        "t_b_s": round(b * dur, 3),
        "changed_frac": round(changed, 4),
        "mean_abs_diff": round(float(diff.mean()), 2),
    }

    left_ok = all(report["frames"][t]["left"]["std"] > 5.0
                  and report["frames"][t]["left"]["nonblack_frac"] > 0.5 for t in tags)
    right_ok = all(report["frames"][t]["right"]["std"] > 3.0
                   and report["frames"][t]["right"]["nonblack_frac"] > 0.05 for t in tags)
    grow_ok = changed > 0.001
    report["verdict"] = {
        "left_rendered": left_ok,
        "right_drawn": right_ok,
        "right_map_grew": grow_ok,
        "pass": bool(left_ok and right_ok and grow_ok),
    }

    (outdir / f"{args.stem}_check.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print()
    print(f"left_rendered={left_ok}  right_drawn={right_ok}  right_map_grew={grow_ok} "
          f"(changed_frac={changed:.4f})  PASS={report['verdict']['pass']}")
    return 0 if report["verdict"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
