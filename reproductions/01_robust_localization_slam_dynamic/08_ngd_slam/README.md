# 01-08 · ngd_slam

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | NGD-SLAM: Towards Real-Time Dynamic SLAM without GPU |
| Venue | **IROS 2025** |
| 论文链接 | [arXiv:2405.07392](https://arxiv.org/abs/2405.07392) |
| 代码 | [yuhaozhang7/NGD-SLAM](https://github.com/yuhaozhang7/NGD-SLAM) ✅ 实测 200 |
| 数据 | TUM RGB-D / BONN（公开） |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | car.md 方向一 · 难点 1「未知动态物体检测」；难点 4 的 CPU 基线 |
| 复现状态 | ⬜ 未开始 |

## 它做了什么 What it does

**纯 CPU 实时**的动态 SLAM：不用神经网络做分割，改用**光流 + 深度方差**判断特征点是否属于运动物体，从而在没有 GPU 的平台上也能剔除动态点。

## 为什么复现它 Why

car.md 的难点 1 主张「独立于语义分割、用纯几何运动视差检测未知动态物体」。NGD-SLAM 正是这条路线目前最好的公开证据：**没有语义先验也能做动态检测**。复现它的意义不只是跑通，而是看它的几何判据在**哪些动态物体上失效**——那正是「语义先验的盲区」这个假设要回答的问题。

## 复现目标（可验收）Goals

- [ ] 编译并在 TUM RGB-D 一条动态序列上跑通，记录 ATE
- [ ] 逐类记录：**非 COCO 类别的动态物体**（气球、被推的椅子、屏幕）它检出了吗？
- [ ] 与「纯语义掩膜」方案对比，给出几何路线在未知动态物体上的优势证据
- [ ] 产出：一张「动态物体类别 × 是否检出」的表 —— 这是难点 1 假设的直接证据

## 步骤 Steps

```bash
git clone https://github.com/yuhaozhang7/NGD-SLAM code/
# CPU only，无 GPU 依赖；按仓库 README 编译（ORB-SLAM3 系）
```

## 坑与注意 Pitfalls

- 属于 ORB-SLAM3 家族，编译依赖较多（Pangolin / OpenCV / DBoW2），预留时间。
- 它报告的是 ATE，而我们要的是**动态物体检出**——需要自己加统计口径（这正是可以做的增量）。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
