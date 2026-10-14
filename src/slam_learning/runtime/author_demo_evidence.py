"""Validate corrected distance-log summaries in native desktop demonstrations."""
import math
from pathlib import Path

import numpy as np


def distance_summary(path: Path) -> dict:
    values = np.loadtxt(path, ndmin=1)
    if len(values) < 2 or not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("Native distance log is empty, negative or nonfinite")
    return {"position_rmse_cells": float(np.sqrt(np.mean(values**2))),
            "final_error_cells": float(values[-1]), "updates": len(values)}


def verify_author_demo(path, record):
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
