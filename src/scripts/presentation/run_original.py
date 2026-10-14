"""Execute author entry points in fresh output trees; never overwrite sealed runs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path


def sha(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("method", choices=["dufomap", "beautymap", "ir-mcl", "adam-mcl"])
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    run = args.run
    run.mkdir(parents=True, exist_ok=True)
    repo = Path(__file__).resolve().parents[3]
    started = time.time()
    manifest = {"method": args.method, "kind": "author_desktop_execution", "started_unix": started,
                "capture": "actual Windows Terminal window", "status": "running",
                "wrapper_sha256": sha(Path(__file__)), "sources": {}, "artifacts": {}}
    (run / "ready.json").write_text(json.dumps({"state": "READY_FOR_CAPTURE"}))
    while not (run / "recording.started").exists():
        if time.time() - started > 180:
            raise TimeoutError("Desktop capture did not start")
        time.sleep(.1)
    print(f"AUTHOR EXECUTION: {args.method}; fresh outputs: {run}", flush=True)
    code = 0
    try:
        if args.method in ("dufomap", "beautymap"):
            sys.path.insert(0, str(repo / "src"))
            os.environ["PYTHONPATH"] = str(repo / "src")
            from slam_learning.runtime.runner import run_method
            root = run / "experiment"
            root.mkdir()
            (root / "src").symlink_to(repo / "src", target_is_directory=True)
            (root / ".cache").symlink_to(Path("/home/qzl/projects/SLAM_Learning/.cache"), target_is_directory=True)
            seen = set()
            halt = threading.Event()

            def echo_log():
                offsets = {}
                while not halt.wait(.2):
                    for path in root.glob(f"results/runs/{args.method}-*/run.log"):
                        if path.stat().st_mtime < started:
                            continue
                        seen.add(path.parent)
                        with path.open(errors="replace") as stream:
                            stream.seek(offsets.get(path, 0))
                            data = stream.read()
                            offsets[path] = stream.tell()
                        if data:
                            print(data, end="", flush=True)

            watcher = threading.Thread(target=echo_log, daemon=True)
            watcher.start()
            record = run_method(root, args.method, timeout=1800)
            halt.set()
            watcher.join(timeout=2)
            native = json.loads(record.read_text())
            if native["status"] != "executed":
                raise RuntimeError(native.get("error", native["status"]))
            shutil.copytree(record.parent, run / "native-run")
            manifest["native_record"] = "native-run/record.json"
            manifest["metrics"] = native["metrics"]
            manifest["scope"] = "141 released KITTI-00 scans, pinned author pipeline; paper comparison as native record"
            manifest["command"] = native["command"]
            manifest["dataset"] = native["dataset"]
        elif args.method == "ir-mcl":
            source = Path("/mnt/d/workspace/be2/tmp/repro/ir-mcl")
            work = run / "author-code"
            shutil.copytree(source, work, ignore=shutil.ignore_patterns(".git", "data", "results", "__pycache__"))
            (work / "data").symlink_to(source / "data", target_is_directory=True)
            manifest["sources"][str(source / "config/global_localization/loc_config_test1.yml")] = sha(source / "config/global_localization/loc_config_test1.yml")
            command = [str(Path.home() / ".venvs/ir-mcl/bin/python"), "-u", "main.py", "--config_file", "./config/global_localization/loc_config_test1.yml"]
            env = dict(os.environ, PYTHONPATH=f"{work}/mcl/srrg_utils:{work}/mcl", MPLBACKEND="Agg")
            manifest["scope"] = "released Bonn IPBLab sequence; native config and 100000 initial particles; fresh inference"
            code = execute(command, work, env, run / "native-output.log")
            manifest["command"] = command
        else:
            source = Path("/mnt/d/workspace/be2/tmp/repro/AdaM_MCL")
            work = run / "AdaM_MCL"
            work.mkdir()
            code_dir = work / "Code"
            shutil.copytree(source / "Code", code_dir, ignore=shutil.ignore_patterns("Dataset", "logs4MCL", "__pycache__", ".git"))
            dashboard = code_dir / "repro/live_eval.py"
            original_dashboard = dashboard.read_text()
            corrected_dashboard = original_dashboard.replace("math.sqrt(float(np.mean(values)))", "math.sqrt(float(np.mean(values ** 2)))")
            dashboard.write_text(corrected_dashboard)
            manifest["dashboard_metrics_note"] = "Wrapper footer corrected: native error_position.txt stores Euclidean distances, not squared errors; author filter unchanged"
            for target in (work / "Dataset", code_dir / "Dataset"):
                target.symlink_to(source / "Dataset", target_is_directory=True)
            model = sorted((source / "Trained_models").glob("simulation_2_*/model_train_38epochs.pth"))[0]
            trials = int(os.environ.get("ADAM_TRIALS", "10"))
            command = [str(Path.home() / ".venvs/adam-mcl/bin/python"), "-u", "repro/live_eval.py", "--python", str(Path.home() / ".venvs/adam-mcl/bin/python"), "--subdataset", "0", "--particles", "200", "--model", str(model), "--trials", str(trials), "--log", str(run / "native-output.log")]
            manifest["sources"][str(model)] = sha(model)
            manifest["scope"] = f"author code; authored 128-cell surrogate; existing 2432-step checkpoint; fresh 123-update x {trials}-trial inference; no paper numeric comparison"
            code = execute(command, code_dir, dict(os.environ, MPLBACKEND="Agg"), run / "dashboard.log")
            manifest["command"] = command
        if code:
            raise RuntimeError(f"Author entry point exited {code}")
        manifest["status"] = "executed"
    except Exception as error:
        manifest.update(status="failed", error=f"{type(error).__name__}: {error}")
        code = code or 1
    finally:
        manifest.update(exit_code=code, finished_unix=time.time(), wall_seconds=time.time()-started)
        for path in run.rglob("*"):
            if path.is_file() and path.suffix in (".txt", ".log", ".json", ".npz") and "author-code" not in path.parts and path.name != "terminal.log":
                manifest["artifacts"][path.relative_to(run).as_posix()] = {"sha256": sha(path), "bytes": path.stat().st_size}
        (run / "execution.json").write_text(json.dumps(manifest, indent=2)+"\n")
        print(json.dumps(manifest, indent=2), flush=True)
        (run / ("finished.json" if not code else "failed.json")).write_text(json.dumps({"exit_code": code, "status": manifest["status"]}))
    return code


def execute(command, work, env, logfile):
    print("EXECUTING: " + " ".join(command), flush=True)
    with logfile.open("w") as log:
        child = subprocess.Popen(command, cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in child.stdout:
            print(line, end="", flush=True)
            log.write(line)
            log.flush()
        return child.wait()


if __name__ == "__main__":
    raise SystemExit(main())
