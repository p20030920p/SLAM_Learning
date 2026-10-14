"""Export each saved native AMCL case at the original common simulation interval."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from package_session import gif, probe, replay
from slam_learning.core.provenance import digest
from slam_learning.runtime.presentation_evidence import read_samples, score
from slam_learning.runtime.runner import verify_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parents", nargs="+", type=Path)
    args = parser.parse_args()
    for parent in args.parents:
        source = parent / "record.json"
        issues = verify_record(source)
        if issues:
            raise ValueError(issues)
        record = json.loads(source.read_text(encoding="utf-8"))
        cases = json.loads((parent / "cases.json").read_text(encoding="utf-8"))
        interval = [record["result_replay"][key] for key in ("common_start_s", "common_end_s")]
        for name, case in cases.items():
            output = parent / "methods" / name
            if (output / "record.json").exists():
                issues = verify_record(output / "record.json")
                if issues:
                    raise ValueError(issues)
                print(f"Already verified: {output}", flush=True)
                continue
            output.mkdir(parents=True, exist_ok=True)
            values = read_samples(parent / f"{name}-samples.csv")
            restore = record.get("restoration", {}).get(name, {}).get("restore_stamp_s")
            label = {"raw": "Raw map", "dufomap": "DUFOMap map", "beautymap": "BeautyMap map"}[case["method"]]
            limited = name.startswith("degraded_")
            subtitle = f"{parent.name} | {label} | AMCL"
            if name.startswith("clean_"):
                subtitle += " | static-map control"
            elif parent.name == "robot-degradation" and not limited:
                subtitle += " | full-scan control"
            replay_meta = replay(parent, {name: values}, restore if limited else None,
                                 output_folder=output, heading_label=subtitle, interval=interval)
            timing = gif(output / "result.mp4", output / "result.gif")
            subprocess.run(["ffmpeg", "-v", "error", "-i", str(output / "result.mp4"), "-f", "null", "-"], check=True)
            duration = float(probe(output / "result.mp4")["format"]["duration"])
            subprocess.run(["ffmpeg", "-v", "error", "-ss", str(duration/2), "-i", str(output / "result.mp4"),
                            "-frames:v", "1", "-y", str(output / "frame-mid.png")], check=True)
            inputs = [f"{name}-samples.csv", "truth.jsonl", "cases.json", "metrics.json",
                      f"maps/{name}/map.pgm", f"maps/{name}/map.yaml"]
            if restore is not None:
                inputs.append("scan-stress.jsonl")
            child = {"schema_version": 1, "kind": "native_case_replay", "status": "executed", "exit_code": 0,
                     "case": name, "parent_record": "../../record.json", "parent_sha256": digest(source),
                     "source_run": record["source_run"], "case_configuration": case,
                     "scope": "Single-case rendering of saved native AMCL poses; shared live execution; no new inference",
                     "metrics": score(values), "result_replay": replay_meta, "timing": timing,
                     "restoration": record.get("restoration", {}).get(name),
                     "source_inputs": {part: digest(parent / part) for part in inputs},
                     "command": "python src/scripts/presentation/package_case_replays.py " + parent.as_posix(),
                     "renderer_sha256": digest(Path(__file__).with_name("package_session.py")),
                     "artifacts": {p.name: {"sha256": digest(p), "bytes": p.stat().st_size, "availability": "portable"}
                                   for p in output.iterdir() if p.is_file()}}
            (output / "record.json").write_text(json.dumps(child, indent=2)+"\n", encoding="utf-8")
            issues = verify_record(output / "record.json")
            if issues:
                raise ValueError(issues)
            print(f"Exported: {output} ({child['metrics']['samples']} native updates)", flush=True)


if __name__ == "__main__":
    main()
