# 最小复现入口

[English](REPRODUCE.md) | 中文

CPU 核心使用 Python 3.10 与仓库锁定依赖；CUDA 核心各有独立环境。不要把 CPU 锁安装进 CUDA 环境。方法设置、数据来源和适配见[论文卡](../papers/README.zh-CN.md)及[语义范围](SEMANTIC.zh-CN.md)。

```bash
uv sync --project src --frozen --python 3.10 --extra methods --extra dev
uv run --project src slam-study fetch
uv run --project src slam-study run --method dufomap
uv run --project src slam-study run --method beautymap
```

Linux／WSL 首次准备 CPU 原生依赖使用 `bash src/scripts/setup/setup_linux.sh`。

准备好环境后，`bash src/launch/reproduce.sh --smoke` 在十帧上运行两种 LiDAR 方法；Windows 使用 `powershell -File src/launch/reproduce.ps1 -Smoke`。旧入口 `src/scripts/run_reproduction.sh` 仍兼容。[目录职责与启动范围](STRUCTURE.zh-CN.md)。

语义核心依次执行，避免争用 GPU：

```bash
bash src/scripts/setup/setup_semantic.sh
.venv-semantic/bin/python src/scripts/methods/run_conceptgraphs.py
bash src/scripts/setup/setup_hovsg.sh
.venv-hovsg/bin/python src/scripts/methods/run_hovsg.py
```

每次创建新运行目录；命令打印 `record.json` 和日志位置。`--frames 10` 只作 LiDAR 冒烟，不输出论文成绩。普通退出码 0 表示执行完成，不代表论文表格一致；`--strict-paper` 对不一致返回 2。

项目清单和锁文件位于 `src/`。从仓库根目录使用 uv 时带 `--project src`。CPU／方法容器使用：

```bash
docker build --file src/docker/Dockerfile --tag slam-learning .
docker run --rm slam-learning doctor
```

## 评价与完整性

```bash
uv run --project src pytest -q src/tests
uv run --project src ruff check --config src/pyproject.toml src/slam_learning src/scripts src/tests
uv run --project src python src/scripts/evidence/verify_evidence.py
uv run --project src python src/scripts/evidence/verify_paired_evidence.py
uv run --project src python src/scripts/evidence/verify_delayed_evidence.py
uv run --project src python src/scripts/evidence/verify_delayed_support.py
uv run --project src python src/scripts/evidence/check_docs.py
uv run --project src slam-study verify results/runs/RUN_ID/record.json --full
```

替换 `RUN_ID` 为该次目录。公开 `results/reference` 不含完整地图，不能代替原生缓存。CI 检查代码、轻量证据与文档，不复跑全部 CUDA 论文实验。

LiDAR 地图近邻阈值 5 cm；SA／DA 的分母及 DUFOMap 直接标签与地图对应差异见[结果](../research/RESULTS.zh-CN.md)。AA 为几何平均，HA 为调和平均，不作统一排行榜。BeautyMap 输入物理移除 GT intensity；XYZ 和 VIEWPOINT 保留。ConceptGraphs 实际入口使用绝对 `dataset.poses`，不再乘第一帧变换。

配对实验的 76 主单元和 21 探索对照有[独立协议](../research/PAIRED_PROTOCOL.zh-CN.md)、[全部记录](../../results/reference/paired-pose/record.json)与[复跑命令](../research/PAIRED_RESULTS.zh-CN.md#复跑检查与面试)。新输出不得覆盖 v1。

新 room1 实验含 35 个冻结迟到修正单元和 6 个独立事后支持门槛对照。[协议与新运行步骤](../research/DELAYED_PROTOCOL.zh-CN.md#复现状态) · [结果与 H1 修订决策](../research/DELAYED_RESULTS.zh-CN.md)。

数据／权重校验、作者提交和资源适配在配置、源码快照和运行记录内固定；[来源与许可](ATTRIBUTION.zh-CN.md)可追溯。完整安装、个人录制和本机排错手册留在本地。公开 PDF 为记录绑定的生成快照，修改当前研究文字不会静默改写旧报告。

## 维护

```text
src/slam_learning/   CLI → 可视化 → 实验 → 运行编排 → 核心
src/launch/             PowerShell／Bash 复现启动入口
src/scripts/            准备、分析、查看器与导出工具
src/configs/            固定输入、协议、标注与独立环境快照
results/reference/  不可改写的证据与已执行源码快照
```

仅检查 CPU 代码，无需下载数据或使用 GPU：

```bash
uv sync --project src --frozen --python 3.10 --extra dev --extra audit
uv run --project src --no-sync deptry src/slam_learning --config src/pyproject.toml
uv run --project src --no-sync lint-imports --config src/pyproject.toml --no-cache
uv run --project src --no-sync vulture --config src/pyproject.toml
uv run --project src --no-sync pytest -q src/tests
```

[deptry](https://deptry.com/usage/) 检查包内依赖。Pillow 显式声明；四项 DEP002 例外对应 BeautyMap 子进程使用的 `fire`／`dztimer`／`tqdm` 和可选 Open3D 查看器。[Import Linter](https://import-linter.readthedocs.io/en/stable/contract_types/) 检查循环依赖、分层方向及 CUDA／ROS 隔离。

[Vulture](https://github.com/jendrikseipp/vulture) 以 100% 置信度检查现行源码、脚本与测试。低置信度结果需人工判断，框架属性和文件接口可能被外部调用。冻结源码快照和 CUDA 依赖清单不纳入此次清理。

[IWYU](https://github.com/include-what-you-use/include-what-you-use) 用于上游 C++ 构建。单独准备匹配的 Clang 与编译数据库，再运行 `iwyu_tool.py -p /path/to/build`。本工作区没有自有 C++ 构建目标，此处不声称已通过 IWYU。
