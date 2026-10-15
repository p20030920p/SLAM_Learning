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
    ap.add_argument("--display-before", default="",
                    help="Xvfb pid/uptime before the capture, recorded verbatim")
    ap.add_argument("--display-after", default="",
                    help="Xvfb pid/uptime after the capture")
    ap.add_argument("--map-static", action="store_true",
                    help="the level localises against a SAVED map, so the map is "
                         "supposed NOT to grow; pass then requires robot_moved "
                         "instead of right_map_grew")
    ap.add_argument("--localization-evidence", default="",
                    help="raw map->base_footprint samples proving the robot's pose "
                         "in the map frame changes; recorded verbatim")
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

    # What actually grows is the *mapped* area.  "Mapped" was the first attempt at
    # measuring it, but it counts the viewer's dark background as occupied (the
    # background is 18,22,28 and "occupied" is anything under 45), so on a take where
    # the grid is small the whole half reads as 99% mapped and the number barely
    # moves.  Free space is the unambiguous signal instead: it is near-white
    # (238,238,234) and nothing else in this viewer is, so free-area growth cannot be
    # confused with either the background or the unknown grey.
    def mapped_frac(arr: np.ndarray) -> float:
        mx, mn = arr.max(axis=2), arr.min(axis=2)
        free = mn > 200
        occupied = mx < 45
        return float((free | occupied).mean())

    def free_frac(arr: np.ndarray) -> float:
        return float((arr.min(axis=2) > 200).mean())

    m_a, m_b = mapped_frac(ra), mapped_frac(rb)
    f_a, f_b = free_frac(ra), free_frac(rb)
    free_growth = f_b - f_a

    # Did the robot actually go anywhere?  The viewer draws the driven trail in light
    # blue, so the trail's bounding box and length are a direct read of how far the
    # robot travelled.  This check exists because a take once passed every other gate
    # while showing a completely stationary robot: slam_toolbox republishes its grid
    # unconditionally at map_update_interval, so rising /map counters prove nothing.
    def trail(arr: np.ndarray) -> dict:
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        mask = (b > 170) & (g > 150) & (r < 160) & (b > r + 60)
        ys, xs = np.nonzero(mask)
        if xs.size < 20:
            return {"pixels": int(xs.size), "span_x": 0, "span_y": 0}
        return {
            "pixels": int(xs.size),
            "span_x": int(xs.max() - xs.min()),
            "span_y": int(ys.max() - ys.min()),
        }

    t_a, t_b = trail(ra), trail(rb)
    # How much further did the robot get?  Use the trail's *pixel count*, not its
    # bounding box.  A lawnmower patrol reaches its full extent early and then fills
    # that area in, so the bounding box stops changing while the robot is still
    # driving perfectly well -- a take that covered the whole arena scored span
    # growth 0 and was wrongly failed by the first version of this check.
    # Accumulated trail length keeps rising for as long as the robot moves.
    trail_growth = t_b["pixels"] - t_a["pixels"]
    moved = trail_growth >= 100
    report["robot_motion"] = {
        "trail_at_t_a": t_a,
        "trail_at_t_b": t_b,
        "trail_pixel_growth": int(trail_growth),
        "moved": bool(moved),
        "note": "trail pixel count, not bounding box: a patrol fills its area in "
                "instead of extending, so span saturates while the robot still moves",
    }

    grew = free_growth > 0.001 or changed > 0.001
    report["right_half_change"] = {
        "t_a_s": round(a * dur, 3),
        "t_b_s": round(b * dur, 3),
        "changed_frac": round(changed, 4),
        "mean_abs_diff": round(float(diff.mean()), 2),
        "free_frac_t_a": round(f_a, 4),
        "free_frac_t_b": round(f_b, 4),
        "free_growth": round(free_growth, 4),
        "mapped_frac_t_a": round(m_a, 4),
        "mapped_frac_t_b": round(m_b, 4),
        "mapped_growth": round(m_b - m_a, 4),
    }

    left_ok = all(report["frames"][t]["left"]["std"] > 5.0
                  and report["frames"][t]["left"]["nonblack_frac"] > 0.5 for t in tags)
    right_ok = all(report["frames"][t]["right"]["std"] > 3.0
                   and report["frames"][t]["right"]["nonblack_frac"] > 0.05 for t in tags)
    grow_ok = bool(grew)
    # Only a *different pid*, or a display whose uptime went backwards, means the
    # display was restarted.  Comparing the raw strings would always differ, since
    # uptime grows during a normal recording.
    def _field(blob: str, key: str) -> str:
        for token in blob.split():
            if token.startswith(key + "="):
                return token[len(key) + 1:]
        return ""

    display_changed = bool(
        args.display_before and args.display_after
        and (_field(args.display_before, "pid") != _field(args.display_after, "pid")
             or float(_field(args.display_after, "uptime_s") or 0)
             < float(_field(args.display_before, "uptime_s") or 0))
    )
    report["display"] = {
        "before": args.display_before,
        "after": args.display_after,
        "changed_during_capture": display_changed,
    }
    report["localization_evidence"] = args.localization_evidence
    report["map_expected_static"] = bool(args.map_static)
    report["verdict"] = {
        "left_rendered": left_ok,
        "right_drawn": right_ok,
        "right_map_grew": grow_ok,
        "robot_moved": bool(moved),
        "display_stable": not display_changed,
        # Which growth criterion applies depends on what the level is supposed to do:
        #
        #  * mapping levels (S1, S2, S4) build a map, so the mapped area must grow;
        #  * a localization level (S3) is handed a SAVED map and must NOT grow it --
        #    demanding growth there is simply the wrong test, and it is what wrongly
        #    failed the first two S3 takes.  What has to be true instead is that the
        #    robot moves and that its pose in the map frame tracks, which is checked
        #    by robot_moved plus the recorded map->base_footprint samples.
        #
        # Either way a take of a parked robot is not evidence of anything, however
        # live the map stream looks, so motion is required in both modes.
        "growth_criterion": "map_static_ok" if args.map_static else "map_grew",
        "pass": bool(left_ok and right_ok and moved
                     and (args.map_static or grow_ok)),
    }

    (outdir / f"{args.stem}_check.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print()
    print(f"left_rendered={left_ok}  right_drawn={right_ok}  right_map_grew={grow_ok}  "
          f"robot_moved={moved}")
    print(f"  criterion={report['verdict']['growth_criterion']}"
          f"{'  (saved map: static is correct)' if args.map_static else ''}")
    print(f"  changed_frac={changed:.4f}  mapped {m_a:.4f}->{m_b:.4f}  "
          f"trail {t_a['pixels']} -> {t_b['pixels']} px "
          f"({trail_growth:+d})")
    print(f"  PASS={report['verdict']['pass']}")
    return 0 if report["verdict"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
