# Repository structure

English | [中文](STRUCTURE.zh-CN.md)

One installable Python package keeps the existing `slam-study` command. Responsibilities are separated inside it; method environments, configuration, launch commands and evidence remain outside the reusable core.

```text
SLAM_Learning/                  Git repository
├── src/slam_learning/          Installable CPU package
│   ├── cli.py                 Command parsing and dispatch
│   ├── visualization/         Reports and measured-output rendering
│   ├── experiments/           Scoped controls and evaluator checks
│   ├── runtime/               Fetch, method adapters and run/evidence handling
│   └── core/                  Geometry, metrics, pose controls and provenance
├── launch/                    PowerShell / Bash reproduction entry points
├── scripts/                   Preparation, analysis, recording and export tools
├── configs/                   Method parameters, frozen protocols and manifests
├── environments/              Separate semantic/CUDA dependency snapshots
├── tests/                     Unit and CLI integration tests
├── docs/                      Bilingual argument, protocols, guides and media
├── annotations/               Versioned labels with review status
├── results/reference/         Published evidence and executed source snapshots
├── archive/                   Historical material
└── results/runs/              Generated local runs, ignored by Git
```

Dependencies flow **CLI → visualization → experiments → runtime → core**. A layer may call any lower layer; core cannot depend on launch commands, experiment orchestration, CUDA or ROS. Import Linter checks layer direction, cycles and the CUDA/ROS boundary.

`runtime/adapters.py` implements the supplied-pose LiDAR adapters. `runtime/runner.py` starts and records executions; `core/provenance.py` handles hashes and strict JSON. Published `record.json` manifests remain the evidence interface. Existing ROS viewing tools use standard messages in a separate environment.

## Start and verify

```bash
bash launch/reproduce.sh --help
bash launch/reproduce.sh --smoke
uv run slam-study run --experiment mechanism
```

On Windows: `powershell -File launch/reproduce.ps1 -Help` or `-Smoke`. The smoke launch executes both author LiDAR methods on ten frames and may fetch their existing inputs; it is separate from the dataset-free synthetic check. Setup remains in `scripts/setup_*.sh`; semantic/CUDA commands remain in [Setup](REPRODUCE.md).

The old `bash scripts/run_reproduction.sh [--smoke]` forwards to the launch entry. CLI arguments, configuration locations and published evidence paths are retained. Internal imports now use `slam_learning.core`, `.runtime`, `.experiments` and `.visualization`; new run snapshots record these paths. Historical source snapshots and result bytes remain unchanged.

## What we borrow from ROS 2

[SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox/tree/ros2) separates functional libraries from node executables. [Nav2](https://github.com/ros-navigation/navigation2) and [ros2_control](https://github.com/ros-controls/ros2_control) split stable responsibilities; [TurtleBot3](https://github.com/ROBOTIS-GIT/turtlebot3) gives bringup and configuration their own place. Here those principles guide the package layers and `launch/` entry points.

This checkout is a Python reproduction project. It has no owned C++ build, custom ROS messages/services or colcon package, so it does not add empty `include/`, `msg/`, `srv/` or `package.xml` files. A future real ROS integration needs a sibling package with its own manifest and tests.

In a ROS workspace, repository and package are different levels: workspace `src/` contains repositories; each actual ROS package owns its manifest. Packages must not contain nested packages; `build/`, `install/` and `log/` are generated workspace outputs. [ROS 2 package guide](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials/Beginner-Client-Libraries/Creating-Your-First-ROS2-Package.rst).
