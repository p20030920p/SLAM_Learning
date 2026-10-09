# 复现运行

[English](REPRODUCE.md) | 中文

从仓库根目录执行。CPU 与 CUDA 环境分别安装；运行前准备各自的数据和模型。

```bash
uv sync --project src --frozen --python 3.10 --extra methods --extra dev
uv run --project src slam-study fetch
uv run --project src slam-study run --method dufomap
uv run --project src slam-study run --method beautymap
```

```bash
bash src/scripts/setup/setup_semantic.sh
.venv-semantic/bin/python src/scripts/methods/run_conceptgraphs.py
```

HOV-SG 在复现中，环境与试跑入口保留如下。

```bash
bash src/scripts/setup/setup_hovsg.sh
.venv-hovsg/bin/python src/scripts/methods/run_hovsg.py
```

## 检查

```bash
uv run --project src pytest -q src/tests
uv run --project src python src/scripts/evidence/verify_evidence.py
uv run --project src python src/scripts/evidence/check_docs.py
uv run --project src slam-study doctor
```

LiDAR 的 `--frames 10` 仅作冒烟检查，不产生论文分数。每次运行创建新目录，完成执行与原文数值一致是不同状态。大点云仅保留在本地。

[Docs](../README.zh-CN.md) · [Results](../../results/REPORT.zh-CN.md) · [Structure](STRUCTURE.zh-CN.md)
