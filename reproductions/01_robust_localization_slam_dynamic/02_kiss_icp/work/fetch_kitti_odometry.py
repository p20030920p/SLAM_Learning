#!/usr/bin/env python3
"""Fetch only the KITTI odometry sequences we evaluate, straight from the official zip.

The official `data_odometry_velodyne.zip` is 84.8 GB, but every member is *stored*
(no compression) and each sequence's frames sit in one contiguous byte range.  So we
read the zip's central directory once (a few KB) and then issue **one ranged GET per
sequence** instead of downloading the whole archive.

Layout it produces (what the KISS-ICP notebook expects):

    data/raw/kitti-odometry/dataset/
    ├── poses/00.txt … 10.txt
    └── sequences/00/{calib.txt,times.txt,velodyne/*.bin} …

Usage:
    python3 fetch_kitti_odometry.py                  # sequences 00–10 (~43 GB)
    python3 fetch_kitti_odometry.py --seq 04 05      # a subset
    python3 fetch_kitti_odometry.py --check          # report what is already there
"""
import argparse
import os
import struct
import sys
import urllib.request
import zipfile

BASE = "https://s3.eu-central-1.amazonaws.com/avg-kitti"
VELODYNE_ZIP = f"{BASE}/data_odometry_velodyne.zip"
POSES_ZIP = f"{BASE}/data_odometry_poses.zip"
CALIB_ZIP = f"{BASE}/data_odometry_calib.zip"

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(HERE, "..", "data", "raw", "kitti-odometry")


def fetch_range(url, start, end, timeout=120):
    """Bytes [start, end) of a remote file."""
    req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end - 1}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    if len(data) != end - start:
        raise RuntimeError(f"short read: wanted {end - start}, got {len(data)}")
    return data


def stream_range(url, start, end, path, timeout=120, chunk=8 << 20):
    """Bytes [start, end) of a remote file, written straight to disk.

    One sequence is up to ~9 GB; holding that in RAM to split it afterwards is not
    an option on a 15 GB machine, so the range goes to a temporary file and the
    splitting reads it back in slices.
    """
    req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end - 1}"})
    done = 0
    with urllib.request.urlopen(req, timeout=timeout) as resp, open(path, "wb") as fh:
        while True:
            block = resp.read(chunk)
            if not block:
                break
            fh.write(block)
            done += len(block)
    if done != end - start:
        raise RuntimeError(f"short read: wanted {end - start}, got {done}")
    return path


def central_directory(url):
    """ZipInfo list, read from the remote archive's central directory only."""
    with zipfile.ZipFile(_RemoteFile(url)) as zf:
        return zf.infolist()


class _RemoteFile:
    """Minimal seekable file over HTTP ranges, enough for zipfile's directory read."""

    def __init__(self, url):
        self.url = url
        self.pos = 0
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=60) as resp:
            self.size = int(resp.headers["Content-Length"])

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else (self.pos + offset if whence == 1
                                              else self.size + offset)
        return self.pos

    def tell(self):
        return self.pos

    def read(self, n=-1):
        if n < 0:
            n = self.size - self.pos
        n = min(n, self.size - self.pos)
        if n <= 0:
            return b""
        data = fetch_range(self.url, self.pos, self.pos + n)
        self.pos += len(data)
        return data


