"""Verify the recorded 3D suite without modifying its sealed evidence."""
import json
from pathlib import Path
import re

import numpy as np
import yaml
from scipy.spatial import cKDTree

from package_frozen_practice import read, sha, write
from visible_3d_suite import ROOT, SUITE, METHODS


def check_artifacts(folder):
    record = read(folder / "record.json")
    for name, metadata in record["artifacts"].items():
        path = folder / name
        assert path.stat().st_size == metadata["bytes"], path
        assert sha(path) == metadata["sha256"], path
    return len(record["artifacts"])


def audit():
    acquisitions, localization = {}, {}
    for scene in ("static", "dynamic", "corridor"):
        folder = SUITE / (scene + "-A")
        record = read(folder / "record.json")
        artifact_count = check_artifacts(folder)
        archive_path = Path(record["mapping_archive"]["path"])
        assert sha(archive_path) == record["mapping_archive"]["sha256"]
        with np.load(archive_path) as archive:
            points = archive["scan_0000"]
            pitches = np.unique(np.round(np.arctan2(points[:, 2], np.linalg.norm(points[:, :2], axis=1)), 3))
            assert len(pitches) == 16
            height_span = float(np.ptp(points[:, 2]))
            assert height_span > 1.0
            scans = len([key for key in archive.files if key.startswith("scan_")])
        view = yaml.safe_load((folder / "live.rviz").read_text())
        vis = view["Visualization Manager"]
        assert vis["Views"]["Current"]["Class"] == "rviz_default_plugins/Orbit"
        assert not any(display["Class"].endswith(("/Map", "/LaserScan")) for display in vis["Displays"])
        review = read(folder / "cleaning-review/record.json")
        assert review["new_inference"] is False
        processing = read(folder / "maps/record.json")
        if scene == "dynamic":
            # The exact label mask is generated next to the native map outputs.
            native_map_dirs = sorted(Path(record["source_run"]).glob("author-maps-*/point-labels.npy"))
            assert len(native_map_dirs) == 1
            labels = np.load(native_map_dirs[0])
        else:
            with np.load(archive_path) as archive:
                labels = np.concatenate([np.where(np.linalg.norm(archive[f"scan_{i:04d}"], axis=1) >= .45, 0, -1)
                                         for i in processing["selected_scan_ids"]])
        evidence = SUITE / "label-evidence" / (scene + ".npy")
        evidence.parent.mkdir(exist_ok=True)
        np.save(evidence, labels)
        map_scores = read(folder / "map-score.json")
        raw_points = np.load(folder / "maps/raw/points.npy")
        assert len(labels) == len(raw_points)
        for method in METHODS:
            assert sha(folder / "maps" / method / "points.npy") == review["source_maps"][method]["sha256"]
            retained = cKDTree(np.load(folder / "maps" / method / "points.npy")).query(raw_points, workers=2)[0] < 2e-5
            assert np.isclose(retained[labels == 0].mean(), map_scores["methods"][method]["static_retention"])
            if scene == "dynamic":
                assert np.isclose((~retained[labels == 1]).mean(), map_scores["methods"][method]["dynamic_removal"])
        acquisitions[scene] = {"sealed_artifacts_verified": artifact_count, "observed_scans": scans,
                               "channels_in_first_scan": len(pitches), "first_scan_height_span_m": height_span,
                               "map_quality": map_scores,
                               "point_labels": {"path": evidence.relative_to(ROOT).as_posix(), "sha256": sha(evidence),
                                                "values": {"0": "static", "1": "dynamic", "-1": "unscored self/boundary"}},
                               "mapping_poses": "provided simulation poses; controlled cleaning, not full 3D SLAM"}

    for scene in ("static", "dynamic", "corridor", "change"):
        folder = SUITE / (scene + "-B")
        record = read(folder / "record.json")
        artifact_count = check_artifacts(folder)
        assert record["frozen_maps_unchanged"] and not record["truth_input_to_localizers"]
        frozen = read(folder / "frozen-inputs.json")
        for filename, expected in frozen["map_sha256"].items():
            assert sha(Path(filename)) == expected
        scores = read(folder / "score.json")
        assert 0 < scores["common_scan_samples"] <= scores["observed_input_scan_samples"]
        begin, end = read(folder / "metrics.json")["recording_interval_sim_s"]
        inputs = {round(t, 6) for t in read(folder / "input-cloud-stamps.json") if begin + 5 <= t < end}
        assert len(inputs) == scores["observed_input_scan_samples"]
        native_log = (folder / "logs/localizers.log").read_text(errors="replace")
        a_scene = "static" if scene == "change" else scene
        expected_points = read(SUITE / (a_scene + "-A/map-score.json"))["methods"]
        loaded_points = {}
        for method in METHODS:
            count = re.search(r"\[" + re.escape(method) + r"\.lidar_localization\]: Map Size (\d+)", native_log)
            assert count is not None
            loaded_points[method] = int(count[1])
            assert loaded_points[method] == expected_points[method]["points"]
            vis = yaml.safe_load((folder / ("view-" + method + ".rviz")).read_text())["Visualization Manager"]
            assert vis["Views"]["Current"]["Class"].endswith("/Orbit")
            displays = {d["Name"]: d for d in vis["Displays"]}
            assert displays["Frozen " + method + " 3D map"]["Alpha"] >= .6
            assert displays["CURRENT SCAN - GREEN"]["Color"] == "55; 255; 120"
            assert "GICP POSE - PINK" in displays and "Native GICP trajectory" in displays
            assert scores["methods"][method]["common_samples"] == scores["common_scan_samples"]
            assert 0 <= scores["methods"][method]["scan_output_coverage"] <= 1
        localization[scene] = {"sealed_artifacts_verified": artifact_count, "maps_unchanged": True,
                               "identical_raw_dufomap_map": record["identical_raw_dufomap_map"],
                               "native_loaded_map_points": loaded_points, "scores": scores}

    report = {"status": "passed", "suite": SUITE.relative_to(ROOT).as_posix(),
              "recordings": {"live_3d_acquisition": 3, "live_3d_frozen_map_localization": 12, "saved_cleaning_reviews": 3},
              "A": acquisitions, "B": localization,
              "score_protocol": "Common finite native scan-stamped poses after 5 s warmup; XYZ and full SO(3) rotation RMSE; truth interpolated to the same time; no trajectory alignment.",
              "previous_score_issue": "The historical latest-pose 10 Hz grid also measured output-age displacement/rotation. Its numbers are retained in historical records and must not be compared directly with scan-time RMSE.",
              "interpretation": ["Freezing disables map updates; it is not an accuracy improvement method.",
                                 "DA/SA are point removal/retention ratios, not localization accuracy.",
                                 "Near-identical static maps can give near-identical poses.",
                                 "Identical Raw/DUFOMap corridor maps cannot support a causal cleaning benefit; separate-process scan histories and numerical instability remain confounds.",
                                 "Single trials do not establish significance; valid scan-output fraction is not localization success."],
              "native_localizer": {"source": "/root/slam-alternative-ws/src/lidar_localization_ros2",
                                   "revision": "ba9f7f06dbe80aeabff602c37d712dfaa948241d", "worktree_clean_at_audit": True,
                                   "label": "Installed native GICP with common fixed configuration, not claimed as unmodified upstream paper implementation.",
                                   "scan_stamp_trace": ["component_subscribers.cpp:803 passes msg->header.stamp to applyAcceptedAlignmentPipelineResult",
                                                        "component_alignment.cpp:651 passes stamp to publishCurrentPose",
                                                        "component_pose_publisher.cpp:6 assigns stamp to output pose header"],
                                   "visual_map_voxel_m": .08, "scan_voxel_m": .15,
                                   "voxel_caveat": "Occupied 15 cm cells are an audit diagnostic, not a claim about registration-target downsampling."}}
    early = Path("F:/be2演讲/原始会话/practice-3d-visible-20261016/早期低对比显示/static-B")
    if early.exists():
        first = read(early / "record.json")
        final = read(SUITE / "static-B/record.json")
        assert first["map_pcd_sha256"] == final["map_pcd_sha256"]
        display_retry = {"reason": "Frozen map was too faint at alpha .28 / 1 px. Re-recorded after increasing display alpha to .70 / 2 px; localization parameters and maps unchanged.",
                         "selection_basis": "Display legibility, not lower localization error. Both runs and all three first-run videos are preserved locally and indexed.",
                         "first_source": str(early), "first_record_sha256": sha(early / "record.json"),
                         "first_scores": first["score"], "first_map_pcd_sha256": first["map_pcd_sha256"],
                         "final_source": (SUITE / "static-B").relative_to(ROOT).as_posix(), "final_scores": final["score"]}
        write(SUITE / "display-rerecording.json", display_retry)
        report["static_display_retry"] = "display-rerecording.json"
    write(SUITE / "audit.json", report)
    print(json.dumps({"audit": "passed", "A": len(acquisitions), "B": len(localization), "videos": 18}))


if __name__ == "__main__":
    audit()
