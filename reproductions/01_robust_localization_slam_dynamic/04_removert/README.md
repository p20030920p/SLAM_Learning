# 01-04 · Removert

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | Removert: Remove then Revert — Static Map Building in Challenging Environment |
| Venue | **IROS 2020** |
| 论文链接 | [doi:10.1109/IROS45743.2020.9340856](https://doi.org/10.1109/IROS45743.2020.9340856) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [gisbi-kim/removert](https://github.com/gisbi-kim/removert) ✅ 实测 200 |
| 数据 | KITTI / MulRan（配合 DynamicMap_Benchmark） |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §2 难点 4 高变动场景的地图维护 |
| 复现状态 | ⬜ 未开始（论文报告值已记录） |

## 它做了什么 What it does

先从距离图像里删掉「可疑」的点，再用多分辨率距离图像把**被误删的静态点回滚回来**（remove then revert）。

## 为什么复现它 Why

**四个方法里唯一带显式回滚步骤的。** 回滚本质上就是在保护静态结构，所以如果 H1′ 成立（F1 高 ≠ 定位好），Removert 应该是表现最稳的对照组——它是我们理解「为什么有的删除方式更伤定位」的关键样本。

## 复现目标（可验收）Goals

- [ ] 编译通过，产出清理后的地图
- [ ] 单独记录 **revert 步骤删掉了多少点**（这是它和其他方法最大的结构差异）
- [ ] 与 ERASOR 对比：同样的 KITTI 序列，静态点保留率差多少
- [ ] 交给 01-02，看回滚是否真的换来了更低的配准失败率

## 步骤 Steps

```bash
git clone https://github.com/gisbi-kim/removert code/
# ROS1 catkin；仓库 README 给的依赖较多，先按它装完再编译
catkin build removert
```

## 坑与注意 Pitfalls

- ROS1，同样单独开工作空间。
- 依赖重（距离图像相关库），编译失败优先查 README 的依赖清单而不是猜。
- 它的参数比 ERASOR 多，**但正因为有 revert 步骤，它对参数应当更不敏感**——
  如果实测发现它也很敏感，这本身就是一个值得记录的发现。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
