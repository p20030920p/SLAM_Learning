"""Fetch only the predeclared new-scene RGB-D frames, with ZIP CRC validation."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fetch_replica_subset import RangeFile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--archive", type=Path,
                        help="Read an existing official ZIP without changing its owner/cache")
    args = parser.parse_args()
    config = json.loads(args.protocol.read_text(encoding="utf-8"))
    scene = config["scene"]
    indexes = sorted(set(config["mapping_frames"] + config["reference_frames"]))
    manifest_path = args.output / "manifest.json"
    if manifest_path.exists():
        saved = json.loads(manifest_path.read_text())
        if saved["protocol_sha256"] != sha(args.protocol):
            raise ValueError("Protocol differs from downloaded scene")
        for item in saved["files"]:
            if sha(args.output / item["path"]) != item["sha256"]:
                raise ValueError(f"Changed source file: {item['path']}")
        print("Existing new-scene source manifest verified", flush=True)
        return 0
    url = "https://cvg-data.inf.ethz.ch/nice-slam/data/Replica.zip"
    remote = None if args.archive else RangeFile(url)
    entries = []
    with zipfile.ZipFile(args.archive if args.archive else remote) as archive:
        trajectory = next(n for n in archive.namelist() if n.endswith(f"{scene}/traj.txt"))
        prefix = trajectory[:-len("traj.txt")]
        full = archive.read(trajectory)
        lines = full.decode().splitlines()
        for index in indexes:
            for kind, suffix in (("frame", "jpg"), ("depth", "png")):
                member = f"{prefix}results/{kind}{index:06d}.{suffix}"
                relative = f"{scene}/results/{kind}{index:06d}.{suffix}"
                target = args.output / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(member))
                entries.append({"path": relative, "member": member,
                                "crc32": archive.getinfo(member).CRC,
                                "bytes": target.stat().st_size, "sha256": sha(target)})
            print(f"CRC-checked {scene} frame {index:06d}", flush=True)
        for name, content in (("traj.full.txt", full), ("traj.txt", (
            "\n".join(lines[i] for i in config["mapping_frames"]) + "\n").encode())):
            target = args.output / scene / name
            target.write_bytes(content)
            entries.append({"path": target.relative_to(args.output).as_posix(),
                            "bytes": len(content), "sha256": sha(target)})
    manifest = {"scene": scene, "source_url": url,
                "archive_etag": remote.etag if remote else None,
                "archive_bytes": remote.size if remote else args.archive.stat().st_size,
                "source_access": "local_archive_read_only" if args.archive else "http_ranges",
                "whole_archive_sha256": None,
                "member_crc_verified": True, "protocol_sha256": sha(args.protocol),
                "mapping_frames": config["mapping_frames"], "reference_frames": config["reference_frames"],
                "fetched_at": datetime.now(timezone.utc).isoformat(), "files": entries}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Bound source manifest: {manifest_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
