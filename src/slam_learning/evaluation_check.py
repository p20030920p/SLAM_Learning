"""Cross-check saved author maps with the unmodified benchmark PCL evaluator."""
from __future__ import annotations

import csv
import json
import shlex
import shutil
import subprocess
import traceback
import uuid
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from .metrics import confusion_metrics
from .pcd import read_pcd
from .provenance import digest, environment, git_state, source_hashes, utc_now, write_json
from .runner import MissingRequirement, execute, validate_inputs, verify_record


def pcl_modules() -> list[str]:
    names = {line.split()[0] for line in subprocess.check_output(
        ["pkg-config", "--list-all"], text=True).splitlines() if line.strip()}
    result = []
    for prefix in ("pcl_io", "pcl_kdtree"):
        candidates = sorted(name for name in names if name == prefix or name.startswith(prefix + "-"))
        if not candidates:
            raise MissingRequirement(f"Missing {prefix} pkg-config metadata; install libpcl-dev")
        result.append(prefix if prefix in candidates else candidates[-1])
    return result


def check_point_order(gt, prediction) -> None:
    if len(gt.records) != len(prediction.records):
        raise ValueError("PCL export changed the GT point count")
    for start in range(0, len(gt.records), 250_000):
        selection = slice(start, start + 250_000)
        if not np.array_equal(gt.xyz(selection), prediction.xyz(selection)):
            raise ValueError("PCL export changed GT point identity/order")


