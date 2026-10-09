# 作者复现

[English](../README.md) | 中文

作者原始建图代码、固定源码版本与实验记录。

## 结果

| 方法 | 复现范围 | 原文对照 |
| --- | --- | --- |
| DUFOMap | KITTI 00 | [Table IV：15/15 个准确率数值一致](reports/DUFOMAP_TABLE4.zh-CN.md) |
| BeautyMap | KITTI 02 | [Table III：9/9 个准确率数值一致](reports/KITTI_PAPER_PROTOCOL.zh-CN.md) |
| ConceptGraphs | 3 个 SAM-only／2 个 Detect 场景 | [部分覆盖](reports/CONCEPTGRAPHS_SCENE_RESULTS.zh-CN.md) |
| HOV-SG | 在复现中 | |

一致指各自论文保留两位小数的准确率。ConceptGraphs 的场景覆盖与原文基准不同。[协议与边界](reports/SCOPE.zh-CN.md)。

## 运行

```bash
git submodule update --init --recursive
python3 src/scripts/prepare_runtime.py --runtime /path/to/new/runtime --cache src/upstream
```

使用 Linux／WSL 运行。[环境](guides/ENVIRONMENT.zh-CN.md) · [手册](guides/RUNBOOK.zh-CN.md) · [数据](guides/DATA_ACCESS.zh-CN.md)。

## 目录

```text
docs/      # 手册与报告
results/   # 日志、校验值与媒体
src/       # 配置、脚本与上游子模块
```

[源码版本](../src/configs/upstreams.json) · [实验记录](../results/README.md) · [交付分支](https://github.com/p20030920p/SLAM_Learning/tree/main) · [个人学习](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008)
