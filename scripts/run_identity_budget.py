"""Gated v2 entry point. Archive rejected inputs without importing native/CUDA code."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from slam_learning.identity_budget import check_resources, digest, validate_freeze


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("protocol", "annotations", "freeze", "data", "frontend", "weights", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--exploratory", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Never overwrite an experiment attempt")
    try:
        freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
        validate_freeze(args.protocol, args.annotations, args.data, freeze, exploratory=args.exploratory)
        front = json.loads((args.frontend / "record.json").read_text())
        if (front.get("status") != "executed" or front.get("freeze_sha256") != digest(args.freeze) or
                front.get("scene") != "room2" or front.get("frames") != list(range(0, 400, 25))):
            raise ValueError("Frontend record does not match the reviewed room2 inputs")
        check_resources()
    except (ValueError, KeyError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        args.output.mkdir(parents=True, exist_ok=False)
        record = {"kind": "identity_budget_v2", "status": "rejected_before_native_import",
                  "created_at": datetime.now(timezone.utc).isoformat(), "error": str(error), "cells": [],
                  "input_hashes": {name: digest(getattr(args, name)) for name in
                                   ("protocol", "annotations", "freeze") if getattr(args, name).is_file()}}
        (args.output / "record.json").write_text(json.dumps(record, indent=2) + "\n")
        print(f"Rejected before model load: {error}", file=sys.stderr)
        return 1
    command = [sys.executable, str(Path(__file__).with_name("run_delayed_correction.py")), "--identity-budget"]
    if args.exploratory:
        command.append("--exploratory")
    for name in ("protocol", "annotations", "freeze", "data", "frontend", "weights", "output"):
        command.extend([f"--{name}", str(getattr(args, name))])
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