def run_evaluation_check(root: Path, records: list[Path], timeout: float = 3600) -> Path:
    if not records or timeout <= 0:
        raise ValueError("Provide at least one full author run and a positive timeout")
    output = root / "results/runs" / f"evaluation-check-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True)
    record = {"schema_version": 1, "kind": "map_evaluator_cross_check", "status": "running",
              "scope": "full_teaser", "started_at": utc_now(), "environment": environment(),
              "repository": git_state(root), "source_sha256": source_hashes(root), "artifacts": {},
              "commands": [], "exit_code": None, "threshold_m": 0.05}
    write_json(output / "record.json", record)
    portable = ["build.log", "summary.json", "comparison.csv", "disagreements.csv"]
    local = ["export_eval_pcd"]
    try:
        if not all(shutil.which(tool) for tool in ("g++", "pkg-config")):
            raise MissingRequirement("Linux g++/pkg-config required; install build-essential and libpcl-dev")
        record.update(validate_inputs(root, "dufomap"))
        source = root / ".cache/upstream/dynamicmap/scripts/cpp/export_eval_pcd.cpp"
        record["pcl_source"] = {"path": str(source), "sha256": digest(source),
                                "modification": "none"}
        modules = pcl_modules()
        record["pcl_modules"] = {m: subprocess.check_output(
            ["pkg-config", "--modversion", m], text=True).strip() for m in modules}
        record["compiler"] = subprocess.check_output(["g++", "--version"], text=True)
        flags = shlex.split(subprocess.check_output(["pkg-config", "--cflags", "--libs", *modules], text=True))
        command = ["g++", "-std=c++17", "-O3", str(source), "-o", str(output / "export_eval_pcd"),
                   *flags, "-lglog", "-lgflags"]
        record["commands"].append(command)
        execute(command, root, output / "build.log", timeout)
        gt_path = root / ".cache/datasets/00/gt_cloud.pcd"
        gt = read_pcd(gt_path)
        truth = np.asarray(gt.records["intensity"])
        summaries, rows, differences = [], [], []
        seen = set()
        for path in records:
            issues = verify_record(path, full=True)
            parent = json.loads(path.read_text(encoding="utf-8"))
            if issues or parent.get("kind") != "author_method" or parent.get("status") != "executed":
                raise ValueError(f"Input must be a verified complete author run: {path}; {issues}")
            if parent["dataset"]["archive_sha256"] != record["dataset"]["archive_sha256"]:
                raise ValueError("Input run used a different dataset")
            method = parent["method"]
            if method in seen:
                raise ValueError("Use only one input run per method")
            seen.add(method)
            work = output / method
            work.mkdir()
            (work / "gt_cloud.pcd").symlink_to(gt_path)
            map_path = path.parent / "cleaned.pcd"
            (work / "cleaned.pcd").symlink_to(map_path.resolve())
            name = f"input-{method}-record.json"
            shutil.copy2(path, output / name)
            portable.extend([name, f"{method}/pcl.log"])
            command = [str(output / "export_eval_pcd"), str(work), "cleaned.pcd", "0.05"]
            record["commands"].append(command)
            execute(command, work, work / "pcl.log", timeout)
            predicted_path = work / "eval/cleaned_exportGT.pcd"
            local.append(f"{method}/eval/cleaned_exportGT.pcd")
            pcl = read_pcd(predicted_path)
            check_point_order(gt, pcl)
            pcl_removed = np.asarray(pcl.records["intensity"])
            pcl_metrics = confusion_metrics(truth, pcl_removed)
            xyz = read_pcd(map_path).xyz()
            tree = cKDTree(xyz)
            scipy_removed = np.empty(len(truth), dtype=bool)
            for start in range(0, len(truth), 250_000):
                stop = min(start + 250_000, len(truth))
                points = gt.xyz(slice(start, stop))
                distance = tree.query(points, workers=2)[0]
                labels = distance > record["threshold_m"]
                scipy_removed[start:stop] = labels
                bad = np.flatnonzero(labels != pcl_removed[start:stop])
                for i in bad:
                    differences.append({"method": method, "gt_index": start + int(i),
                        "gt_label": int(truth[start + i]), "pcl_removed": int(pcl_removed[start + i]),
                        "scipy_removed": int(labels[i]), "nearest_distance_m": float(distance[i])})
            scipy_metrics = confusion_metrics(truth, scipy_removed)
            if scipy_metrics["counts"] != parent["metrics"]["counts"]:
                raise ValueError("Current SciPy classification differs from saved input metrics")
            disagreement_count = int(np.count_nonzero(scipy_removed != pcl_removed))
            summary = {"method": method, "input_record_sha256": digest(path),
                       "input_map_sha256": digest(map_path), "exact_point_order_verified": True,
                       "gt_points": len(truth), "disagreement_points": disagreement_count,
                       "scipy": scipy_metrics, "pcl": pcl_metrics,
                       "difference_pp": {k: pcl_metrics[k] - scipy_metrics[k] for k in ("SA", "DA", "AA", "HA")}}
            summaries.append(summary)
            for evaluator, metrics in (("scipy", scipy_metrics), ("author_pcl", pcl_metrics)):
                rows.append({"method": method, "evaluator": evaluator, **metrics["counts"],
                             **{k: metrics[k] for k in ("SA", "DA", "AA", "HA")}})
            del tree, xyz, scipy_removed, pcl_removed
        for name, values, fields in (
            ("comparison.csv", rows, list(rows[0])),
            ("disagreements.csv", differences,
             ["method", "gt_index", "gt_label", "pcl_removed", "scipy_removed", "nearest_distance_m"]),
        ):
            with (output / name).open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(values)
        write_json(output / "summary.json", {"threshold_m": record["threshold_m"], "methods": summaries,
                   "scope": "Same saved maps and GT; evaluator comparison only, not paper-table reconciliation"})
        record.update(status="executed", exit_code=0,
                      methods=summaries, total_disagreement_points=sum(s["disagreement_points"] for s in summaries))
    except MissingRequirement as e:
        record.update(status="blocked", error=str(e))
    except Exception as e:
        record.update(status="failed", error=str(e), traceback=traceback.format_exc())
        if isinstance(e, subprocess.CalledProcessError):
            record["exit_code"] = e.returncode
    finally:
        record["finished_at"] = utc_now()
        for name in portable + local:
            path = output / name
            if path.is_file():
                record["artifacts"][name] = {"sha256": digest(path), "bytes": path.stat().st_size,
                                           "availability": "portable" if name in portable else "local_only"}
        write_json(output / "record.json", record)
    print(f"Evaluator cross-check: {record['status']} -> {output / 'record.json'}", flush=True)
    return output / "record.json"
