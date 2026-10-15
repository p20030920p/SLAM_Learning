# Three open questions and experiments

H1/H2/H3 replace M1/M4/M5 as the current organization. Historical records retain their identity.

## E1 · Dynamic traces and held-out localization (H1)

Use the existing static, dynamic and corridor scenes and Sim2Real omni chassis. Native 2D uses 720-beam scans and wheel odometry: Raw accumulation vs author SRRG maintenance. Remove the projected DUFOMap/BeautyMap arms from current 2D tests. Freeze A, launch separate B, share scans and AMCL settings, and use the same initial offset. Truth is evaluation-only. Keep 3D Raw/DUFOMap/BeautyMap and GICP unchanged.

Report DA/SA, geometric error and observed support, then common-time pose/angular RMSE, P95, valid coverage and failures. DA is N/A without dynamics. Different representations are not ranked together. SRRG changes pose optimization and maintenance together; end-to-end observations do not isolate deletion. Cleaning without downstream improvement does not establish the entire hypothesis.

## E2 · FAST-LIO motion-distortion ablation (H2)

An isolated robot/world variant adds a 200Hz Gazebo IMU. Filter invalid returns and gate both IMU/scans until 3s of settling. Native gpu_lidar scans are instantaneous. Build a sequential scan from three successive measured 120-degree sectors with their actual packet timestamps; no truth-based warping or commercial scan-pattern claim.

Feed identical rolling scans, IMU and extrinsics to two official ROS2 FAST-LIO2 instances. A disclosed ablation skips only backward point correction after IMU state prediction; preserve matching and prediction. Bind the source commit and patch.

After stationary initialization, execute stationary, slow rotation, fast rotation, forward/reverse translation and stop phases. Check timing, IMU coverage and native outputs before scoring. Failures remain diagnostic records. Accumulate finite native registered clouds at matched times with 5cm voxels, including rendered ground and drifted points. Do not crop by estimated world height. This is frozen registered-scan accumulation, not an ikd-Tree export. Align poses only by the known start, never a best-fit trajectory alignment. Report odometry separately from held-out B: same GICP and initial pose on both frozen maps using an independent existing B scan session. Missing B is an explicit incomplete test, never substituted with odometry.

## E3a · Missing returns near a mirror (H3)

The supplied physical images motivate a controlled missing-return test: remove a fixed angular sector in a known scene and compare invalid/unknown handling with incorrectly treating it as maximum-range free rays. Score wrongly cleared real boundary cells, unknown space and geometric support. This is a missing-return control, not physical reflection simulation or a mirror detector. Real multipath, incidence-angle dependence and classification require additional hardware data.

## E3b · Corridor geometry (H3)

Compare the original corridor with a derived scene containing two asymmetric, LiDAR-visible physical side landmarks, leaving the route clear. Recollect A/B with identical parameters, route, initial offset and scan-limit/restoration timing. Score along/across-corridor error, yaw, coverage and the first 50s limited phase separately. The intervention changes the environment; it does not validate automatic degeneracy detection or fusion.

## Evidence

Bind recordings to inputs, source versions, configuration, native outputs, independent truth and media hashes. The few current runs are exploratory, not preregistered or statistically conclusive. Later vary speeds, contamination, offsets and repetitions. Homepage reporting contains metric definitions, values and blank analysis slots.
