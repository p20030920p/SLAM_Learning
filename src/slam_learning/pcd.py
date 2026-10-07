"""Strict binary PCD I/O. Reject unsupported layouts rather than guess their dtype."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Cloud:
    records: np.ndarray
    viewpoint: list[float]

    def xyz(self, selection=slice(None)) -> np.ndarray:
        return np.column_stack([self.records[axis][selection] for axis in ("x", "y", "z")]).astype(np.float32)


def read_pcd(path: Path) -> Cloud:
    metadata = {}
    with path.open("rb") as f:
        for _ in range(100):
            line = f.readline()
            if not line:
                raise ValueError(f"{path}: no DATA header")
            text = line.decode("ascii").strip()
            if not text or text.startswith("#"):
                continue
            key, *values = text.split()
            metadata[key.upper()] = values
            if key.upper() == "DATA":
                offset = f.tell()
                break
        else:
            raise ValueError("PCD header too long")
    if metadata.get("DATA") != ["binary"]:
        raise ValueError("Only uncompressed binary PCD is supported")
    fields = metadata["FIELDS"]
    sizes = list(map(int, metadata["SIZE"]))
    types = metadata["TYPE"]
    counts = list(map(int, metadata.get("COUNT", ["1"] * len(fields))))
    n = int(metadata["POINTS"][0])
    if not (len(fields) == len(sizes) == len(types) == len(counts)) or len(set(fields)) != len(fields):
        raise ValueError("Inconsistent PCD fields")
    if n < 0 or n != int(metadata["WIDTH"][0]) * int(metadata["HEIGHT"][0]):
        raise ValueError("Inconsistent PCD dimensions")
    dtype = []
    for name, size, kind, count in zip(fields, sizes, types, counts):
        if count < 1 or (kind, size) not in {(t, s) for t in ("I", "U") for s in (1, 2, 4, 8)} | {("F", 4), ("F", 8)}:
            raise ValueError("Unsupported PCD dtype")
        scalar = np.dtype(f"<{'f' if kind == 'F' else 'i' if kind == 'I' else 'u'}{size}")
        dtype.append((name, scalar) if count == 1 else (name, scalar, (count,)))
    dtype = np.dtype(dtype)
    if not {"x", "y", "z"}.issubset(fields) or any(counts[fields.index(a)] != 1 for a in ("x", "y", "z")):
        raise ValueError("PCD must contain scalar x,y,z")
    if path.stat().st_size - offset != n * dtype.itemsize:
        raise ValueError("PCD payload length does not match header")
    viewpoint = list(map(float, metadata.get("VIEWPOINT", ["0", "0", "0", "1", "0", "0", "0"])))
    if len(viewpoint) != 7 or not np.isfinite(viewpoint).all():
        raise ValueError("Invalid PCD VIEWPOINT")
    records = np.memmap(path, dtype=dtype, offset=offset, mode="r", shape=(n,)) if n else np.empty(0, dtype=dtype)
    return Cloud(records, viewpoint)


def write_pcd(path: Path, xyz: np.ndarray, labels: np.ndarray | None = None,
              viewpoint: list[float] | None = None) -> None:
    xyz = np.asarray(xyz, dtype="<f4")
    if xyz.ndim != 2 or xyz.shape[1] != 3 or not np.isfinite(xyz).all():
        raise ValueError("xyz must be a finite Nx3 array")
    fields = ["x", "y", "z"] + (["intensity"] if labels is not None else [])
    if labels is not None and np.asarray(labels).shape != (len(xyz),):
        raise ValueError("Label shape mismatch")
    viewpoint = [0, 0, 0, 1, 0, 0, 0] if viewpoint is None else viewpoint
    if len(viewpoint) != 7 or not np.isfinite(viewpoint).all():
        raise ValueError("Invalid PCD VIEWPOINT")
    pose_text = " ".join(str(v) for v in viewpoint)
    values = np.column_stack([xyz, labels]).astype("<f4") if labels is not None else xyz
    header = ("VERSION .7\nFIELDS " + " ".join(fields) + "\nSIZE " + " ".join(["4"] * len(fields))
              + "\nTYPE " + " ".join(["F"] * len(fields)) + "\nCOUNT " + " ".join(["1"] * len(fields))
              + f"\nWIDTH {len(xyz)}\nHEIGHT 1\nVIEWPOINT {pose_text}\nPOINTS {len(xyz)}\nDATA binary\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(header.encode("ascii"))
        f.write(values.tobytes())
