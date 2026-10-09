# 仓库结构

[English](STRUCTURE.md) | 中文

顶层只保留七个业务目录。常用操作从 `launch/` 和 `slam-study` 进入，其余工具按用途分组。

```text
SLAM_Learning/
├── src/slam_learning/      Python 包与 slam-study 命令
├── configs/               参数、协议、annotations/、environments/
├── launch/                PowerShell／Bash 复现入口
├── scripts/               setup/、methods/、experiments/、evidence/、media/
├── tests/                 单元与命令集成测试
├── docs/                  guides/、research/、papers/、figures/、media/、pdf/、archive/
└── results/               已发布 reference/；忽略的本地 runs/
```

项目清单、锁文件、README、许可、引用和 Docker 文件留在根目录；`.github/` 放 CI。文档从[总索引](../README.zh-CN.md)进入，脚本从[工具索引](../../scripts/README.md)进入。本地环境、缓存和构建产物由 Git 忽略。

包内 `cli.py`、`visualization/`、`experiments/`、`runtime/`、`core/` 依次向下依赖。Import Linter 检查分层方向、循环依赖与 CUDA／ROS 边界。

`runtime/adapters.py` 实现给定位姿的 LiDAR 方法适配；`runtime/runner.py` 启动并记录执行；`core/provenance.py` 负责哈希与严格 JSON。已发布 `record.json` 清单仍是证据接口。现有 ROS 查看工具在独立环境中使用标准消息。

## 启动与检查

```bash
bash launch/reproduce.sh --help
bash launch/reproduce.sh --smoke
uv run slam-study run --experiment mechanism
```

Windows 使用 `powershell -File launch/reproduce.ps1 -Help` 或 `-Smoke`。启动器烟测会在十帧上执行两种作者 LiDAR 方法，并可能下载既有输入；它与无需数据集的合成检查分开。环境安装由 `scripts/setup/` 负责；语义／CUDA 命令见[安装说明](REPRODUCE.zh-CN.md)。

旧命令 `bash scripts/run_reproduction.sh [--smoke]` 转发到新启动入口，`slam-study` 参数保留。其他工具保持原文件名和参数，改用新的分组路径。现行文档与命令使用新路径；历史记录保留当时路径、源码快照与结果字节。

## 借鉴 ROS 2 的部分

[SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox/tree/ros2) 区分功能库与节点入口；[Nav2](https://github.com/ros-navigation/navigation2)、[ros2_control](https://github.com/ros-controls/ros2_control) 按稳定职责拆分；[TurtleBot3](https://github.com/ROBOTIS-GIT/turtlebot3) 单独组织启动与配置。本仓库据此整理包内层次与 `launch/` 入口。

当前是 Python 复现项目，没有自有 C++ 构建、自定义 ROS 消息／服务或 colcon 包，因此不添加空的 `include/`、`msg/`、`srv/` 或 `package.xml`。后续实际 ROS 集成应建立同级包，并提供自己的清单与测试。

ROS 工作空间、仓库和包是不同层级：工作空间 `src/` 下放仓库；每个实际 ROS 包拥有自己的清单，包内不能再嵌套包。`build/`、`install/` 与 `log/` 属于工作空间生成目录。[ROS 2 包目录说明](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials/Beginner-Client-Libraries/Creating-Your-First-ROS2-Package.rst)。
