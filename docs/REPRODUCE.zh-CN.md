# 最小复现入口

[English](REPRODUCE.md) | 中文

CPU 核心使用 Python 3.10 与仓库锁定依赖；CUDA 核心各有独立环境。不要把 CPU 锁安装进 CUDA 环境。方法设置、数据来源和适配见[论文卡](papers/README.zh-CN.md)及[语义范围](SEMANTIC.zh-CN.md)。

```bash
uv sync --frozen --python 3.10 --extra methods --extra dev
uv run slam-study fetch
uv run slam-study run --method dufomap
uv run slam-study run --method beautymap
```

Linux／WSL 首次准备 CPU 原生依赖使用 `bash scripts/setup_linux.sh`。语义核心依次执行，避免争用 GPU：

```bash
bash scripts/setup_semantic.sh
.venv-semantic/bin/python scripts/run_conceptgraphs.py
bash scripts/setup_hovsg.sh
.venv-hovsg/bin/python scripts/run_hovsg.py
```

每次创建新运行目录；命令打印 `record.json` 和日志位置。`--frames 10` 只作 LiDAR 冒烟，不输出论文成绩。普通退出码 0 表示执行完成，不代表论文表格一致；`--strict-paper` 对不一致返回 2。

## 1. 评价与完整性

```bash
uv run pytest -q
uv run ruff check src tests scripts
uv run python scripts/verify_evidence.py
uv run python scripts/verify_paired_evidence.py
uv run python scripts/verify_delayed_evidence.py
uv run python scripts/verify_delayed_support.py
uv run python scripts/check_docs.py
uv run slam-study verify results/runs/RUN_ID/record.json --full
```

替换 `RUN_ID` 为该次目录。公开 `results/reference` 不含完整地图，不能代替原生缓存。CI 检查代码、轻量证据与文档，不复跑全部 CUDA 论文实验。

LiDAR 地图近邻阈值 5 cm；SA／DA 的分母及 DUFOMap 直接标签与地图对应差异见[结果](RESULTS.zh-CN.md)。AA 为几何平均，HA 为调和平均，不作统一排行榜。BeautyMap 输入物理移除 GT intensity；XYZ 和 VIEWPOINT 保留。ConceptGraphs 实际入口使用绝对 `dataset.poses`，不再乘第一帧变换。

配对实验的 76 主单元和 21 探索对照有[独立协议](PAIRED_PROTOCOL.zh-CN.md)、[全部记录](../results/reference/paired-pose/record.json)与[复跑命令](PAIRED_RESULTS.zh-CN.md#复跑检查与面试)。新输出不得覆盖 v1。

新 room1 实验含 35 个冻结迟到修正单元和 6 个独立事后支持门槛对照。[协议与新运行步骤](DELAYED_PROTOCOL.zh-CN.md#复现状态) · [结果与 H1 修订决策](DELAYED_RESULTS.zh-CN.md)。

数据／权重校验、作者提交和资源适配在配置、源码快照和运行记录内固定；[来源与许可](ATTRIBUTION.zh-CN.md)可追溯。完整安装、个人录制和本机排错手册留在本地。公开 PDF 为记录绑定的生成快照，修改当前研究文字不会静默改写旧报告。
