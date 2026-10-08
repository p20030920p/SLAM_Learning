"""Recover exact executed cell adapters from Git history without altering results."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    required = set()
    for run in args.runs:
        for path in (run / "cells").glob("*/record.json"):
            required.add(json.loads(path.read_text(encoding="utf-8"))["script_sha256"])
    versions = {}
    commits = subprocess.check_output(
        ["git", "log", "--all", "--format=%H", "--", "scripts/run_paired_cell.py"], cwd=root, text=True
    ).splitlines()
    for commit in commits:
        blob = subprocess.check_output(["git", "show", f"{commit}:scripts/run_paired_cell.py"], cwd=root)
        for style, content in (
            ("LF", blob.replace(b"\r\n", b"\n")),
            ("CRLF", blob.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")),
        ):
            digest = hashlib.sha256(content).hexdigest()
            if digest in required and digest not in versions:
                versions[digest] = {"commit": commit, "newlines": style, "content": content}
    if required - versions.keys():
        raise ValueError(f"Executed source is absent from Git history: {required - versions.keys()}")
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {}
    for digest, version in versions.items():
        (args.output / f"{digest}.py").write_bytes(version.pop("content"))
        manifest[digest] = version
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Exact adapters recovered: {len(manifest)}")


if __name__ == "__main__":
    main()
