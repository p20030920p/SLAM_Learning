"""Verify stored A clouds and explain the original top-down recording view."""
import numpy as np
import yaml

from package_frozen_practice import ROOT, read, sha, windows_path, write


def audit():
    groups = []
    for scene in ("static", "dynamic", "corridor"):
        frozen = ROOT / "results/reference/practice-frozen-20261016" / ("3d-" + scene)
        processing = read(frozen / "mapping-A-processing.json")
        source = windows_path(processing["source_recording"])
        archive = source / "mapping-clouds.npz"
        assert sha(archive) == processing["input_sha256"]
        checks = []
        with np.load(archive, allow_pickle=False) as data:
            selected = processing["selected_scan_ids"]
            for index in (selected[0], selected[len(selected)//2], selected[-1]):
                scan = data[f"scan_{index:04d}"]
                assert scan.ndim == 2 and scan.shape[1] == 3
                angles = np.rad2deg(np.arctan2(scan[:, 2], np.linalg.norm(scan[:, :2], axis=1)))
                levels = np.unique(np.round(angles, 1))
                assert np.allclose(levels, np.arange(-15, 16, 2))
                checks.append({"scan": int(index), "points": len(scan), "vertical_angle_levels_deg": levels.tolist(),
                               "sensor_z_span_m": float(np.ptp(scan[:, 2]))})
            frames = len(data["poses"])
        view = yaml.safe_load((source / "live.rviz").read_text())["Visualization Manager"]
        assert view["Views"]["Current"]["Class"] == "rviz_default_plugins/TopDownOrtho"
        groups.append({"scene": scene, "source_mapping_A": str(source), "archive_sha256": sha(archive),
                       "archived_cloud_frames": frames, "selected_cloud_frames": len(selected), "sampled_scans": checks,
                       "recorded_view": view["Views"]["Current"]["Class"],
                       "visible_2D_map_topic": "/map", "stored_3D_cloud_topic": "/points"})
    output = ROOT / "results/reference/practice-map-cleaning-review-20261016/acquisition-dimension-audit.json"
    write(output, {"status": "verified", "scope": "Verify immutable A archives used by the frozen maps; first/middle/last selected scans have 16 vertical channels. The original recording uses a top-down 2D grid view.",
                   "mapping_A_pose_source": "provided simulation ground-truth poses; not full 3D SLAM pose estimation",
                   "truth_input_to_localization_B": False, "groups": groups})
    print(output)


if __name__ == "__main__":
    audit()
