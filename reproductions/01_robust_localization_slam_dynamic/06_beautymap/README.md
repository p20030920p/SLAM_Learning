# 01-06 · BeautyMap

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | BeautyMap: Binary-Encoded Adaptable Ground Matrix for Dynamic Points Removal in Global Maps |
| Venue | **RA-L 2024** |
| 论文链接 | [arXiv:2405.07283](https://arxiv.org/abs/2405.07283) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [MKJia/BeautyMap](https://github.com/MKJia/BeautyMap) ✅ 实测 200 |
| 数据 | KITTI / MulRan（配合 DynamicMap_Benchmark） |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §2 难点 4 高变动场景的地图维护 |
| 复现状态 | ⬜ 未开始（论文报告值已记录） |

## 它做了什么 What it does

用**二值编码的「可适应地面矩阵」**表示地面，把地面上的动态点从全局地图里剔除；核心卖点是不用逐数据集调参。

## 为什么复现它 Why

第四个清理方法，补齐 H1′ 的对比集合。它和 DUFOMap 代表两种「免调参」路线（几何地面假设 vs 可见性建模），两者都要在，排名才有说服力。

## 复现目标（可验收）Goals

- [ ] 编译通过，产出清理后的地图
- [ ] 验证「免调参」：在两个不同数据集上是否真的用同一组参数
- [ ] 交给 01-02 得配准失败率
- [ ] 与 DUFOMap 对照：免调参路线内部，谁的定位可用性更好

## 步骤 Steps

```bash
git clone https://github.com/MKJia/BeautyMap code/
# 按仓库 README 构建与运行
```

## 坑与注意 Pitfalls

- ⚠️ **链接修正**：上游 `Localise/01_task_books/materials/links.md` 记的是
  `github.com/KTH-RPL/BeautyMap`，该地址**实测 404**。正确仓库是
  [`MKJia/BeautyMap`](https://github.com/MKJia/BeautyMap)（实测 200），别照抄旧的。
- 地面假设在坡道/多层场景会失效，记录它在哪种场景下降。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
