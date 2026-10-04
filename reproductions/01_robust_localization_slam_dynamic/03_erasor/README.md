# 01-03 · ERASOR

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | ERASOR: Egocentric Ratio of Pseudo Occupancy-Based Dynamic Object Removal for Static 3D Point Cloud Map Building |
| Venue | **RA-L 2021** |
| 论文链接 | [arXiv:2103.04316](https://arxiv.org/abs/2103.04316) |
| 代码 | [LimHyungTae/ERASOR](https://github.com/LimHyungTae/ERASOR) ✅ 实测 200 |
| 数据 | KITTI / MulRan（配合 DynamicMap_Benchmark） |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §2 难点 4 高变动场景的地图维护 |
| 复现状态 | ⬜ 未开始 |

## 它做了什么 What it does

把地图切成极坐标的「伪占据」体素，用每个体素在单次扫描中占据的高度比（egocentric ratio）与阈值判断它是不是动态，然后删除。

## 为什么复现它 Why

**阈值敏感方法的代表**：不同数据集要用不同阈值，换场景就要重调。这正是任务书 §1 H9 说的「删除决策没有被标定」的最直接物证——如果它的 F1 很高但定位效果一般，H1′ 就成立了一半。

## 复现目标（可验收）Goals

- [ ] 编译通过，在 KITTI 一条序列上产出清理后的地图
- [ ] 记录**用了什么阈值、为什么**，以及换阈值后结果变化多大（做一次敏感性扫描）
- [ ] 把清理后的地图交给 01-02，得到配准失败率
- [ ] 产出：阈值—F1—定位失败率 的三者关系图（这张图比单点数字更有说服力）

## 步骤 Steps

```bash
git clone https://github.com/LimHyungTae/ERASOR code/
# ROS1 catkin 工作空间；官方 README 里有 docker 方案，编译踩坑时优先用 docker
catkin build erasor
roslaunch erasor erasor.launch
```

## 坑与注意 Pitfalls

- ROS1 / catkin，和本仓库的 ROS 2（Jazzy）**不是同一套环境**，单独开一个工作空间，
  不要试图和 `src/` 里的包混编。
- 编译依赖较多（PCL、range image 相关），docker 往往比本机编译省时间。
- 阈值是它的核心参数，**改动必须记录**，否则结果不可复现。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
