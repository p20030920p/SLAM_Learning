# Localization methods and current deployment

AMCL is a baseline, not a requirement. Holding the localizer fixed isolates the effect of Raw / DUFOMap / BeautyMap maps. Comparing localization algorithms is a separate experiment: map, sensor input, initialization, route and score window must be controlled.

| Open-source system | Estimates | Input / map | Current platform |
| --- | --- | --- | --- |
| [Nav2 AMCL](https://docs.nav2.org/configuration/packages/configuring-amcl.html) | 2D pose using particle filtering | 2D scan, wheel odometry, occupancy map | Executed in four robot conditions |
| [slam_toolbox localization](https://docs.ros.org/en/jazzy/p/slam_toolbox/) | 2D pose using scan matching and a stored pose graph | 2D scan, odometry, serialized pose graph | Mapping installed; localization requires a new serialized map |
| [IR-MCL](https://github.com/PRBonn/ir-mcl) | 2D pose using neural scan likelihoods and particles | 2D scan, motion, trained neural field | Author Bonn sequence executed; Gazebo map needs new field training |
| [AdaM-MCL](https://github.com/Runjian-Chen/AdaM_MCL) | 2D pose using learned proposals and an adaptive particle mixture | Scan, map, trained proposal model | Limited author-code run; current Gazebo map requires training/adaptation |
| [NDT / GICP](https://github.com/rsasaki0109/lidar_localization_ros2) | 3D pose by scan-to-prior-map registration | 3D points, fixed point-cloud map, optional odometry/IMU | Jazzy source build completed; native integration below |
| [Beluga](https://github.com/Ekumen-OS/beluga) | MCL-family localization | Modular observation/motion models | Installed; a different implementation, still a particle-filter family |

NDT represents map neighbourhoods by distributions; GICP aligns scans using local geometric covariances. Both need an informative scene and usable initialization; a working tracking demo does not prove global relocalization. Ordinary LiDAR odometry (for example KISS-ICP) estimates motion between scans and is not a direct replacement for fixed-map localization.

## Native 3D integration

Upstream lidar_localization_ros2 is pinned at ba9f7f06dbe80aeabff602c37d712dfaa948241d, built with its source dependency ndt_omp_ros2 in a separate /root/slam-alternative-ws/build_ws Jazzy overlay. The local integration launch is [registration.launch.py](../../src/scripts/presentation/registration.launch.py). No upstream estimator changes are made.

Input: live /points transformed through the robot's actual sensor extrinsic; frozen Raw mapping-A 3D map; wheel odometry. Output: native /<method>/pcl_pose and native map-to-odom TF. Independent Gazebo truth is collected only by the scorer. IMU and continuous-time deskew are disabled: the current profile has no IMU or per-point timing. The background occupancy map is only a display layer; NDT/GICP use the 3D map for estimation.

Initial belief follows the existing baseline's X=0.25 m, Y=0.15 m, yaw=0.12 rad offset. NDT resolution 0.5 m, input voxel size 0.15 m, range 0.3–12 m, up to 35 iterations and two NDT threads. This is a small indoor deployment test, not an author benchmark reproduction or a sensor-matched ranking against 2D AMCL.

One-click entries: F:\be2演讲\实机脚本\31-NDT三维定位_静态.bat / 32-GICP三维定位_静态.bat. They start real Gazebo/RViz/Terminal windows and record native output.

## Executed static trials

- [NDT latest native run](../../results/reference/robot-ndt-static/record.json): 402 matched updates, XY RMSE 0.93 cm, yaw 0.17°.
- [GICP native run](../../results/reference/robot-gicp-static/record.json): 397 matched updates, XY RMSE 1.09 cm, yaw 0.16°.
- [NDT initial trial](../../results/reference/robot-ndt-static-initial/record.json): 399 updates, XY RMSE 34.43 cm. Its viewport was subsequently corrected and a fresh trial recorded; estimator parameters were unchanged. Keeping both trials exposes run-to-run variation; its cause has not yet been established. Latest-trial accuracy is not a stability claim.

These earlier trials are short static 35-simulation-second drives with 3D input and XY/yaw scoring. They are not directly comparable to the longer 2D AMCL trials. The newer multi-map GICP trials below test dynamic and degradation conditions; physical kidnapping remains untested.

The source build completed two packages and the upstream focused suite passed 342 tests. Dependency ndt_omp_ros2 revision: 63bf15b965b71d3a53db1757abe8e31b6114372a. [Pinned rebuild script](../../demo/build-registration.sh) uses a separate overlay and refuses to reset an existing checkout at another revision.

## Four-scene 3D map comparison, 2026-10-14–15

Raw, DUFOMap and BeautyMap complete 3D point maps now feed separate identical GICP instances. All receive the same published cloud/odometry source; their consumed histories and accepted-output coverage may differ. Global TF broadcasts are disabled and private full-SE(3) display relays isolate the RViz windows. XYZ position and quaternion-angle errors are scored from retained native poses against independent truth. Mapping uses supplied poses, without a full 3D SLAM claim.

[Four-scene scores, failed-output coverage and map-classification audit](MAP-2D-3D.md) · [native recordings](../../demo/gallery.html#3d). The new trials show no clear localization gain from cleaning; corridor controls expose registration instability. Entries 33–36 reproduce the multi-map trials, while 31–32 retain the earlier Raw-only demonstrations.
