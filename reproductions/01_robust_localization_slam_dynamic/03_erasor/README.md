# 01-03 · ERASOR

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | ERASOR: Egocentric Ratio of Pseudo Occupancy-Based Dynamic Object Removal for Static 3D Point Cloud Map Building |
| Venue | **RA-L 2021** |
| 论文链接 | [arXiv:2103.04316](https://arxiv.org/abs/2103.04316) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [LimHyungTae/ERASOR](https://github.com/LimHyungTae/ERASOR) ✅ 实测 200 |
| 数据 | KITTI / MulRan（配合 DynamicMap_Benchmark） |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §2 难点 4 高变动场景的地图维护 |
| 复现状态 | 🟢 **已复现：命中基准表 I 行（66.70/98.54/81.07）** |
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

## 复现结果 Results（2026-10-05）

### 一、命中基准行：SA/DA/AA 两位小数一致

跑法：DynamicMap_Benchmark 的 `methods/ERASOR/build/erasor_run <seq> config/seq_00.yaml`，
数据是 KITTI 00（141 帧），评测用基准自带的 `export_eval_pcd`（`min_dis=0.05`）。

| | SA [%] | DA [%] | AA [%] | HA [%] |
| :--- | ---: | ---: | ---: | ---: |
| **DynamicMap_Benchmark 表 I, p.5** | 66.70 | 98.54 | 81.07 | — |
| **BeautyMap 论文 表 I, p.6（HA 列）** | 66.70 | 98.54 | — | 79.55 |
| **本次复现** | **66.7078** | **98.5352** | **81.0744** | **79.5563** |

### 二、⚠️ 低 SA 不是"删太多"，是**下采样**

输出地图只有 **1,417,955** 点，而 GT 有 **17,362,230** 点 —— 少了一个数量级。
原因是 ERASOR 的 `MapUpdater` 以 `map_voxel_size: 0.1` 做体素化。

于是 `export_eval_pcd` 的「0.05 m 内找不到邻居就判为删除」把**大量下采样掉的静态点读成了删除**：
`false_removal = 5,748,315`，而真正漏掉的动态点只有 `1,406`。
**SA 66.71 里的绝大部分是分辨率损失，不是算法错误。** 这一条对任何"用下游定位评测清理质量"的实验都成立，必须先扣掉。

### 三、⚠️ 同一个 ERASOR，两套口径差 27 个百分点

| 口径 | 数据集 | 指标 | 数值 |
| :--- | :--- | :--- | ---: |
| **ERASOR 论文 表 II, p.8** | SemanticKITTI 00 | voxel-wise PR / RR / F1（voxel 0.2） | **93.980** / 97.081 / 0.955 |
| **DynamicMap_Benchmark 表 I, p.5** | KITTI 00 | 点级 SA / DA / AA | **66.70** / 98.54 / 81.07 |

**同一个方法，从 93.98 掉到 66.70。** 而 Removert 在同样两套口径下是 **85.50 → 99.44**——
**换一套指标，两个方法的排名直接翻转**。这就是任务书 §6 并行实验 H1′ 要问的问题，
现在有了它自己的数字，见 [`../PAPER_BASELINES.md`](../PAPER_BASELINES.md) §3.1。

```bash
python3 reproductions/run_all.py --only 01-03
```

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
