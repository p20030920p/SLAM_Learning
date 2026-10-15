"""Publish genuine native capture, inputs, map metrics and failure diagnostics."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from package_session import gif, probe  # noqa: E402 - shared presentation packager
from export_grid import export  # noqa: E402

ROOT = HERE.parents[3]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def compact_snapshots(dest, run, record):
    source = run / "srrg-snapshots.npz"
    if not source.is_file():
        return
    archive = np.load(source)
    target = dest / "srrg-map-snapshots.npz"
    np.savez_compressed(
        target, **{k: archive[k] for k in archive.files if k == "stamps" or k.startswith("clean_")}
    )
    previous = dest / "srrg-snapshots.npz"
    if previous.is_file():
        assert previous.resolve().is_relative_to((ROOT / "results/reference").resolve())
        previous.unlink()  # Generated duplicate only; the full original stays in run.
    record["artifacts"].pop("srrg-snapshots.npz", None)
    record["snapshot_export"] = {
        "scope": "All clean-map snapshots and timestamps retained; quadratic raw-history duplicates stay in original run and are reconstructible from saved scan+pose inputs",
        "original_sha256": sha(source),
        "original_path": str(source),
    }


def augment_exports():
    for scene in ("static", "dynamic", "large-change", "corridor", "static-graph-merge-on"):
        dest = ROOT / f"results/reference/srrg-2d-{scene}"
        path = dest / "record.json"
        record = json.loads(path.read_text())
        for name, meta in record["artifacts"].items():
            assert sha(dest / name) == meta["sha256"]
        run = Path(record["source_run"])
        compact_snapshots(dest, run, record)
        export(run)
        shutil.copytree(run / "maps", dest / "maps", dirs_exist_ok=True)
        for p in run.glob("prior*"):
            if p.is_file():
                shutil.copy2(p, dest / p.name)
        prior = record.get("multi_session_prior")
        if prior:
            target = dest / "initial-prior"
            target.mkdir(exist_ok=True)
            for p in Path(prior).glob("prior*"):
                if p.is_file():
                    shutil.copy2(p, target / p.name)
            record["initial_prior_artifacts"] = {p.name: sha(p) for p in target.iterdir() if p.is_file()}
        for p in sorted(dest.rglob("*")):
            if p.is_file() and p != path:
                record["artifacts"][p.relative_to(dest).as_posix()] = {
                    "sha256": sha(p),
                    "bytes": p.stat().st_size,
                    "availability": "portable",
                }
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Verified exports and lineage:", scene)


def package(run, diagnostic=False):
    runtime = json.loads((run / "runtime.json").read_text())
    scene = runtime["scene"]
    dest = ROOT / "results/reference" / ("srrg-diagnostic-" + run.name if diagnostic else "srrg-2d-" + scene)
    if dest.exists():
        raise FileExistsError(dest)
    if not diagnostic:
        assert json.loads((run / "session-stopped.json").read_text())["exit_code"] == 0
        assert (run / "srrg-finished.json").is_file()
        audit = json.loads((run / "srrg-quality.json").read_text())
    else:
        audit = {}
    if not diagnostic:
        export(run)
    dest.mkdir(parents=True)
    names = [
        "execution.mp4",
        "session.json",
        "runtime.json",
        "truth.jsonl",
        "recording.started",
        "recording.stopped",
        "srrg-frames.jsonl",
        "srrg-inputs.jsonl",
        "srrg-final.npy",
        "srrg-raw.npy",
        "srrg-quality-inputs.npz",
        "srrg-quality.json",
        "srrg-finished.json",
        "object-geometry.json",
        "object-truth.jsonl",
        "object-scene.pbtxt",
        "srrg-2d.urdf",
        "srrg-bridge.yaml",
        "live.rviz",
        "session-stopped.json",
        "failed.json",
    ]
    for name in names:
        if (run / name).is_file():
            shutil.copy2(run / name, dest / name)
    for p in run.glob("prior*"):
        if p.is_file():
            shutil.copy2(p, dest / p.name)
    if not diagnostic:
        shutil.copytree(run / "maps", dest / "maps")
    if runtime.get("srrg_prior"):
        prior = Path(runtime["srrg_prior"])
        (dest / "initial-prior").mkdir()
        for p in prior.glob("prior*"):
            if p.is_file():
                shutil.copy2(p, dest / "initial-prior" / p.name)
    shutil.copytree(run / "logs", dest / "logs")
    timing = gif(dest / "execution.mp4", dest / "execution.gif")
    info = probe(dest / "execution.mp4")
    duration = float(info["format"]["duration"])
    for label, fraction in [("first", 0.05), ("mid", 0.5), ("last", 0.95)]:
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-ss",
                str(duration * fraction),
                "-i",
                str(dest / "execution.mp4"),
                "-frames:v",
                "1",
                "-update",
                "1",
                "-y",
                str(dest / f"frame-{label}.png"),
            ],
            check=True,
        )
    sources = {p.relative_to(ROOT).as_posix(): sha(p) for p in HERE.iterdir() if p.suffix in (".py", ".cpp")}
    record = {
        "schema_version": 1,
        "kind": "srrg_native_2d_mapping_diagnostic" if diagnostic else "srrg_native_2d_mapping",
        "status": "diagnostic_failed" if diagnostic else "executed",
        "exit_code": None if diagnostic else 0,
        "source_run": str(run),
        "command": json.loads((run / "session.json").read_text())["flow"],
        "scope": "Actual Gazebo + RViz + Terminal capture; native author 2D mapping, not a 3D projection. Single short session unless explicit prior present.",
        "map_quality": audit.get("methods", {}),
        "audit": audit,
        "capture": info,
        "gif_timing": timing,
        "adapter_sources_at_packaging": sources,
        "sources_at_capture": json.loads((run / "session.json").read_text())["assets"],
        "native_versions": {
            "srrg_mapper2d": "5ea162d1d90b25f916f25240b653e97e2758210e",
            "srrg_scan_matcher": "e070f08f6663132d1de3e49869132581091972d7",
        },
        "truth_input_to_mapper": False,
        "fixed_start_anchor": runtime["spawn"],
        "multi_session_prior": runtime.get("srrg_prior"),
        "artifacts": {},
    }
    compact_snapshots(dest, run, record)
    for p in sorted(dest.rglob("*")):
        if p.is_file():
            record["artifacts"][p.relative_to(dest).as_posix()] = {
                "sha256": sha(p),
                "bytes": p.stat().st_size,
                "availability": "portable",
            }
    (dest / "record.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(dest)
    return dest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("run", type=Path, nargs="?")
    p.add_argument("--diagnostic", action="store_true")
    p.add_argument("--augment-exports", action="store_true")
    a = p.parse_args()
    if a.augment_exports:
        augment_exports()
    else:
        package(a.run, a.diagnostic)
