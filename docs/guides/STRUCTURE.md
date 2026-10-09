# Repository structure

English | [中文](STRUCTURE.zh-CN.md)

Seven top-level working directories keep the delivery small. Start ordinary tasks through `launch/` and `slam-study`; other tools are grouped by purpose.

```text
SLAM_Learning/
├── src/slam_learning/      Python package and slam-study CLI
├── configs/               Parameters, protocols, annotations/, environments/
├── launch/                PowerShell / Bash reproduction entry points
├── scripts/               setup/, methods/, experiments/, evidence/, media/
├── tests/                 Unit and command integration tests
├── docs/                  guides/, research/, papers/, figures/, media/, pdf/, archive/
└── results/               Published reference/; ignored local runs/
```

Project manifests, locks, README, license, citation and Docker files stay at the root; `.github/` holds CI. Start documentation from its [index](../README.md) and scripts from the [tool index](../../scripts/README.md). Local environments, caches and build products are ignored by Git.

Package dependencies flow **CLI → visualization → experiments → runtime → core**. Import Linter checks layer direction, cycles and the CUDA/ROS boundary.

`runtime/adapters.py` implements the supplied-pose LiDAR adapters. `runtime/runner.py` starts and records executions; `core/provenance.py` handles hashes and strict JSON. Published `record.json` manifests remain the evidence interface. Existing ROS viewing tools use standard messages in a separate environment.

## Start and verify

```bash
bash launch/reproduce.sh --help
bash launch/reproduce.sh --smoke
uv run slam-study run --experiment mechanism
```

On Windows: `powershell -File launch/reproduce.ps1 -Help` or `-Smoke`. The smoke launch executes both author LiDAR methods on ten frames and may fetch their existing inputs; it is separate from the dataset-free synthetic check. Environment installation lives in `scripts/setup/`; semantic/CUDA commands remain in [Setup](REPRODUCE.md).

The old `bash scripts/run_reproduction.sh [--smoke]` forwards to the launch entry, and `slam-study` arguments stay unchanged. Other tools keep their filenames and arguments under their new groups. Active documentation and commands use the new paths; historical records retain recorded paths, source snapshots and result bytes.

## What we borrow from ROS 2

[SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox/tree/ros2) separates functional libraries from node executables. [Nav2](https://github.com/ros-navigation/navigation2) and [ros2_control](https://github.com/ros-controls/ros2_control) split stable responsibilities; [TurtleBot3](https://github.com/ROBOTIS-GIT/turtlebot3) gives bringup and configuration their own place. Here those principles guide the package layers and `launch/` entry points.

This checkout is a Python reproduction project. It has no owned C++ build, custom ROS messages/services or colcon package, so it does not add empty `include/`, `msg/`, `srv/` or `package.xml` files. A future real ROS integration needs a sibling package with its own manifest and tests.

In a ROS workspace, repository and package are different levels: workspace `src/` contains repositories; each actual ROS package owns its manifest. Packages must not contain nested packages; `build/`, `install/` and `log/` are generated workspace outputs. [ROS 2 package guide](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials/Beginner-Client-Libraries/Creating-Your-First-ROS2-Package.rst).
