"""Controlled missing-return map-update replay from the user's actual 2D scene.

This tests unknown/free-space semantics only, not reflection physics/detection.
"""

from pathlib import Path
import hashlib
import json
import sys

import numpy as np
from PIL import Image


def run(source, output):
    output.mkdir(parents=True, exist_ok=False)
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    # Fixed-pose update isolates validity semantics from robot/mapper motion.
    row = next(r for r in rows if np.count_nonzero(np.array(r["ranges"]) > 0.45) > 200)
    ranges = np.asarray(row["ranges"])
    angles = row["angle_min"] + np.arange(len(ranges)) * row["angle_increment"]
    valid = (ranges > 0.45) & (ranges < 12) & np.isfinite(ranges)
    missing = valid & (angles > -0.6) & (angles < 0.6)
    assert missing.sum() > 20
    resolution = 0.05
    origin = np.array([-13.0, -13.0])
    shape = (521, 521)
    endpoint = np.column_stack((ranges * np.cos(angles), ranges * np.sin(angles)))
    ids = np.floor((endpoint[valid] - origin) / resolution).astype(int)
    baseline = np.zeros(shape, bool)
    baseline[ids[:, 1], ids[:, 0]] = True
    reference = np.zeros(shape, bool)
    mid = np.floor((endpoint[missing] - origin) / resolution).astype(int)
    reference[mid[:, 1], mid[:, 0]] = True
    maps = {"unknown": baseline.copy(), "incorrect_free": baseline.copy()}
    frames = []
    history = []
    for update in range(21):
        if update:
            for angle in angles[missing]:
                distances = np.arange(0, 12, resolution / 2)
                xy = np.column_stack((distances * np.cos(angle), distances * np.sin(angle)))
                cells = np.floor((xy - origin) / resolution).astype(int)
                maps["incorrect_free"][cells[:, 1], cells[:, 0]] = False
        metrics = {
            n: {
                "wrongly_cleared_boundary_cells": int(np.sum(reference & ~m)),
                "reference_boundary_cells": int(reference.sum()),
                "boundary_retention": float(np.sum(reference & m) / reference.sum()),
            }
            for n, m in maps.items()
        }
        history.append({"update": update, "metrics": metrics})
        images = []
        for n, m in maps.items():
            rgb = np.full((*shape, 3), 225, np.uint8)
            rgb[baseline] = [155, 155, 155]
            rgb[m] = [25, 60, 70]
            rgb[reference & ~m] = [235, 55, 55]
            images.append(Image.fromarray(np.flipud(rgb)))
        from PIL import ImageDraw

        canvas = Image.new("RGB", (1042, 590), "white")
        canvas.paste(images[0], (0, 60))
        canvas.paste(images[1], (521, 60))
        draw = ImageDraw.Draw(canvas)
        draw.text(
            (10, 6),
            "E3a measured-scan replay | controlled missing returns | NOT mirror physics",
            fill="black",
        )
        for i, (n, m) in enumerate(metrics.items()):
            draw.text(
                (i * 521 + 10, 25),
                f"{n} | update={update} | boundary retained={m['boundary_retention'] * 100:.1f}%",
                fill="black",
            )
        frames.append(canvas)
    frames[0].save(
        output / "control-replay.gif", save_all=True, append_images=frames[1:], duration=300, loop=0
    )
    frames[-1].save(output / "result.png")
    np.savez_compressed(output / "inputs.npz", ranges=ranges, angles=angles, valid=valid, missing=missing)
    (output / "updates.json").write_text(json.dumps(history, indent=2) + "\n")
    record = {
        "schema_version": 1,
        "kind": "controlled_missing_return_semantics",
        "status": "executed",
        "exit_code": 0,
        "scope": "Fixed-pose replay of one real Gazebo 2D scan; synthetic angular dropout, no physical mirror model or detector; no localization claim",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_record": str(source),
        "masked_beams": int(missing.sum()),
        "resolution_m": resolution,
        "metrics": history[-1]["metrics"],
        "reference": "Observed real boundary endpoints in the masked sector, not hidden truth",
        "artifacts": {
            p.name: {
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "bytes": p.stat().st_size,
                "availability": "portable",
            }
            for p in output.iterdir()
            if p.is_file()
        },
    }
    (output / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record["metrics"]))


if __name__ == "__main__":
    run(Path(sys.argv[1]), Path(sys.argv[2]))
