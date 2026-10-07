# Physical experiments with D435i and Unitree L2

English | [中文](REAL_WORLD.zh-CN.md)

**Status: proposed protocol, no physical result claimed.** No mobile robot is needed for fixed-sensor change tests or handheld mapping. The available equipment is a D435i RGB-D/IMU camera and a Unitree L2 LiDAR/IMU. Test these separately first; a dual-sensor experiment requires a rigid mount, extrinsic calibration and measured clock alignment.

## What can actually be measured

| Equipment / arrangement | Question | What it cannot establish |
| --- | --- | --- |
| Fixed D435i, objects moved by hand | Hidden versus removed target; semantic association and current coordinates | Robot navigation success, absolute SLAM ATE |
| Fixed L2, objects moved by hand | Void/occupancy evidence, static loss, dynamic removal and sparse visibility | A universal KITTI-equivalent score without new labels |
| Handheld D435i or L2 on a rigid handle | Revisit consistency, drift-dependent mapping, recovery after correction | Accurate trajectory ground truth from IMU integration alone |
| Both sensors on a rigid board | Whether a wider stable background helps distinguish ego error from object change | Automatic fusion merely because both devices have an IMU |

The [D435i IMU calibration guide](https://www.intel.com/content/dam/support/us/en/documents/emerging-technologies/intel-realsense-technology/RealSense_Depth_D435i_IMU_Calib.pdf) and [L2 SDK](https://github.com/unitreerobotics/unilidar_sdk2) establish the sensor interfaces. The L2 SDK exposes point clouds, IMU, point time and ring; preserve them for deskewing. Device timestamps are not proof that two devices share a clock.

## Prepare one room

Use a table, chair, box, panel and two similar objects in a room with a visible wall and floor. Place tape marks at target positions and measure distances with a ruler. Use 1.5–3 m as an initial working arrangement, then check depth validity and LiDAR return density; this is a test choice, not a sensor range specification.

Mount the sensor on a stable tripod. Put a fiducial board on the static background, never on the moving target. Record a separate phone view showing the sensor, objects and a visible session label. The phone video verifies the event sequence, not millimetre-accurate ground truth. Tags visible to the algorithm are an assisted baseline; tags used only for evaluation must be masked from its input or processed in a separate view.

Before experiments, capture 30 seconds of a static scene. Inspect dropped frames, depth scale, intrinsics, distortion, units, frame axes and IMU gravity direction. Repeat with the other sensor on/off to detect possible depth/return changes. Log invalid-depth ratio and plane-fit residual. Check raw playback before moving anything.

## Acquisition paths

For D435i, use the [librealsense native recorder](https://github.com/realsenseai/librealsense/blob/master/doc/record-and-playback.md), which retains raw streams in a `.bag`. A convenience entry point is:

```bash
python scripts/capture_realsense.py --session A-static-01 --seconds 120
```

Run it in an environment with the official `pyrealsense2` package and direct device access. It requests RGB/depth at 640×480, 30 Hz and the device's default IMU profiles, records calibration and a bag hash. This script has syntax/help checks; it has **not** been tested on connected hardware here. SDK delivery samples do not verify the bag's full IMU frequency.

USB passthrough into WSL and direct Ethernet access are separate setup tasks. Native Windows capture is a practical first choice for D435i. Do not change the host network or lidar working mode automatically. For L2, inspect the official SDK example and record raw cloud/IMU data with the supported C++ or ROS wrapper. The SDK's published ROS2 example was verified on Foxy; this does not establish support for every Ubuntu/ROS combination.

When using a tested ROS2 installation, discover the actual topics first:

```bash
ros2 topic list -t
ros2 topic hz /unilidar/cloud
ros2 topic hz /unilidar/imu
ros2 bag record -o L2-A-static-01 /unilidar/cloud /unilidar/imu /tf /tf_static
```

These are the SDK's default lidar names; camera topic names vary by wrapper version. Record RGB, raw/aligned depth as appropriate, camera_info and both motion streams. Do not call a native RealSense bag a ROS2 bag. Pin the driver commit, firmware, profile and actual topic list in each session manifest.

## A. Fixed sensor, four distinguishable events

Capture each sensor separately; start with a 20-second unchanged reference, then perform one event, then observe for at least 20 seconds. Reacquire the unchanged scene before each event.

| Event | Action | Expected semantic distinction |
| --- | --- | --- |
| Static control | Nothing moves | False deletion and identity fragmentation should stay low |
| Occluded | Hide the chair with a panel, without moving it | Unknown/hidden, not proven removed |
| Removed and visible | Take the chair away; retain view of its former volume/background | Actual disappearance with visibility evidence |
| Moved | Shift the chair by measured tape displacement, e.g. 0.3 m | New current coordinate; old coordinate becomes stale |

Also capture an object outside the camera FOV as a separate condition. L2's coverage and camera coverage differ; judge disappearance only inside a sensor-specific observable region. A ray never reaching the former volume cannot certify absence.

First process fixed-camera data with identity poses. Use repeated static observations as a negative control. For the LiDAR adapters, export XYZ without semantic truth as input and supply the actual sensor origin; keep time/ring in the archive. Make the evaluation labels separately. For semantic adapters, preserve raw image/depth, calibrated intrinsics and per-frame pose; masks and features come from the original frontend.

## B. Handheld revisit and independent references

Walk a slow 1–2 minute loop, stop at the initial tape position, and observe the original scene again. Keep the device rigid and the static background visible. Start and finish stationary. Use LiDAR/IMU odometry or RGB-D odometry as an **estimated** pose source; D435i is not a tracking camera, and either IMU alone drifts.

Use several background tags/planes to check relative pose consistency. A calibrated tag PnP estimate is a noisy reference, not motion-capture truth. Record its reprojection error and view geometry. Compare sensor-fixed A, handheld B and the same recordings with controlled pose perturbations. Keep within-sweep motion/time information for L2 deskewing; do not confuse rolling acquisition distortion with scene dynamics.

## C. A paired test of the hypothesis

On the **same recorded frames**, keep masks/features fixed and replay exact/reference, estimated, independently perturbed and smoothly correlated poses. Begin with proposed translation RMS 0, 1, 3, 10 cm and rotation RMS 0, 0.3, 1, 3 degrees. Fix the map's gauge and verify achieved RMS after first-frame normalization. These are draft levels; change them only on validation sessions, then freeze.

Compare an ordinary threshold sweep, visibility protection, independent pose uncertainty, and the candidate shared-variable/provisional-update sidecar. Include known injected covariance as an oracle upper-bound diagnostic and an estimated-covariance version. Save the entire risk–coverage–delay curve; match change recall as well. The sidecar's buffer and replay cost count toward its budget.

Add a failure condition: move most visible similar boxes together while hiding the static board. Neither extra counts nor a median correction can create the missing anchor. Repeat after restoring the board to separate lack of information from an algorithm defect.

## Labels, repetitions and outputs

Assign physical object IDs before collection. Record initial/final positions, event interval, visible/occluded/out-of-FOV state and approximate measuring uncertainty. Annotate a small set of per-frame masks or 3D boxes; an event timestamp alone cannot yield pointwise SA/DA. A ruler-measured target position with its uncertainty can support coordinate error; it cannot support sub-centimetre claims automatically.

Use five independent validation sessions per event, then five test sessions with another layout/room after protocol freeze. This is a proposed minimum, not a guarantee of statistical power. Session-level intervals are preferable to treating every depth pixel as an independent sample. Avoid cherry-picking a single clean sequence.

Publish static loss, change recall, identity switches/fragmentation, target coordinate error, query coverage, stale duration, update delay and resources. Do not report navigation success without a robot. Publish failed captures and failures under coherent motion too.

For each session keep `capture.json`, calibration, raw file hashes, poses with frame convention, annotations, native logs, metrics, a phone clip and a fixed-view result replay. The homepage should show **real input + map decision + annotation/event label**, with session ID, units, supplied/estimated pose source and playback scope. Until data is collected, use a clearly marked planned section rather than an invented photograph or score.
