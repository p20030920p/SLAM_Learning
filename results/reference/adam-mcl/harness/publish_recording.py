"""Publish the recorded session directory exactly as it will be stored.

record_session.py writes its own recording.json next to the capture. Three files
must not be published verbatim:

  full-session.mp4   renamed to replay.mp4, which is the name the repository
                     convention and docs/figures/slots.json expect
  terminal.raw       124 MB of PTY transcript; committed xz-compressed instead
  private.Xauthority an X authentication cookie, deleted (never publish secrets)
  GO / DONE          recorder handshake markers, deleted

Everything else is kept byte-for-byte. The artifacts map is rewritten so it
describes exactly what is in the directory, and the removed files keep their
hashes in a separate record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()

    record = json.loads((directory / "recording.json").read_text(encoding="utf-8"))
    original = dict(record["artifacts"])

    excluded = {}
    for name in ("private.Xauthority", "GO", "DONE"):
        path = directory / name
        if path.is_file():
            excluded[name] = {"sha256": sha256(path), "bytes": path.stat().st_size,
                              "reason": "recorder handshake marker or X authentication cookie"}
            path.unlink()

    raw = directory / "terminal.raw"
    if raw.is_file():
        import subprocess
        subprocess.run(["xz", "-9", "-T2", "-f", "-k", str(raw)], check=True)
        excluded["terminal.raw"] = {
            "sha256": sha256(raw), "bytes": raw.stat().st_size,
            "reason": "published as terminal.raw.xz; the uncompressed PTY transcript is 124 MB",
        }
        raw.unlink()

    video = directory / "full-session.mp4"
    if video.is_file():
        video.rename(directory / "replay.mp4")
        record["renamed"] = {"full-session.mp4": "replay.mp4",
                             "reason": "repository name for the recorded session video"}

    record["artifacts"] = {}
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.name != "recording.json":
            record["artifacts"][path.name] = {"sha256": sha256(path), "bytes": path.stat().st_size}
    record["not_published"] = excluded
    record["published_note"] = (
        "Artifacts map rewritten after publishing: full-session.mp4 was renamed replay.mp4, "
        "terminal.raw is committed xz-compressed, and the X authentication cookie plus the "
        "recorder handshake markers were removed. All published files keep their recorded bytes.")
    (directory / "recording.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({name: info["bytes"] for name, info in record["artifacts"].items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
