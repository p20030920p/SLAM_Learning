"""Portable common-point audit of every retained single-factor map experiment."""
import argparse
import json
import shutil
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from slam_learning.core.provenance import digest
from slam_learning.runtime.map_point_audit import retention_score
from slam_learning.runtime.runner import verify_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if (args.output / "record.json").exists():
        raise ValueError("An executed audit already exists; choose a new output")
    args.output.mkdir(parents=True, exist_ok=True)
    source = args.baseline / "point-label-inputs.npz"
    shutil.copyfile(source, args.output / source.name)
    with np.load(source, allow_pickle=False) as data:
        raw, labels = data["points"], data["labels"]
    configurations = {}
    for name, maps in [("baseline", args.baseline), *[(name, args.run / ("ablation-"+name))
                         for name in ("visibility12", "allscans", "dufo02", "beautyz05")]]:
        folder = args.output / name
        folder.mkdir(exist_ok=True)
        masks, metrics, source_hashes = {}, {}, {}
        native_input = np.load(maps / "raw/points.npy", allow_pickle=False)
        for method in ("raw", "dufomap", "beautymap"):
            output = maps / method / "points.npy"
            points = np.load(output, allow_pickle=False)
            tree = cKDTree(points)
            if (tree.query(native_input, workers=2)[0] < 2e-5).sum() != len(points):
                raise ValueError("Native output does not preserve exact source point multiplicity")
            masks[method] = tree.query(raw, workers=2)[0] < 2e-5
            metrics[method] = retention_score(labels, masks[method])
            source_hashes[method] = {"path": str(output.resolve()), "sha256": digest(output)}
        np.savez_compressed(folder / "retention-masks.npz", **masks)
        shutil.copyfile(maps / "record.json", folder / "processing-source.json")
        processing = json.loads((maps / "record.json").read_text())
        if "parameters" not in processing:
            beauty = json.loads((maps / "beautymap-native/record.json").read_text())["parameters"]
            processing["parameters"] = {"dufo_resolution": .1, "dufo_ds": .2, "dufo_dp": 1,
                                        "beauty_range": beauty["dis_range"], "beauty_xy": beauty["xy_resolution"],
                                        "beauty_z": beauty["h_res"]}
            processing["parameters_source"] = "native BeautyMap record and pinned pre-CLI build_maps.py defaults at f415a06; original processing-source.json preserved"
        (folder / "processing.json").write_text(json.dumps(processing, indent=2)+"\n")
        configurations[name] = {"parameters": processing["parameters"], "metrics": metrics,
                                "source_outputs": source_hashes, "source_scan_count": len(processing["selected_scan_ids"])}
        for method in ("dufomap", "beautymap"):
            log = maps / f"{method}-native/native.log"
            if log.is_file():
                shutil.copyfile(log, folder / (method+".log"))
        shutil.copyfile(maps / "beautymap-native/compatibility.patch", folder / "beautymap-compatibility.patch")
    for name in ("object-geometry.json", "object-scene.pbtxt"):
        shutil.copyfile(args.run / name, args.output / name)
    shutil.copyfile(args.baseline / "point-label-scores.json", args.output / "baseline-geometry-score.json")
    record = {"schema_version": 1, "kind": "native_map_point_audit", "status": "executed", "exit_code": 0,
              "configurations": configurations,
              "scored_static_points": int((labels == 0).sum()), "scored_dynamic_points": int((labels == 1).sum()),
              "ambiguous_points": int((labels < 0).sum()),
              "scope": "every configuration scored on the identical 60-scan baseline points; simulator moving-box labels; 2cm surface tolerance, 5cm ambiguous shell, self-return exclusion .45m; not paper benchmark ground truth",
              "source_run": str(args.run.resolve()), "source_input_hashes": json.loads((args.baseline / "point-label-scores.json").read_text())["inputs"],
              "truth_input_to_held_out_localizers": False,
              "artifacts": {p.relative_to(args.output).as_posix(): {"sha256": digest(p), "bytes": p.stat().st_size, "availability": "portable"}
                            for p in args.output.rglob("*") if p.is_file()}}
    (args.output / "record.json").write_text(json.dumps(record, indent=2)+"\n")
    issues = verify_record(args.output / "record.json")
    if issues:
        raise ValueError(issues)
    print(json.dumps(configurations, indent=2))


if __name__ == "__main__":
    main()
