"""Stage only manifest-listed RGB-D inputs, verifying every copied hash.

Useful for WSL replay: keep original recordings on Windows; read images from
Linux filesystem without copying old algorithm outputs or changing the data.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--verify-existing", action="store_true", help="Audit an existing staged copy; never overwrite inputs")
    args = ap.parse_args()
    source, target = args.dataset.resolve(), args.output.resolve()
    if source == target or source.is_relative_to(target) or target.is_relative_to(source):
        ap.error("Source and staging directories must be separate, without nesting")
    if args.verify_existing:
        if not target.is_dir():
            ap.error("Existing staging directory missing")
    else:
        target.mkdir(parents=True, exist_ok=False)
    report_path = target / "stage-verification.json"
    if report_path.exists():
        ap.error("Refusing to overwrite an earlier verification")
    record = {"status": "failed", "source": str(source), "target": str(target),
              "verify_existing": args.verify_existing, "checked_files": 0, "bytes": 0}
    start = time.monotonic()
    try:
        manifest = json.loads((source / "rgbd.json").read_text())
        if manifest["status"] != "exported":
            raise ValueError("Require successful RGB-D export")
        files = {"rgbd.json": sha(source / "rgbd.json"), **manifest["configuration_files"]}
        for row in manifest["frames"]:
            for item in row["files"].values():
                if item["path"] in files and files[item["path"]] != item["sha256"]:
                    raise ValueError("Conflicting manifest file hashes")
                files[item["path"]] = item["sha256"]
        for relative, expected in files.items():
            origin, dest = (source / relative).resolve(), (target / relative).resolve()
            if not origin.is_relative_to(source) or not dest.is_relative_to(target):
                raise ValueError("Manifest path escapes input or output directory")
            if not args.verify_existing:
                if sha(origin) != expected:
                    raise ValueError(f"Source hash mismatch: {relative}")
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origin, dest)
            if sha(dest) != expected:
                raise ValueError(f"Staged hash mismatch: {relative}")
            record["checked_files"] += 1
            record["bytes"] += dest.stat().st_size
        record.update(status="verified", input_manifest_sha256=files["rgbd.json"])
    except Exception as error:
        record["error"] = repr(error)
    record["wall_s"] = time.monotonic() - start
    report_path.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    return int(record["status"] != "verified")


if __name__ == "__main__":
    raise SystemExit(main())
