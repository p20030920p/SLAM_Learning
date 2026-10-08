"""Cross-check all paired cells against frozen errors, source bytes and CSV values."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import numpy as np

from slam_learning.paired_pose import paired_translations
from slam_learning.provenance import digest
from slam_learning.runner import verify_record


def main():
    root = Path(__file__).resolve().parents[1] / "results/reference/paired-pose"
    analysis = json.loads((root / "record.json").read_text(encoding="utf-8"))
    assert analysis["status"] == "executed"
    assert not verify_record(root / "record.json")
    suite = json.loads((root / "suite/record.json").read_text(encoding="utf-8"))
    controls = json.loads((root / "controls/record.json").read_text(encoding="utf-8"))
    assert suite["status"] == controls["status"] == "executed"
    assert len(suite["cells"]) == suite["completed_cells"] == 76
    assert len(controls["cells"]) == controls["completed_cells"] == 21
    with (root / "measurements.csv").open(newline="", encoding="utf-8") as stream:
        rows = {r["id"]: r for r in csv.DictReader(stream)}
    assert len(rows) == 76
    annotations = digest(root / "suite/inputs/annotations/room0/targets.json")
    primary = {}
    for spec in suite["cells"]:
        path = root / "suite/cells" / spec["id"] / "record.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        assert record["status"] == "executed" and record["exit_code"] == 0
        assert record["method"] == spec["method"]
        assert record["annotations_sha256"] == annotations
        assert not verify_record(path), path
        assert json.loads((path.parent / "summary.json").read_text(encoding="utf-8")) == record["summary"]
        count = 141 if spec["method"] in ("dufomap", "beautymap") else 8
        errors = (
            np.zeros((count, 3))
            if spec["mode"] == "reference"
            else paired_translations(count, spec["rms_m"], spec["seed"])[spec["mode"]]
        )
        buffer = io.BytesIO()
        np.save(buffer, errors)
        expected = hashlib.sha256(buffer.getvalue()).hexdigest()
        assert record["errors_sha256"] == expected == suite["artifacts"][spec["path"]]["sha256"]
        source = root / "suite/inputs/executed-code" / f"{record['script_sha256']}.py"
        assert digest(source) == record["script_sha256"]
        for key, value in record["summary"]["metrics"].items():
            if isinstance(value, (float, int)):
                assert abs(float(rows[spec["id"]][key]) - value) < 1e-12
        primary[spec["id"]] = record
    for spec in controls["cells"]:
        path = root / "controls/cells" / spec["id"] / "record.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        assert record["status"] == "executed" and record["exit_code"] == 0
        assert not verify_record(path), path
        assert digest(path) == spec["record_sha256"]
        assert record["errors_sha256"] == primary[spec["original_id"]]["errors_sha256"]
        assert record["annotations_sha256"] == annotations
        assert record["summary"] == spec["summary"]
        assert (
            digest(root / "suite/inputs/executed-code" / f"{record['script_sha256']}.py")
            == record["script_sha256"]
        )
    hov = primary["hovsg-reference"]["summary"]["mapping"]["cache_zero_error_byte_equivalence"]
    assert hov == {"map.ply": True, "segment_features.npy": True}
    print(
        "97 cells verified: native logs/summaries, regenerated error hashes, exact source adapters, CSV and HOV gate"
    )


if __name__ == "__main__":
    main()
