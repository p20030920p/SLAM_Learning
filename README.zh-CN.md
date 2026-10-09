<div align="center">

# 个人学习

</div>

[English](README.md) | 中文

学习笔记与 D435／宇树 L2 实物实验统一放在 `notes/personal-study-guide-20261008`。研究交付见 [main](https://github.com/p20030920p/SLAM_Learning/tree/main)，作者原库复现见 [reproduce/author-originals](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals)。

| 要做什么 | 入口 |
| --- | --- |
| 阅读分析、学习笔记和 Windows 操作说明 | [笔记索引](notes/README.zh-CN.md) |
| 操作相机、雷达，查看实物试验与失败记录 | [实物学习](physical/README.zh-CN.md) |
| 对照实验室要求整理开放问题与假设 | [分析提纲](notes/LAB_ANALYSIS.zh-CN.md) |
| 手动重复四篇复现与录屏 | [Windows 操作](notes/WINDOWS_START.zh-CN.md) · [录屏](notes/MANUAL_RECORDING.zh-CN.md) |
| 查看 room2 的冻结协议、代码与已有证据 | [固定实验快照](https://github.com/p20030920p/SLAM_Learning/tree/4361d4f353a7449c7d6964887643915d2fc72a11) |

原有笔记和复现核心保留在根目录；实物项目完整保留在 `physical/`，使用其中自己的脚本、配置与依赖，运行时以该目录为项目目录。现有本地设备工作区 `D:/workspace/be2/Personal-Learning-Physical` 继续可用，环境和运行数据不移动。

SDK 实测为 **D435，无 IMU**。收流、里程计试跑与原生加载检查不等于完整 SLAM、导航或 H1 验证。研究边界与不利结果保留；原始设备数据、完整视频和环境仍留本机。

[合并来源与固定提交](notes/merge-sources.json)
