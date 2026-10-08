"""Execute a frozen exploratory paired-pose protocol on four author map cores."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import uuid
from pathlib import Path

import numpy as np

from slam_learning.paired_pose import paired_translations, error_description
from slam_learning.provenance import digest, git_state, utc_now, write_json
from slam_learning.runner import verify_record


def prepare(root, output, semantic_sources):
    protocol_path = root / "configs/paired_pose.json"
    protocol = json.loads(protocol_path.read_text())
    output.mkdir(parents=True, exist_ok=False)
    inputs = output / "inputs"
    inputs.mkdir()
    for relative in (
        "configs/paired_pose.json",
        "annotations/room0/targets.json",
        "scripts/run_paired_cell.py",
        "scripts/run_paired_suite.py",
        "src/slam_learning/paired_pose.py",
    ):
        destination = inputs / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((root / relative).read_bytes())
    cells = []
    for group, count in (("lidar", 141), ("semantic", 8)):
        error_dir = inputs / group
        error_dir.mkdir()
        zero = error_dir / "reference.npy"
        np.save(zero, np.zeros((count, 3)))
        entries = [
            {
                "id": "reference",
                "mode": "reference",
                "seed": None,
                "rms_m": 0.0,
                "path": zero.relative_to(output).as_posix(),
                "error": error_description(np.zeros((count, 3))),
            }
        ]
        for amplitude in protocol["translation_rms_m"]:
            for seed in protocol["seeds"]:
                for mode, error in paired_translations(count, amplitude, seed).items():
                    name = f"{mode}-{amplitude:.2f}-{seed}"
                    path = error_dir / f"{name}.npy"
                    np.save(path, error)
                    entries.append(
                        {
                            "id": name,
                            "mode": mode,
                            "seed": seed,
                            "rms_m": amplitude,
                            "path": path.relative_to(output).as_posix(),
                            "error": error_description(error),
                        }
                    )
        for method in ("dufomap", "beautymap") if group == "lidar" else ("conceptgraphs", "hovsg"):
            cells.extend([{**entry, "method": method, "id": f"{method}-{entry['id']}"} for entry in entries])
    cg, hov = [semantic_sources[method] for method in ("conceptgraphs", "hovsg")]
    for source in (cg, hov):
        errors = verify_record(source / "record.json", full=True)
        if errors:
            raise ValueError(f"Native cache source is invalid: {errors}")
    record = {
        "schema_version": 1,
        "kind": "paired_pose_suite",
        "status": "prepared",
        "started_at": utc_now(),
        "protocol": protocol,
        "repository": git_state(root),
        "cells": cells,
        "artifacts": {},
        "semantic_sources": {method: str(path) for method, path in semantic_sources.items()},
        "source_records": {
            str(p.relative_to(root)): digest(p) for p in (cg / "record.json", hov / "record.json")
        },
        "source_code": {
            name: digest(root / name)
            for name in (
                "scripts/run_paired_cell.py",
                "scripts/run_paired_suite.py",
                "src/slam_learning/paired_pose.py",
            )
        },
    }
    write_json(output / "record.json", record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--resume", type=Path)
    parser.add_argument(
        "--conceptgraphs-source", type=Path, help="Full local native run with cached detections"
    )
    parser.add_argument(
        "--hovsg-source", type=Path, help="Full local native run with cached per-mask features"
    )
    parser.add_argument("--methods", nargs="+", default=["dufomap", "beautymap", "conceptgraphs", "hovsg"])
    parser.add_argument("--references-only", action="store_true")
    parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Verify completed cells without executing or changing them",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = (
        args.resume or args.output or root / "results/runs" / f"paired-pose-{uuid.uuid4().hex[:12]}"
    ).resolve()
    semantic_sources = {
        "conceptgraphs": (
            args.conceptgraphs_source or root / "results/runs/conceptgraphs-7795d7b47007"
        ).resolve(),
        "hovsg": (args.hovsg_source or root / "results/runs/hovsg-0206da9f0145").resolve(),
    }
    record = (
        json.loads((output / "record.json").read_text())
        if args.resume
        else prepare(root, output, semantic_sources)
    )
    semantic_sources = {
        method: Path(path) for method, path in record.get("semantic_sources", semantic_sources).items()
    }
    for source, expected in record["source_records"].items():
        if digest(root / source) != expected:
            raise ValueError("Native source record changed: " + source)
    for name, expected in record["source_code"].items():
        if not args.aggregate_only and digest(root / name) != expected:
            raise ValueError("Source changed after protocol preparation: " + name)
    for relative in ("configs/paired_pose.json", "annotations/room0/targets.json"):
        if digest(root / relative) != digest(output / "inputs" / relative):
            raise ValueError("Protocol/annotations changed after preparation")
    text_path = output / "inputs/text_features.npy"
    if not text_path.exists() and set(args.methods) & {"conceptgraphs", "hovsg"}:
        code = (
            "import numpy as np,torch,open_clip; "
            "m,_,_=open_clip.create_model_and_transforms('ViT-H-14',"
            "'.cache/semantic-weights/clip/open_clip_pytorch_model.bin',device='cuda');m.eval(); "
            f"t=open_clip.get_tokenizer('ViT-H-14')({record['protocol']['semantic_queries']!r}).cuda(); "
            "torch.set_grad_enabled(False);f=m.encode_text(t).float(); "
            f"np.save({str(text_path)!r},torch.nn.functional.normalize(f,dim=-1).cpu().numpy())"
        )
        subprocess.run([str(root / ".venv-semantic/bin/python"), "-c", code], cwd=root, check=True)
    record["status"] = "running"
    write_json(output / "record.json", record)
    for index, cell in enumerate(record["cells"]):
        if cell["method"] not in args.methods or (args.references_only and cell["mode"] != "reference"):
            continue
        destination = output / "cells" / cell["id"]
        saved = destination / "record.json"
        if saved.exists():
            previous = json.loads(saved.read_text())
            problems = verify_record(saved, full=True)
            if previous["status"] != "executed" or problems:
                raise ValueError(f"Refusing to overwrite failed or changed cell {cell['id']}: {problems}")
            continue
        if args.aggregate_only:
            raise ValueError("Aggregation requires every selected cell to be complete: " + cell["id"])
        env_name = {
            "dufomap": ".venv",
            "beautymap": ".venv",
            "conceptgraphs": ".venv-semantic",
            "hovsg": ".venv-hovsg",
        }[cell["method"]]
        command = [
            str(root / env_name / "bin/python"),
            str(root / "scripts/run_paired_cell.py"),
            "--method",
            cell["method"],
            "--output",
            str(destination),
            "--errors",
            str(output / cell["path"]),
        ]
        if cell["method"] in ("conceptgraphs", "hovsg"):
            source = semantic_sources[cell["method"]]
            command.extend(["--source", str(source), "--text-features", str(text_path)])
        print(f"[{index+1}/{len(record['cells'])}] {cell['id']}", flush=True)
        output_log = output / f"{cell['id']}.log"
        with output_log.open("w") as log:
            status = subprocess.run(
                command,
                cwd=root,
                env=dict(os.environ, OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4"),
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=3600,
            ).returncode
        if status:
            record.update(status="failed", failed_cell=cell["id"], exit_code=status)
            write_json(output / "record.json", record)
            print(output_log.read_text()[-6000:], flush=True)
            return status
        result = json.loads(saved.read_text())["summary"]
        print(json.dumps({"cell": cell["id"], "metrics": result["metrics"]}, allow_nan=False), flush=True)
    measured = []
    for cell in record["cells"]:
        path = output / "cells" / cell["id"] / "record.json"
        if not path.exists():
            continue
        value = json.loads(path.read_text())
        metrics = value["summary"]["metrics"]
        common = {
            "cell": cell["id"],
            "method": cell["method"],
            "mode": cell["mode"],
            "seed": cell["seed"],
            "rms_m": cell["rms_m"],
            "lag1_correlation": cell["error"]["lag1_correlation"],
            "elapsed_seconds": value["elapsed_seconds"],
        }
        if cell["method"] in ("dufomap", "beautymap"):
            common.update({k: metrics[k] for k in ("SA", "DA", "AA", "HA")})
            direct = value["summary"].get("direct_point_metrics")
            if direct:
                common.update({f"direct_{k}": direct[k] for k in ("SA", "DA")})
        else:
            common.update(
                {
                    k: metrics[k]
                    for k in ("query_hit_fraction", "target_recovery_fraction", "mean_best_surface_coverage")
                }
            )
            common["objects"] = value["summary"]["objects"]
        measured.append(common)
    keys = sorted(set().union(*(row.keys() for row in measured)))
    with (output / "cells.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows(measured)
    complete = len(measured) == len(record["cells"])
    record.update(
        status="executed" if complete else "partial",
        finished_at=utc_now(),
        completed_cells=len(measured),
        exit_code=0,
        summary={"cells": measured, "scope": record["protocol"]["scope"]},
    )
    record["executed_cell_script_sha256"] = sorted(
        {
            json.loads((output / "cells" / cell["id"] / "record.json").read_text())["script_sha256"]
            for cell in record["cells"]
            if (output / "cells" / cell["id"] / "record.json").is_file()
        }
    )
    record["implementation_amendment"] = (
        "CLI threshold parsing preserves JSON integer type for DUFOMap's uint d_p. Primary cells have no threshold override; original code snapshot and each actual cell script hash are retained."
    )
    for path in output.rglob("*"):
        if not path.is_file() or "cells" in path.relative_to(output).parts or path == output / "record.json":
            continue
        relative = path.relative_to(output).as_posix()
        record["artifacts"][relative] = {
            "sha256": digest(path),
            "bytes": path.stat().st_size,
            "availability": "local_only" if path.suffix == ".npy" else "portable",
        }
    write_json(output / "record.json", record)
    print(
        f"Paired suite: {record['status']}, {len(measured)}/{len(record['cells'])} cells -> {output}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
