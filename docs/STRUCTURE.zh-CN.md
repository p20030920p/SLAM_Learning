# 仓库结构

[English](STRUCTURE.md) | 中文

保留一个可安装的 Python 包及现有 `slam-study` 命令，在包内按职责分层；方法环境、配置、启动命令与证据放在可复用核心之外。

```text
SLAM_Learning/                  Git 仓库
├── src/slam_learning/          可安装的 CPU 包
│   ├── cli.py                 命令解析与分发
│   ├── visualization/         报告与实测输出可视化
│   ├── experiments/           有限范围对照与评价器检查
│   ├── runtime/               下载、方法适配、运行与证据管理
│   └── core/                  几何、指标、位姿对照与来源记录
├── launch/                    PowerShell／Bash 复现启动入口
├── scripts/                   准备、分析、录制与导出工具
├── configs/                   方法参数、冻结协议与清单
├── environments/              独立语义／CUDA 依赖快照
├── tests/                     单元与 CLI 集成测试
├── docs/                      双语论证、协议、操作说明与媒体
├── annotations/               带复核状态的版本化标注
├── results/reference/         已发布证据与实际执行的源码快照
├── archive/                   历史材料
└── results/runs/              本地生成运行，Git 忽略
```

依赖方向为 **CLI → 可视化 → 实验 → 运行编排 → 核心**。每层可调用任意下层；核心不依赖启动命令、实验编排、CUDA 或 ROS。Import Linter 检查分层方向、循环依赖与 CUDA／ROS 边界。

`runtime/adapters.py` 实现给定位姿的 LiDAR 方法适配；`runtime/runner.py` 启动并记录执行；`core/provenance.py` 负责哈希与严格 JSON。已发布 `record.json` 清单仍是证据接口。现有 ROS 查看工具在独立环境中使用标准消息。

## 启动与检查

```bash
bash launch/reproduce.sh --help
bash launch/reproduce.sh --smoke
uv run slam-study run --experiment mechanism
```

Windows 使用 `powershell -File launch/reproduce.ps1 -Help` 或 `-Smoke`。启动器烟测会在十帧上执行两种作者 LiDAR 方法，并可能下载既有输入；它与无需数据集的合成检查分开。环境安装仍由 `scripts/setup_*.sh` 负责；语义／CUDA 命令见[安装说明](REPRODUCE.zh-CN.md)。

旧命令 `bash scripts/run_reproduction.sh [--smoke]` 转发到新启动入口。CLI 参数、配置位置和已发布证据路径保留。内部导入改为 `slam_learning.core`、`.runtime`、`.experiments` 与 `.visualization`，新运行快照记录新路径。历史源码快照与结果字节保持不变。

## 借鉴 ROS 2 的部分

[SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox/tree/ros2) 区分功能库与节点入口；[Nav2](https://github.com/ros-navigation/navigation2)、[ros2_control](https://github.com/ros-controls/ros2_control) 按稳定职责拆分；[TurtleBot3](https://github.com/ROBOTIS-GIT/turtlebot3) 单独组织启动与配置。本仓库据此整理包内层次与 `launch/` 入口。

当前是 Python 复现项目，没有自有 C++ 构建、自定义 ROS 消息／服务或 colcon 包，因此不添加空的 `include/`、`msg/`、`srv/` 或 `package.xml`。后续实际 ROS 集成应建立同级包，并提供自己的清单与测试。

ROS 工作空间、仓库和包是不同层级：工作空间 `src/` 下放仓库；每个实际 ROS 包拥有自己的清单，包内不能再嵌套包。`build/`、`install/` 与 `log/` 属于工作空间生成目录。[ROS 2 包目录说明](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials/Beginner-Client-Libraries/Creating-Your-First-ROS2-Package.rst)。