def extract_sequence(url, infos, seq, out_dir):
    """One ranged GET covering `seq`, then split it back into frames."""
    prefix = f"dataset/sequences/{seq}/velodyne/"
    frames = sorted((i for i in infos
                     if i.filename.startswith(prefix) and i.filename.endswith(".bin")),
                    key=lambda i: i.header_offset)
    if not frames:
        raise RuntimeError(f"sequence {seq} has no velodyne frames in the zip")

    start = frames[0].header_offset
    last = frames[-1]
    # local file header (30) + name + extra; the gap is constant inside one sequence
    if len(frames) > 1:
        over = frames[1].header_offset - (frames[0].header_offset + frames[0].file_size)
    else:
        over = 30 + len(last.filename) + 64
    end = last.header_offset + over + last.file_size

    velo_dir = os.path.join(out_dir, "dataset", "sequences", seq, "velodyne")
    os.makedirs(velo_dir, exist_ok=True)
    done = [f for f in os.listdir(velo_dir) if f.endswith(".bin")]
    if len(done) == len(frames):
        print(f"  seq {seq}: already complete ({len(done)} frames) — skipped")
        return len(done)

    print(f"  seq {seq}: {len(frames)} frames, {(end - start) / 1e9:.2f} GB"
          f" (bytes {start}..{end})", flush=True)
    tmp = os.path.join(velo_dir, f".seq{seq}.range")
    stream_range(url, start, end, tmp)
    print(f"  seq {seq}: downloaded to {tmp}, splitting …", flush=True)

    pos = 0
    written = 0
    with open(tmp, "rb") as fh:
        for info in frames:
            fh.seek(pos)
            sig, _ver, _flag, _method, _t, _d, _crc, csize, usize, fn_len, extra_len = \
                struct.unpack("<IHHHHHIIIHH", fh.read(30))
            if sig != 0x04034B50:
                raise RuntimeError(f"bad local header for {info.filename} at blob offset {pos}")
            data_start = pos + 30 + fn_len + extra_len
            if usize != info.file_size:
                raise RuntimeError(f"size mismatch for {info.filename}")
            fh.seek(data_start)
            with open(os.path.join(velo_dir, os.path.basename(info.filename)), "wb") as out:
                left = usize
                while left:
                    block = fh.read(min(8 << 20, left))
                    if not block:
                        raise RuntimeError(f"truncated payload for {info.filename}")
                    out.write(block)
                    left -= len(block)
            pos = data_start + usize
            written += 1
    os.remove(tmp)
    print(f"  seq {seq}: wrote {written} frames", flush=True)
    return written


def fetch_small_zip(url, out_dir, what):
    """poses / calib are a few hundred KB — plain download and unzip."""
    if os.path.isdir(os.path.join(out_dir, "dataset")) and what == "poses" \
            and os.path.exists(os.path.join(out_dir, "dataset", "poses", "00.txt")):
        print(f"  {what}: already there")
        return
    tmp = os.path.join(out_dir, os.path.basename(url))
    os.makedirs(out_dir, exist_ok=True)
    print(f"  {what}: {url}")
    urllib.request.urlretrieve(url, tmp)
    with zipfile.ZipFile(tmp) as zf:
        zf.extractall(out_dir)
    os.remove(tmp)
    print(f"  {what}: extracted")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seq", nargs="*", default=[f"{i:02d}" for i in range(11)],
                    help="sequences to fetch (default 00–10, the KITTI training set)")
    ap.add_argument("--out", default=os.path.normpath(DEFAULT_OUT))
    ap.add_argument("--check", action="store_true", help="only report what exists")
    args = ap.parse_args()

    out_dir = os.path.abspath(args.out)
    print(f"target: {out_dir}")

    if args.check:
        for seq in args.seq:
            velo = os.path.join(out_dir, "dataset", "sequences", seq, "velodyne")
            n = len([f for f in os.listdir(velo) if f.endswith(".bin")]) \
                if os.path.isdir(velo) else 0
            print(f"  seq {seq}: {n} frames")
        poses = os.path.join(out_dir, "dataset", "poses")
        print(f"  poses: {len(os.listdir(poses)) if os.path.isdir(poses) else 0} files")
        return 0

    fetch_small_zip(POSES_ZIP, out_dir, "poses")
    fetch_small_zip(CALIB_ZIP, out_dir, "calib")

    print("reading the remote zip's central directory …")
    infos = central_directory(VELODYNE_ZIP)
    print(f"  {len(infos)} members")
    for seq in args.seq:
        extract_sequence(VELODYNE_ZIP, infos, seq, out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
