"""Exploratory simple-parameter controls using the frozen paired input errors."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from slam_learning.provenance import digest, git_state, utc_now, write_json
from slam_learning.runner import verify_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    protocol_path = root / "configs/paired_controls.json"
    protocol = json.loads(protocol_path.read_text())
    suite = json.loads((args.suite / "record.json").read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "protocol.json").write_bytes(protocol_path.read_bytes())
    record = {
        "schema_version": 1,
        "kind": "paired_parameter_controls",
        "status": "running",
        "started_at": utc_now(),
        "protocol": protocol,
        "repository": git_state(root),
        "script_sha256": digest(Path(__file__)),
        "suite_protocol_sha256": digest(args.suite / "inputs/configs/paired_pose.json"),
        "artifacts": {},
        "cells": [],
    }
    write_json(args.output / "record.json", record)
    for original in suite["cells"]:
        method = original["method"]
        if method not in ("dufomap", "conceptgraphs") or original["rms_m"] not in (
            0.0,
            protocol["translation_rms_m"],
        ):
            continue
        thresholds = (
            protocol["dufomap_d_p"] if method == "dufomap" else protocol["conceptgraphs_sim_threshold"]
        )
        for threshold in thresholds:
            name = f"{original['id']}-threshold-{threshold}"
            destination = args.output / "cells" / name
            env_name = ".venv" if method == "dufomap" else ".venv-semantic"
            command = [
                str(root / env_name / "bin/python"),
                str(root / "scripts/run_paired_cell.py"),
                "--method",
                method,
                "--output",
                str(destination),
                "--errors",
                str((args.suite / original["path"]).resolve()),
                "--threshold",
                str(threshold),
            ]
            if method == "conceptgraphs":
                command.extend(
                    [
                        "--source",
                        str(root / "results/runs/conceptgraphs-7795d7b47007"),
                        "--text-features",
                        str((args.suite / "inputs/text_features.npy").resolve()),
                    ]
                )
            print(name, flush=True)
            with (args.output / f"{name}.log").open("w") as log:
                result = subprocess.run(
                    command,
                    cwd=root,
                    env=dict(os.environ, OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4"),
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=1800,
                )
            if result.returncode:
                record.update(status="failed", failed_cell=name)
                write_json(args.output / "record.json", record)
                print((args.output / f"{name}.log").read_text()[-6000:])
                return 1
            path = destination / "record.json"
            issues = verify_record(path, full=True)
            if issues:
                raise ValueError(str(issues))
            measured = json.loads(path.read_text())
            record["cells"].append(
                {
                    **original,
                    "id": name,
                    "original_id": original["id"],
                    "threshold": threshold,
                    "record_sha256": digest(path),
                    "summary": measured["summary"],
                }
            )
            write_json(args.output / "record.json", record)
    record.update(status="executed", finished_at=utc_now(), completed_cells=len(record["cells"]), exit_code=0)
    for path in args.output.rglob("*"):
        if not path.is_file() or "cells" in path.relative_to(args.output).parts or path.name == "record.json":
            continue
        record["artifacts"][path.relative_to(args.output).as_posix()] = {
            "sha256": digest(path),
            "bytes": path.stat().st_size,
            "availability": "portable",
        }
    write_json(args.output / "record.json", record)
    print(f"Simple parameter controls completed: {len(record['cells'])}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
