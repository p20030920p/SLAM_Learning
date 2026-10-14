"""Freeze hypotheses and implementation before the formal recording batch."""
import datetime
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.runtime.recovery_probe import PARAMETERS

ROOT = Path(__file__).resolve().parents[3]


def main():
    output = ROOT / "results/analysis/hypotheses"
    output.mkdir(parents=True, exist_ok=True)
    protocol = output / "protocol.json"
    if protocol.exists():
        raise ValueError("Protocol is already frozen; preserve the previous protocol")
    sources = [ROOT / "src/slam_learning/runtime/recovery_probe.py", ROOT / "src/scripts/presentation/probe_localizer.py",
               ROOT / "src/scripts/presentation/prepare_probe.py", ROOT / "src/scripts/presentation/probe_sensors.py"]
    (output / "sources").mkdir()
    for path in sources:
        shutil.copyfile(path, output / "sources" / path.name)
    data = {
        "frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "hypotheses": {
            "H1": "Robust plane residuals, weak-direction projection and odometry regularization reduce corruption/degeneracy-driven drift; cannot create missing absolute constraints",
            "H2": "A real 4m depth camera supplies additional height geometry only if distinctive surfaces are visible and mapped; parallel walls alone remain ambiguous",
            "H3": "Bounded multi-candidate search with uniqueness and consecutive odometry-consistent confirmation can correct an offset initial belief where local fitting cannot",
        },
        "parameters": PARAMETERS,
        "comparisons": {"H1": ["plain", "guard"], "H2": ["guard", "depth"],
                        "H3_lidar": ["guard", "search"], "H3_depth": ["depth", "recover"],
                        "depth_during_recovery": ["search", "recover"]},
        "arms": ["2D lidar + depth camera, no 3D lidar in B URDF", "16-channel 3D lidar + same depth camera"],
        "scenes": ["static", "dynamic", "large-change", "corridor", "height-corridor"],
        "trials_per_condition": 1,
        "duration_sim_s": {"static": 90, "dynamic": 90, "large-change": 90, "corridor": 120, "height-corridor": 120},
        "depth": {"actual_sensor": "Gazebo depth_camera", "horizontal_fov_deg": 80, "resolution": [320, 240],
                  "range_m": [.25, 4.0], "synchronization_max_s": .12, "motion_compensation": "wheel odometry",
                  "noise": "ideal rendered depth, no hardware noise model"},
        "pose_scope": "All five prototypes estimate x/y/yaw with z/roll/pitch fixed; 3D arm uses XYZ plane residuals; native GICP retains its original full pose output",
        "mapping": "Separate measured A per scene, supplied mapping poses, raw lidar point map and independent depth point map; static A reused for persistent-change B; frozen maps",
        "truth_in_B": "independent scoring only; never an estimator input",
        "sampling": "all recorded published outputs; custom variants share frame IDs and sensor/odom bytes; native anchors consume the same live source independently",
        "metrics": "XY RMSE for 2D, XYZ RMSE for 3D; no spatial alignment; truth delta<=0.05s; first registered estimates, no unpublished initial belief or missing-output zero fill",
        "recovery_evaluation": "after actual observation-restoration stamp: XY<0.1m and |yaw|<5deg continuously >=5s with >=8 updates; retained XYZ/rotation separately",
        "limitations": ["Exploratory single run, no stable ranking", "Native-vs-prototype differences include motion prior, optimizer and map representation; no isolated sensor attribution",
                        "Bounded +/-2m, +/-30deg search, not arbitrary global kidnapping", "No online map update or full 3D SLAM", "Height control changes the world and is explicitly separate from original corridor"],
        "source_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
    }
    protocol.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Frozen: {protocol}")


if __name__ == "__main__":
    main()
