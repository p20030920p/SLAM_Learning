import importlib.util
import json
from pathlib import Path

from slam_learning.core.provenance import digest, write_json


def test_published_copy_is_bound_to_exact_source_artifact(tmp_path):
    spec = importlib.util.spec_from_file_location("check_docs", Path(__file__).parents[1] / "scripts/evidence/check_docs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (tmp_path / "configs").mkdir()
    (tmp_path / "docs/figures").mkdir(parents=True)
    (tmp_path / "results/reference/run").mkdir(parents=True)
    for name in ("README.md", "README.zh-CN.md"):
        (tmp_path / name).write_text("A bilingual page", encoding="utf-8")
    write_json(tmp_path / "configs/documentation.json", {"pairs": [{"en": "README.md", "zh": "README.zh-CN.md"}]})
    original = tmp_path / "results/reference/run/plot.png"
    original.write_bytes(b"measured image bytes")
    published = tmp_path / "docs/figures/preview.png"
    published.write_bytes(original.read_bytes())
    write_json(original.parent / "record.json", {"schema_version": 1, "kind": "measured_diagnostic_plot",
        "status": "executed", "artifacts": {"plot.png": {"sha256": digest(original), "availability": "portable"}}})
    slots = {"slots": [{"id": "preview", "status": "published", "path": "docs/figures/preview.png",
        "caption": {"en": "Measured", "zh": "实测"}, "source_artifact": "plot.png",
        "source_records": ["results/reference/run/record.json"]}]}
    path = tmp_path / "docs/figures/slots.json"
    write_json(path, slots)
    assert module.check(tmp_path) == []
    published.write_bytes(b"retouched image")
    assert any("not hash-bound" in e for e in module.check(tmp_path))
    published.write_bytes(original.read_bytes())
    slots["slots"][0]["source_artifact"] = "another.png"
    path.write_text(json.dumps(slots), encoding="utf-8")
    assert any("not hash-bound" in e for e in module.check(tmp_path))
