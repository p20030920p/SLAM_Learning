"""Run the released AdaM_MCL global-localization / kidnapping evaluation live.

The released entry point is

    python Main.py --operation test_MCL --dataset simulation --subdataset <n> \
        --update_mode Adaptive_Mixture_MCL --w_cut 0.6 --particle_num <n> --load_model <file>

This wrapper runs exactly that command as a child process and keeps its complete,
unfiltered stdout in a log file. On the terminal it shows a live dashboard of the
values that same child prints -- the particle-overlay PNG the released
Global_Localization_Interface writes before every filter update, rendered as ANSI
half-blocks, plus the ground truth, estimate, squared position error and update
time parsed from the child's own output. Nothing is invented here: the numbers on
the dashboard are the released program's numbers, and the log file retains all of
them verbatim.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import cv2
import numpy as np

ANSI = re.compile(r"\x1b\[[0-9;]*m")
NUMBER = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")
BLOCK = "\u2580"


def numbers(text: str) -> float | None:
    """Last number on a released output line (values are printed inside array brackets)."""
    found = NUMBER.findall(text.split(":", 1)[-1])
    return float(found[-1]) if found else None


def ansi_frame(image: np.ndarray, columns: int, rows: int) -> str:
    """Render a BGR image as `rows` pixels tall using terminal half-blocks."""
    resized = cv2.resize(image, (columns, rows), interpolation=cv2.INTER_AREA)
    resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.int16)
    lines = []
    for top in range(0, rows - 1, 2):
        upper, lower = resized[top], resized[top + 1]
        cells = []
        for column in range(columns):
            up, down = upper[column], lower[column]
            cells.append(
                f"\x1b[38;2;{up[0]};{up[1]};{up[2]}m\x1b[48;2;{down[0]};{down[1]};{down[2]}m{BLOCK}"
            )
        lines.append("".join(cells) + "\x1b[0m")
    return "\n".join(lines)


class Dashboard(threading.Thread):
    def __init__(self, root: Path, columns: int, rows: int, interval: float, trials: int) -> None:
        super().__init__(daemon=True)
        self.root = root
        self.columns = columns
        self.rows = rows
        self.interval = interval
        self.trials = trials
        self.stop = threading.Event()
        self.seen: set[str] = set()
        self.lock = threading.Lock()
        self.state: dict[str, str] = {
            "trial": "1", "iteration": "-", "frames": "-",
            "truth": "-", "estimate": "-", "error": "-", "weight": "-", "cost": "-",
        }
        self.view = "waiting for the first particle frame"
        self.frame = ""
        self.rendered = 0

    def observe(self, key: str, value: str) -> None:
        with self.lock:
            self.state[key] = value

    def draw(self, subtitle: str) -> None:
        with self.lock:
            state = dict(self.state)
            header = (f"AdaM_MCL  adaptive mixture MCL  |  released Main.py --operation test_MCL  |  "
                      f"trial {state['trial']}/{self.trials}  update {state['iteration']}")
            lines = [
                "\x1b[2J\x1b[H",
                "\x1b[1m" + header + "\x1b[0m",
                subtitle,
                self.frame,
                "",
                f"ground truth  {state['truth']}",
                f"estimate      {state['estimate']}",
                f"squared position error  {state['error']} px^2     "
                f"weight {state['weight']}     update time {state['cost']} s",
                "green = particles (brightness is particle weight), red square = ground truth; "
                "the released code writes this frame before every filter update",
            ]
        print("\n".join(lines), flush=True)

    def run(self) -> None:
        while not self.stop.is_set():
            newest = None
            for path in self.root.glob("**/*_th_iter.png"):
                if str(path) in self.seen:
                    continue
                if newest is None or path.stat().st_mtime > newest.stat().st_mtime:
                    newest = path
            if newest is not None:
                self.seen.add(str(newest))
                image = cv2.imread(str(newest))
                if image is not None:
                    self.frame = ansi_frame(image, self.columns, self.rows)
                    self.rendered += 1
                    self.draw(f"frame {newest.stem} from {newest.parent.name[:64]}")
                self.stop.wait(self.interval)
            else:
                self.stop.wait(self.interval)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True)
    parser.add_argument("--subdataset", default="1")
    parser.add_argument("--particles", type=int, default=200)
    parser.add_argument("--w-cut", default="0.6")
    parser.add_argument("--model", required=True)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--columns", type=int, default=84)
    parser.add_argument("--rows", type=int, default=78)
    parser.add_argument("--view-interval", type=float, default=0.02)
    parser.add_argument("--trials", type=int, default=100)
    args = parser.parse_args()

    command = [
        args.python, "Main.py", "--operation", "test_MCL", "--dataset", "simulation",
        "--subdataset", args.subdataset, "--update_mode", "Adaptive_Mixture_MCL",
        "--w_cut", args.w_cut, "--particle_num", str(args.particles),
        "--load_model", args.model,
    ]
    print("AdaM_MCL reproduction: released global-localization / kidnapping evaluation")
    print("$ " + " ".join(command))
    print(f"ADAM_MCL_TRIALS={args.trials}  complete unfiltered output -> {args.log.resolve()}")
    print("the terminal view below is a live dashboard of the released program's own output")
    sys.stdout.flush()
    time.sleep(2)

    dashboard = Dashboard(Path("logs4MCL"), args.columns, args.rows, args.view_interval, args.trials)
    dashboard.start()

    environment = dict(os.environ, ADAM_MCL_TRIALS=str(args.trials), PYTHONUNBUFFERED="1")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, bufsize=1, env=environment)
    trial = 0
    started = time.monotonic()
    with args.log.open("w") as log:
        log.write("# " + " ".join(command) + "\n")
        log.write(f"# ADAM_MCL_TRIALS={args.trials}\n")
        for line in process.stdout:
            log.write(line)
            stripped = ANSI.sub("", line).strip()
            if stripped.startswith("Update Iteration"):
                iteration = int(re.search(r"(\d+)", stripped).group(1))
                if iteration == 1:
                    trial += 1
                    dashboard.observe("trial", str(trial))
                dashboard.observe("iteration", str(iteration))
            elif stripped.startswith("Ground truth:"):
                dashboard.observe("truth", stripped.split(":", 1)[1].strip())
            elif stripped.startswith("Estimation:"):
                dashboard.observe("estimate", stripped.split(":", 1)[1].strip())
            elif stripped.startswith("Error in position:"):
                value = numbers(stripped)
                dashboard.observe("error", f"{value:.4f}" if value is not None else "-")
            elif stripped.startswith("Weight of estimation:"):
                dashboard.observe("weight", stripped.split(":", 1)[1].strip())
            elif stripped.startswith("Time cost:"):
                value = numbers(stripped)
                dashboard.observe("cost", f"{value:.4f}" if value is not None else "-")
    code = process.wait()
    dashboard.stop.set()
    dashboard.join(timeout=5)
    elapsed = time.monotonic() - started
    print(f"\nreleased command finished: exit {code}; elapsed {elapsed:.1f}s; "
          f"particle frames rendered {dashboard.rendered}", flush=True)

    errors = []
    for path in sorted(Path("logs4MCL").glob("**/error_position.txt")):
        values = np.loadtxt(path, ndmin=1)
        errors.append(math.sqrt(float(np.mean(values))))
    if errors:
        errors = np.array(errors)
        print(f"trials with saved logs: {len(errors)}  final position RMSE over trials: "
              f"mean {errors.mean():.3f} px  median {np.median(errors):.3f} px  "
              f"min {errors.min():.3f} px  max {errors.max():.3f} px", flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
