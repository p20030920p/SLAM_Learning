<div align="center">

# Personal Learning

</div>

English | [中文](README.zh-CN.md)

Study notes and D435 / Unitree L2 hardware trials share `notes/personal-study-guide-20261008`. See [main](https://github.com/p20030920p/SLAM_Learning/tree/main) for the research delivery and [reproduce/author-originals](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals) for original-code reproductions.

| Task | Entry |
| --- | --- |
| Read analysis, study notes and Windows instructions | [Notes index](notes/README.md) |
| Operate the sensors and inspect hardware trials and failures | [Hardware learning](physical/README.md) |
| Develop the open question and hypothesis from the lab brief | [Analysis outline](notes/LAB_ANALYSIS.md) |
| Repeat the four reproductions and recordings manually | [Windows operations](notes/WINDOWS_START.md) · [Recording](notes/MANUAL_RECORDING.md) |
| Inspect the frozen room2 protocol, code and evidence | [Pinned study snapshot](https://github.com/p20030920p/SLAM_Learning/tree/4361d4f353a7449c7d6964887643915d2fc72a11) |

Existing notes and reproduction cores remain at the root. The complete hardware project lives under `physical/`, with its own scripts, configuration and dependencies; use that directory as its project root. The existing local device worktree at `D:/workspace/be2/Personal-Learning-Physical` remains usable. Environments and run data are not moved.

The SDK reports **D435 without IMU**. Streaming, odometry trials and native-loader checks do not establish complete SLAM, navigation or H1. Research limits and adverse results remain; raw device data, full recordings and environments stay local.

[Merge sources and pinned commits](notes/merge-sources.json)
