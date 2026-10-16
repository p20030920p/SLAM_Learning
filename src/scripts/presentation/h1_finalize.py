"""Audit revised H1 and pool all predeclared fresh B sessions."""
import json
from pathlib import Path
import sys

import numpy as np

from h1_revision import ROOT, OLD, SUITE, METHODS, read, write, sha


def finalize(refined=False):
    if refined:
        from h1_refined import SUITE, METHODS
    else:
        from h1_revision import SUITE, METHODS
    protocol = read(SUITE / "confirmation-protocol.json")
    sources = protocol.get("algorithm_sources", {"own_mapping.py": protocol.get("algorithm_sha256")})
    for name, expected in sources.items():
        assert sha(ROOT / "src/slam_learning/runtime" / name) == expected
    assert sha(ROOT / "src/scripts/presentation/localization.launch.py") == protocol["unchanged_AMCL_sha256"]
    for scene in ("static", "dynamic"):
        a = SUITE / (scene + "-A")
        for relative, expected in protocol["maps"][scene].items():
            assert sha(a / relative) == expected
        for method, historical in (("raw", "raw"),) if refined else (("raw", "raw"), ("legacy", "temporal")):
            np.testing.assert_array_equal(np.load(a / "maps" / method / "points.npy"),
                                          np.load(OLD / (scene + "-A/maps") / historical / "points.npy"))
            assert (a / "maps" / method / "map.pgm").read_bytes() == (OLD / (scene + "-A/maps") / historical / "map.pgm").read_bytes()
        assert read(a / "A-replay-finished.json")["all_four_maps_reproduced_exactly"]
        assert (a / "execution.mp4").exists() and (a / "execution.gif").exists()
    development = read(SUITE / "dynamic-replay/trial-1/time-grid-score.json")
    original = read(OLD / "dynamic-B/time-grid-score.json")
    assert development["common_grid_samples"] == original["common_grid_samples"]
    for name, old_name in (("raw", "raw"),) if refined else (("raw", "raw"), ("legacy", "temporal")):
        assert abs(development["methods"][name]["common"]["rmse_m"] - original["methods"][old_name]["common"]["rmse_m"]) < 1e-10
    sessions, source_runs = {}, set()
    for folder in ("static-B", "dynamic-B", "dynamic-B2", "dynamic-B3"):
        b = SUITE / folder
        record = read(b / "record.json")
        session = read(b / "session.json")
        assert not session["truth_input_to_localizers"]
        assert set(read(b / "cases.json")) == {"raw", "temporal"}
        assert record["source_run"] not in source_runs
        source_runs.add(record["source_run"])
        a_scene = folder.split("-")[0]
        for method in ("raw", "temporal"):
            for name in ("map.pgm", "map.yaml"):
                assert sha(b / "maps" / method / name) == sha(SUITE / (a_scene + "-A/maps") / method / name)
            assert (b / "executions" / (method + ".mp4")).exists()
            assert (b / "executions" / (method + ".gif")).exists()
        raw_run = Path(record["source_run"])
        sessions[folder] = {"score": read(b / "time-grid-score.json"), "source_run": str(raw_run),
                            "input_bags": {str(p): {"sha256": sha(p), "bytes": p.stat().st_size, "availability": "local_only"}
                                           for p in (raw_run / "input-bag").glob("*.mcap")}}
    trials = [sessions[name]["score"] for name in ("dynamic-B", "dynamic-B2", "dynamic-B3")]
    count = sum(trial["common_grid_samples"] for trial in trials)
    assert count > 0
    pooled = {method: {"common": {"rmse_m": float(np.sqrt(sum(
        trial["methods"][method]["common"]["rmse_m"] ** 2 * trial["common_grid_samples"] for trial in trials) / count)),
                                     "samples": count}} for method in ("raw", "temporal")}
    quality = read(SUITE / "dynamic-A/record.json")
    q = quality["methods"]
    map_met = q["temporal"]["static_retention"] >= q["raw"]["static_retention"] - .01 and q["temporal"]["dynamic_removal"] > q["raw"]["dynamic_removal"]
    met = map_met and pooled["temporal"]["common"]["rmse_m"] < pooled["raw"]["common"]["rmse_m"]
    report = {"status": "executed", "kind": "predeclared_three_fresh_B_pooled_score", "methods": pooled,
              "fresh_dynamic_trials": 3, "common_grid_samples": count, "H1_conditions_met_this_batch": met,
              "map_criterion": map_met,
              "scope": "Same maps and AMCL parameters in all trials. Pool squared errors over each trial's common valid 10 Hz times; no trial selected by outcome. Not proof of general statistical significance.",
              "sessions": sessions, "development_replay_reproduces_original_negative_result": True,
              "development_B": development, "algorithm_sources": sources, "maps_unchanged": True}
    if refined:
        previous = ROOT / "results/reference/h1-supported-20261016/confirmation-score.json"
        report["cleanup_only_previous_confirmation"] = {"record": previous.relative_to(ROOT).as_posix(),
                                                        "methods": read(previous)["methods"]}
    write(SUITE / "confirmation-score.json", report)
    write(SUITE / "validation.json", {"status": "passed", "original_raw_and_legacy_maps_reproduced_exactly": True,
          "old_B_negative_RMSE_reproduced_exactly": True, "frozen_maps_unchanged": True,
          "algorithm_and_AMCL_unchanged_during_fresh_B": True, "fresh_B_sessions": len(sessions),
          "A_replays_reproduce_all_maps": True, "truth_to_algorithms": False})
    print(json.dumps({"pooled_cm": {key: value["common"]["rmse_m"]*100 for key, value in pooled.items()},
                      "H1_conditions_met_this_batch": met}, ensure_ascii=False))


if __name__ == "__main__":
    finalize("--refined" in sys.argv[1:])
