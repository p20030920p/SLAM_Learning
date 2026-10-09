from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temp.replace(path)


def git_state(path: Path) -> dict:
    def read(*args):
        return subprocess.check_output(["git", "-C", str(path), *args], text=True, encoding="utf-8").strip()
    try:
        return {"commit": read("rev-parse", "HEAD"), "dirty": bool(read("status", "--porcelain"))}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "dirty": None}


def environment() -> dict:
    packages = {}
    for name in ("slam-learning", "numpy", "scipy", "matplotlib", "dufomap", "open3d", "dztimer"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {"python": sys.version, "platform": platform.platform(), "packages": packages}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def source_hashes(root: Path) -> dict:
    sources = (root / "src/slam_learning", root / "src/scripts")
    return {p.relative_to(root).as_posix(): digest(p)
            for p in sorted(path for source in sources for path in source.rglob("*.py"))}
