# Repository structure

English | [中文](STRUCTURE.zh-CN.md)

The root holds one README and three working directories. `src/` contains the complete runnable Python project, `docs/` contains the Chinese homepage, guides, research, media, PDFs and citation, and `results/` contains recorded evidence.

```text
SLAM_Learning/
├── README.md
├── src/
│   ├── slam_learning/
│   ├── configs/
│   ├── launch/
│   ├── scripts/
│   ├── tests/
│   ├── docker/
│   ├── pyproject.toml
│   ├── uv.lock
│   └── LICENSE
├── docs/
└── results/
```

Required hidden Git configuration stays at the root: `.gitignore`, `.gitattributes` and `.github/`. Generated environments, caches and build output are ignored.

From the repository root:

```bash
uv sync --project src --frozen --python 3.10 --extra dev --extra audit
uv run --project src slam-study doctor
bash src/launch/reproduce.sh --help
```

Windows: `powershell -File src/launch/reproduce.ps1 -Help`. Use `--smoke` / `-Smoke` for the ten-frame author LiDAR run; this may fetch data. The dataset-free check is `uv run --project src slam-study run --experiment mechanism`.

`slam-study` arguments stay unchanged. Scripts and launchers use paths under `src/`; `src/scripts/run_reproduction.sh` forwards to the launcher. Historical records retain their recorded paths and original bytes. [Setup](REPRODUCE.md) · [Tool groups](../../src/scripts/README.md) · [Reading index](../README.md).

Inside the package, dependencies flow from CLI through visualization, experiments and runtime to core. Import Linter checks direction, cycles and CUDA/ROS isolation. Source hashing covers owned package/tool code and excludes installed environments.

This follows the separation of implementation, startup and configuration in [SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox/tree/ros2) and stable responsibilities in [Nav2](https://github.com/ros-navigation/navigation2). It remains one Python project; actual ROS integration needs a sibling ROS package with its own manifest. [ROS 2 package guide](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials/Beginner-Client-Libraries/Creating-Your-First-ROS2-Package.rst).


This learning branch also contains `docs/notes/` for study guides and `src/physical/` for the self-contained hardware project. Hardware scripts retain their internal relative paths; device evidence remains in `src/physical/evidence/`.
