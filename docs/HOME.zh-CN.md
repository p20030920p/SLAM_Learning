# 个人学习

[English](../README.md) | 中文

阅读笔记、复现练习，以及 D435／Unitree L2 实物实验。

## 入口

| 用途 | 入口 |
| --- | --- |
| 学习与分析 | [学习手册](notes/README.zh-CN.md) |
| 实物练习 | [D435／L2](../src/physical/README.zh-CN.md) |
| 建图流程 | [运行手册](guides/REPRODUCE.zh-CN.md) |
| 已有结果 | [报告](README.zh-CN.md) · [证据](../results/reference) |

## 状态

已记录相机／雷达采集和 RGB-D 加载检查。实物语义建图与受控恢复实验仍在进行中。D435 不带 IMU。

## 目录

```text
docs/      # 笔记、论文与手册
results/   # 实验记录与媒体
src/       # 建图代码、脚本、配置和 physical/
```

建图命令从仓库根目录执行；硬件命令以 `src/physical/` 为项目根目录。[环境说明](guides/STRUCTURE.zh-CN.md) · [硬件环境](../src/physical/docs/ENVIRONMENT.zh-CN.md)。

[交付分支](https://github.com/p20030920p/SLAM_Learning/tree/main) · [作者复现](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals)
