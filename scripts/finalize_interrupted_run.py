"""Append an observed supervisor termination to an unfinished local run."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from run_conceptgraphs import sha, timestamp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    parser.add_argument("--exit-code", type=int, required=True)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    if record.get("status") != "running" or args.exit_code == 0:
        raise ValueError("Only an unfinished non-successful run can be finalized")
    original = args.record.parent / "unfinished-record.json"
    if original.exists():
        raise FileExistsError(original)
    shutil.copy2(args.record, original)
    record.update(status="failed", exit_code=args.exit_code, finished_at=timestamp(),
                  error=args.reason, terminalization="Observed after worker termination; original running record preserved")
    for path in sorted(args.record.parent.rglob("*")):
        if not path.is_file() or path.name == "record.json" or "author-code" in path.parts or "input" in path.parts:
            continue
        record["artifacts"][path.relative_to(args.record.parent).as_posix()] = {
            "sha256": sha(path), "bytes": path.stat().st_size,
            "availability": "local_only" if path.suffix in (".ply", ".npy", ".npz") else "portable"}
    args.record.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
