# 仓库结构

[English](STRUCTURE.md) | 中文

根目录只保留一个 README 和三个业务目录：`src/` 放完整可运行 Python 项目；`docs/` 放中文首页、操作说明、研究、媒体、PDF 与引用；`results/` 放已记录证据。

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

根目录另有 Git 必需的隐藏配置 `.gitignore`、`.gitattributes`、`.github/`。生成环境、缓存和构建产物由 Git 忽略。

从仓库根目录运行：

```bash
uv sync --project src --frozen --python 3.10 --extra dev --extra audit
uv run --project src slam-study doctor
bash src/launch/reproduce.sh --help
```

Windows 使用 `powershell -File src/launch/reproduce.ps1 -Help`。`--smoke`／`-Smoke` 在十帧上运行作者 LiDAR 方法，可能下载数据；无需数据集的检查使用 `uv run --project src slam-study doctor`。

`slam-study` 参数保留，脚本与启动器统一使用 `src/` 下的路径；`src/scripts/run_reproduction.sh` 继续转发到启动入口。历史记录保留当时路径与原始字节。[安装说明](REPRODUCE.zh-CN.md) · [工具分组](../../src/scripts/README.md) · [阅读索引](../README.zh-CN.md)。

包内依赖依次为 CLI、可视化、运行编排、核心。Import Linter 检查方向、循环依赖与 CUDA／ROS 隔离。源码哈希只覆盖项目包与工具，不包含安装环境。

借鉴 [SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox/tree/ros2) 对实现、启动和配置的区分，以及 [Nav2](https://github.com/ros-navigation/navigation2) 的稳定职责边界，当前仍是一个 Python 项目。实际 ROS 集成应建立拥有自己清单的同级包。[ROS 2 包目录说明](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials/Beginner-Client-Libraries/Creating-Your-First-ROS2-Package.rst)。
