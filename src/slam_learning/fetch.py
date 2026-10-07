from __future__ import annotations

import json
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from .provenance import digest, utc_now, write_json


def safe_extract(archive: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            name = PurePosixPath(info.filename.replace("\\", "/"))
            target = (destination / str(name)).resolve()
            if name.is_absolute() or not target.is_relative_to(destination) or ":" in info.filename:
                raise ValueError(f"Unsafe archive path: {info.filename}")
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError(f"Archive symlink refused: {info.filename}")
        z.extractall(destination)


def fetch(root: Path, direct: bool = False) -> None:
    cache = root / ".cache"
    config = json.loads((root / "configs/dataset.json").read_text(encoding="utf-8"))
    archive = cache / "downloads" / config["filename"]
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({})) if direct else urllib.request.build_opener()
        part = archive.with_suffix(".zip.part")
        request = urllib.request.Request(config["url"], headers={"User-Agent": "SLAM-Learning/0.2 research"})
        with opener.open(request, timeout=60) as response, part.open("wb") as f:
            total = int(response.headers.get("Content-Length", 0))
            size, last = 0, 0
            while block := response.read(1024 * 1024):
                f.write(block)
                size += len(block)
                if size - last >= 32 * 1024 * 1024:
                    print(f"Downloaded {size / 1e6:.0f} / {total / 1e6:.0f} MB", flush=True)
                    last = size
        if digest(part, "md5") != config["md5"]:
            raise ValueError("Dataset checksum mismatch; .part kept for diagnosis, never extracted")
        part.replace(archive)
    if digest(archive, "md5") != config["md5"]:
        raise ValueError("Cached archive checksum mismatch; remove this archive explicitly before retrying")
    target = cache / "datasets"
    if not (target / "00/provenance.json").exists():
        stage = cache / "dataset-stage"
        if stage.exists():
            shutil.rmtree(stage)
        safe_extract(archive, stage)
        seq = stage / "00"
        if not seq.is_dir():
            raise ValueError("Archive has no 00/ sequence")
        target.mkdir(parents=True, exist_ok=True)
        if (target / "00").exists():
            raise ValueError("Unverified existing dataset directory; move it aside before fetching")
        seq.replace(target / "00")
        files = sorted((target / "00").rglob("*.pcd"))
        write_json(target / "00/provenance.json", {
            "downloaded_at": utc_now(), "source": config, "archive_sha256": digest(archive),
            "files": {p.relative_to(target / "00").as_posix(): digest(p) for p in files},
        })
    sources = json.loads((root / "configs/upstreams.json").read_text(encoding="utf-8"))
    for name, spec in sources.items():
        checkout = cache / "upstream" / name
        git = ["git", "-c", "http.proxy=", "-c", "https.proxy="] if direct else ["git"]
        if not checkout.exists():
            checkout.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(git + ["clone", spec["url"], str(checkout)], check=True)
        dirty = subprocess.check_output(["git", "-C", str(checkout), "status", "--porcelain"], text=True)
        if dirty.strip():
            raise ValueError(f"Upstream checkout {name} has edits; fetch refuses to reset them")
        subprocess.run(git + ["-C", str(checkout), "checkout", "--detach", spec["commit"]], check=True)
    print("Verified dataset and pinned upstreams ready", flush=True)
