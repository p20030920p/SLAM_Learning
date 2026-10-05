#!/usr/bin/env python3
"""Download a Google Drive file in byte ranges when the normal link is quota-blocked.

The ELite authors' dataset lives on Drive, and the plain download endpoint answers
"Google Drive - Quota exceeded" (there is a per-file cap on how many times a file
may be downloaded per day). What still works is a *ranged* request: the server
happily serves `Range: bytes=a-b` and returns the real bytes with 206.

So this fetches the file chunk by chunk. It is a workaround for the quota page,
not a way around any permission: the files are public, and the same URL serves
them normally when the quota is fresh.

Usage:
    python3 gdrive_range_fetch.py <file-id> <output-path> [--chunk-mb 8]
"""
import argparse
import os
import sys
import time
import urllib.request

URL = ("https://drive.usercontent.google.com/download"
       "?id={fid}&export=download&confirm=t")


def _request(fid, start, end, timeout=180):
    req = urllib.request.Request(
        URL.format(fid=fid),
        headers={"Range": f"bytes={start}-{end}", "User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=timeout)


def total_size(fid):
    with _request(fid, 0, 0) as resp:
        if resp.status != 206:
            raise RuntimeError(f"server answered {resp.status}; the ranged path is unavailable")
        return int(resp.headers["Content-Range"].split("/")[-1])


def fetch(fid, out, chunk=8 << 20, attempts=40, max_backoff=60.0):
    size = total_size(fid)
    done = os.path.getsize(out) if os.path.exists(out) else 0
    if done > size:
        done = 0
    print(f"  total {size / 1e6:.1f} MB, {chunk >> 20} MB per request, resuming at "
          f"{done / 1e6:.1f} MB")
    t0 = time.time()
    with open(out, "ab" if done else "wb") as fh:
        while done < size:
            end = min(done + chunk, size) - 1
            for attempt in range(attempts):
                try:
                    with _request(fid, done, end) as resp:
                        block = resp.read()
                    if len(block) != end - done + 1:
                        raise RuntimeError(f"short read at {done}: {len(block)} "
                                           "(the quota page came back)")
                    break
                except Exception as exc:                      # noqa: BLE001
                    if attempt == attempts - 1:
                        raise
                    wait = min(3.0 * (attempt + 1), max_backoff)
                    print(f"\n    quota/throttle at {done / 1e6:.0f} MB, retry "
                          f"{attempt + 1}/{attempts - 1} in {wait:.0f}s: {exc}",
                          flush=True)
                    time.sleep(wait)
            fh.write(block)
            done += len(block)
            pct = 100.0 * done / size
            rate = done / max(time.time() - t0, 1e-9) / 1e6
            print(f"\r  {pct:5.1f} %  {done / 1e6:7.1f}/{size / 1e6:.1f} MB  {rate:5.1f} MB/s",
                  end="", flush=True)
    print()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file_id")
    ap.add_argument("output")
    ap.add_argument("--chunk-mb", type=int, default=4)
    args = ap.parse_args()

    if os.path.exists(args.output) and os.path.getsize(args.output) == total_size(args.file_id):
        print(f"{args.output} already complete")
        return 0
    fetch(args.file_id, args.output, chunk=args.chunk_mb << 20)
    print(f"wrote {args.output} ({os.path.getsize(args.output) / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
