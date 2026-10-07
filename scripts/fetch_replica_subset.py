"""Fetch CRC-checked ZIP members by HTTP range; never download the entire archive."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path


class RangeFile(io.RawIOBase):
    def __init__(self, url: str):
        self.url, self.position = url, 0
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60) as r:
            self.size = int(r.headers["Content-Length"])
            self.etag = r.headers.get("ETag")
        self.blocks = {}

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        if self.position < 0:
            raise ValueError("Negative archive offset")
        return self.position

    def read(self, size=-1):
        size = min(self.size - self.position, size if size >= 0 else self.size - self.position)
        result = []
        block_size = 1024 * 1024
        while size > 0:
            block = self.position // block_size
            if block not in self.blocks:
                start = block * block_size
                stop = min(start + block_size, self.size) - 1
                request = urllib.request.Request(self.url, headers={"Range": f"bytes={start}-{stop}",
                                                                    "Accept-Encoding": "identity"})
                with urllib.request.urlopen(request, timeout=120) as r:
                    if r.status != 206 or r.headers.get("Content-Range") != f"bytes {start}-{stop}/{self.size}":
                        raise ValueError("Server did not honor exact byte range")
                    data = r.read(stop - start + 2)
                if len(data) != stop - start + 1:
                    raise ValueError("Truncated or oversized HTTP range")
                if len(self.blocks) >= 16:
                    self.blocks.pop(next(iter(self.blocks)))
                self.blocks[block] = data
            offset = self.position % block_size
            n = min(size, len(self.blocks[block]) - offset)
            result.append(self.blocks[block][offset:offset + n])
            self.position += n
            size -= n
        return b"".join(result)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path(".cache/semantic-data/Replica"))
    p.add_argument("--frames", type=int, default=40)
    p.add_argument("--stride", type=int, default=5)
    args = p.parse_args()
    if args.frames < 1 or args.stride < 1 or args.frames * args.stride > 2000:
        p.error("Positive frame count/stride covering at most 2000 source entries required")
    url = "https://cvg-data.inf.ethz.ch/nice-slam/data/Replica.zip"
    remote = RangeFile(url)
    with zipfile.ZipFile(remote) as archive:
        names = archive.namelist()
        trajectory = next(name for name in names if name.endswith("room0/traj.txt"))
        prefix = trajectory[:-len("traj.txt")]
        target = args.output / "room0"
        target.mkdir(parents=True, exist_ok=True)
        full = archive.read(trajectory)  # ZipFile validates CRC.
        (target / "traj.full.txt").write_bytes(full)
        lines = full.decode("utf-8").splitlines()
        indexes = list(range(0, args.frames * args.stride, args.stride))
        entries = []
        for i in indexes:
            for filename in (f"frame{i:06d}.jpg", f"depth{i:06d}.png"):
                member = prefix + "results/" + filename
                data = archive.read(member)  # ZipFile validates CRC.
                path = target / "results" / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                entries.append({"member": member, "source_crc32": archive.getinfo(member).CRC,
                                "path": path.relative_to(args.output).as_posix(), "bytes": len(data),
                                "sha256": hashlib.sha256(data).hexdigest()})
            print(f"Fetched source frame {i:06d}", flush=True)
        pose_subset = ("\n".join(lines[i] for i in indexes) + "\n").encode()
        (target / "traj.txt").write_bytes(pose_subset)
        for name, data in (("traj.full.txt", full), ("traj.txt", pose_subset)):
            entries.append({"path": "room0/" + name, "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest()})
        metadata = {"source_url": url, "archive_bytes": remote.size, "archive_etag": remote.etag,
                    "whole_archive_sha256": None, "member_crc_verified": True, "scene": "room0",
                    "source_frame_indexes": indexes, "files": entries,
                    "scope": "Replica rendered RGB-D, 40-entry subset by default; not full paper evaluation",
                    "poses": "Subset of supplied camera-to-world matrices in original index order; no estimated SLAM"}
        (args.output / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        print(f"Manifest saved: {args.output / 'manifest.json'}", flush=True)


if __name__ == "__main__":
    main()
