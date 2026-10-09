from slam_learning.core.provenance import write_json
from slam_learning.visualization.report import render_report


def test_report_selects_latest_method_run_and_excludes_research(tmp_path):
    paths = []
    for name, method, stamp, scope in [
        ("old", "dufomap", "2026-10-08", "old scope"),
        ("new", "dufomap", "2026-10-09", "latest scope"),
        ("study", "unrelated", "2026-10-09", "research scope"),
    ]:
        path = tmp_path / name / "record.json"
        write_json(path, {"schema_version": 1, "kind": "fixture", "status": "recorded",
                          "method": method, "started_at": stamp, "scope": scope, "artifacts": {}})
        paths.append(path)
    report = render_report(paths, tmp_path)
    assert report.count("| DUFOMap |") == 1
    assert "latest scope" in report
    assert "old scope" not in report
    assert "research scope" not in report
    assert "new/record.json" in report


def test_hovsg_diagnostic_does_not_become_completed_reproduction(tmp_path):
    path = tmp_path / "record.json"
    write_json(path, {"schema_version": 1, "kind": "fixture", "status": "executed",
                      "method": "HOV-SG", "scope": "diagnostic subset", "artifacts": {}})
    report = render_report([path], tmp_path, "zh")
    assert "| HOV-SG | | 在复现中 | |" in report
    assert "diagnostic subset" not in report
