from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from slam_learning.core.provenance import environment


def find_root(value: str | None) -> Path:
    if value:
        root = Path(value).resolve()
    else:
        root = Path.cwd().resolve()
        while not (root / "configs/methods.json").is_file():
            if root == root.parent:
                raise ValueError("Run from the repository checkout or pass --root")
            root = root.parent
    if not (root / "configs/methods.json").is_file():
        raise ValueError(f"No experiment configuration at {root}")
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evidence-first SLAM/semantic mapping experiments")
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("doctor", "fetch", "run", "report", "verify", "export", "cross-check", "render-reproduction", "_worker"):
        p = sub.add_parser(action)
        p.add_argument("--root")
        if action == "cross-check":
            p.add_argument("records", nargs="+", help="Complete author-method record.json paths")
            p.add_argument("--timeout", type=float, default=3600)
        if action == "render-reproduction":
            p.add_argument("record", help="Completed evaluator cross-check record")
        if action == "fetch":
            p.add_argument("--direct", action="store_true", help="Bypass broken proxy only for these fetches")
        if action in ("run", "_worker"):
            p.add_argument("--method", choices=("dufomap", "beautymap"), required=action == "_worker")
            p.add_argument("--frames", type=int, default=0, help="0=full teaser; positive=smoke, no paper score")
        if action == "run":
            p.add_argument("--experiment", choices=("mechanism", "pose-stress", "evidence-stress", "api-check"))
            p.add_argument("--timeout", type=float, default=3600)
            p.add_argument("--strict-paper", action="store_true", help="Exit nonzero on paper mismatch")
        if action == "_worker":
            p.add_argument("--output", required=True)
        if action == "report":
            p.add_argument("--runs", default="results/reference")
            p.add_argument("--output", default="results/REPORT.md")
            p.add_argument("--lang", choices=("en", "zh"), default="en")
        if action == "verify":
            p.add_argument("record")
            p.add_argument("--full", action="store_true")
        if action == "export":
            p.add_argument("record")
            p.add_argument("--name", required=True)
    args = parser.parse_args(argv)
    try:
        root = find_root(args.root)
        if args.action == "doctor":
            print(json.dumps({**environment(), "root": str(root), "git": shutil.which("git"),
                  "verified_dataset": (root / ".cache/datasets/00/provenance.json").exists(),
                  "nvidia_smi": shutil.which("nvidia-smi"),
                  "note": "CUDA is optional for the active CPU experiments; capability is detected, not hardcoded."}, indent=2))
        elif args.action == "fetch":
            from slam_learning.runtime.fetch import fetch
            fetch(root, args.direct)
        elif args.action == "_worker":
            from slam_learning.runtime.adapters import worker
            worker(root, args.method, Path(args.output).resolve(), args.frames)
        elif args.action == "run":
            if bool(args.method) == bool(args.experiment):
                parser.error("Choose exactly one of --method and --experiment")
            if args.experiment:
                if args.frames or args.strict_paper:
                    parser.error("--frames/--strict-paper only apply to author methods")
                if args.experiment == "mechanism":
                    from slam_learning.experiments.synthetic import run_synthetic
                    run_synthetic(root)
                elif args.experiment == "evidence-stress":
                    from slam_learning.experiments.evidence_stress import run_evidence_stress
                    run_evidence_stress(root)
                elif args.experiment == "api-check":
                    from slam_learning.experiments.api_check import run_api_check
                    record_path = run_api_check(root, args.timeout)
                    return int(json.loads(record_path.read_text(encoding="utf-8"))["status"] != "executed")
                else:
                    from slam_learning.experiments.pose_stress import run_pose_stress
                    record_path = run_pose_stress(root)
                    return int(json.loads(record_path.read_text(encoding="utf-8"))["status"] != "executed")
            else:
                from slam_learning.runtime.runner import run_method
                record_path = run_method(root, args.method, args.frames, args.timeout)
                record = json.loads(record_path.read_text(encoding="utf-8"))
                if record["status"] in ("failed", "blocked"):
                    return 1
                if args.strict_paper and (not record.get("paper_comparison") or not record["paper_comparison"]["matched"]):
                    return 2
        elif args.action == "cross-check":
            from slam_learning.experiments.evaluation_check import run_evaluation_check
            records = [Path(p) if Path(p).is_absolute() else root / p for p in args.records]
            path = run_evaluation_check(root, records, args.timeout)
            return int(json.loads(path.read_text(encoding="utf-8"))["status"] != "executed")
        elif args.action == "render-reproduction":
            from slam_learning.visualization.render_reproduction import render_reproduction
            value = Path(args.record)
            path = render_reproduction(root, value if value.is_absolute() else root / value)
            return int(json.loads(path.read_text(encoding="utf-8"))["status"] != "executed")
        elif args.action == "verify":
            from slam_learning.runtime.runner import verify_record
            path = Path(args.record)
            errors = verify_record(path if path.is_absolute() else root / path, args.full)
            print("\n".join(errors) if errors else "Evidence integrity verified" + (" (including local maps)" if args.full else " (portable files)"))
            return int(bool(errors))
        elif args.action == "export":
            from slam_learning.runtime.runner import export_record
            if not args.name or Path(args.name).name != args.name or args.name in (".", "..") or ":" in args.name:
                raise ValueError("Export name must be one directory component")
            path = Path(args.record)
            export_record(path if path.is_absolute() else root / path, root / "results/reference" / args.name)
            print(root / "results/reference" / args.name)
        elif args.action == "report":
            from slam_learning.visualization.report import render_report
            runs = Path(args.runs)
            runs = runs if runs.is_absolute() else root / runs
            paths = list(runs.glob("*/record.json"))
            if not paths:
                raise ValueError(f"No run records under {runs}")
            output = Path(args.output)
            output = output if output.is_absolute() else root / output
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(render_report(paths, output.parent, args.lang), encoding="utf-8")
            print(output)
        return 0
    except (ValueError, OSError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
