# 01-09 · LT-mapper

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | LT-mapper: A Modular Framework for LiDAR-based Lifelong Mapping |
| Venue | **ICRA 2022** |
| 论文链接 | [arXiv:2107.07712](https://arxiv.org/abs/2107.07712) |
| 代码 | [gisbi-kim/lt-mapper](https://github.com/gisbi-kim/lt-mapper) ✅ 实测 200 |
| 数据 | MulRan / KITTI（多会话序列） |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §2 难点 4 地图维护；car.md 难点 3「终身 SLAM」与参考库 |
| 复现状态 | ⬜ 未开始 |

## 它做了什么 What it does

模块化的长期 LiDAR 建图流水线：**多会话 SLAM（MSS）→ 高/低动态变化检测 → 正/负变化管理**，并在会话间维护位姿图，因此不要求好的初始对齐。

## 为什么复现它 Why

它是任务书 §4.1「地图更新策略」和 car.md 难点 3「终身 SLAM」共同指向的那篇工作。关键复现点在于它的**变化检测是几何的、体素阈值化的**——能报出变化区域，却分不清「结构真的变了」和「只是这次被挡住了」。这句话如果能在实验里复现出来，就直接支撑了「可观测性」这个切入点。

## 复现目标（可验收）Goals

- [ ] 跑通多会话对齐，得到跨会话的位姿图
- [ ] 复现它的变化检测，记录**用了什么阈值**
- [ ] **关键实验**：构造一个「结构未变但本次被遮挡」的场景，看它是否误报变化
- [ ] 产出：一份「几何阈值法在遮挡下误报」的实测记录

## 步骤 Steps

```bash
git clone https://github.com/gisbi-kim/lt-mapper code/
# ROS1 catkin；按仓库 README 分模块跑（MSS → change detection → management）
```

## 坑与注意 Pitfalls

- ROS1，与本仓库的 ROS 2 环境隔离。
- 它的模块是分步的（MSS / CD / CM），**按模块验收**，不要指望一条命令跑到底。
- 「遮挡导致误报」这个实验需要自己设计场景 —— 这是本次复现真正的产出。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
