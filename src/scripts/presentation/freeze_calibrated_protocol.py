"""Freeze the frame-corrected repeat, preserving the complete zero-height trial."""
import datetime
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.core.provenance import digest
from slam_learning.runtime.frame_prior import height_from_mapping


def main():
    root = Path(__file__).resolve().parents[3]
    output = root / "results/analysis/hypotheses"
    path = output / "calibrated-protocol.json"
    if path.exists():
        raise ValueError("The calibrated protocol is already frozen")
    data = json.loads((output / "protocol.json").read_text())
    data["frozen_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    data["parent_protocol_sha256"] = digest(output / "protocol.json")
    data["correction"] = "Align internal XYZ map coordinates to the body reference calibrated from mapping A; publish world Z using that same fixed prior. All H1/H2/H3 settings remain unchanged. Localization B truth is never used for calibration."
    data["pose_scope"] = "x/y/yaw; z fixed to median mapping-A body height reconstructed with actual URDF extrinsics; roll/pitch=0; native GICP still unconstrained"
    data["mapping_A_height_priors"] = {scene: height_from_mapping(root / f"results/reference/probe-mapping-{scene}") for scene in ("static", "dynamic", "corridor", "height-corridor")}
    sources = [root / "src/slam_learning/runtime/recovery_probe.py", root / "src/scripts/presentation/probe_localizer.py",
               root / "src/slam_learning/runtime/frame_prior.py", root / "src/scripts/presentation/prepare_calibrated_probe.py"]
    snapshot = output / "calibrated-sources"
    snapshot.mkdir()
    for source in sources:
        shutil.copyfile(source, snapshot / source.name)
    data["source_sha256"] = {source.name: digest(source) for source in sources}
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({scene: value["ground_z_m"] for scene, value in data["mapping_A_height_priors"].items()}, indent=2))


if __name__ == "__main__":
    main()
