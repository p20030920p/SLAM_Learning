"""Validate corrected distance-log summaries in native desktop demonstrations."""
import math
import json
from pathlib import Path

import numpy as np


def distance_summary(path: Path) -> dict:
    values = np.loadtxt(path, ndmin=1)
    if len(values) < 2 or not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("Native distance log is empty, negative or nonfinite")
    return {"position_rmse_cells": float(np.sqrt(np.mean(values**2))),
            "final_error_cells": float(values[-1]), "updates": len(values)}


def verify_author_demo(path, record):
    if record.get("live_state"):
        try:
            events = [json.loads(line) for line in (path.parent / "live-events.jsonl").read_text().splitlines()]
            shown = [json.loads(line) for line in (path.parent / "live-published.jsonl").read_text().splitlines()]
            execution = json.loads((path.parent / "execution.json").read_text())
            if len(events) < 10 or len(shown) < 8 or not all(row["method"] == record["method"] for row in events+shown):
                raise ValueError("Too few live states or wrong method")
            if any(a["serial"] >= b["serial"] or a["frame"] >= b["frame"] for a, b in zip(events, events[1:])):
                raise ValueError("Native live states are not chronological")
            if all("monotonic_s" in row for row in events) and any(a["monotonic_s"] > b["monotonic_s"] for a, b in zip(events, events[1:])):
                raise ValueError("Native monotonic clock moved backwards")
            native = {row["serial"]: row for row in events}
            for row in shown:
                if row["sha256"] != native[row["serial"]]["sha256"] or row["frame"] != native[row["serial"]]["frame"]:
                    raise ValueError("RViz displayed states from another execution")
                # WSL wall clocks can be corrected while running; causal frame/serial order is authoritative.
                if row["wall_unix"] < execution["started_unix"]-2 or row["wall_unix"] > row["published_unix"]+2:
                    raise ValueError("Old states were shown as live execution")
                if "monotonic_s" in row and "published_monotonic_s" in row and row["monotonic_s"] > row["published_monotonic_s"]:
                    raise ValueError("State was published before it was produced")
            if events[-1]["wall_unix"] > execution["finished_unix"]:
                raise ValueError("Snapshots were produced after native execution finished")
        except (OSError, ValueError, KeyError, TypeError) as error:
            return [f"Author live display: {error}"]
    if record.get("method") != "adam-mcl":
        return []
    errors = []
    try:
        actual = distance_summary(path.parent / "error_position.txt")
        for name, value in actual.items():
            if not math.isclose(value, record["metrics"][name], abs_tol=1e-10, rel_tol=0):
                errors.append(f"AdaM-MCL: {name} differs from saved Euclidean distance logs")
        if record["metrics"].get("paper_comparison") is not False:
            errors.append("Surrogate AdaM-MCL trial cannot claim paper numeric comparison")
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append(f"AdaM-MCL desktop evidence: {error}")
    return errors
