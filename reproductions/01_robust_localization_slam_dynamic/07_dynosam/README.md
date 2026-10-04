# 01-07 · DynoSAM

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | DynoSAM: Open-Source Smoothing and Mapping Framework for Dynamic SLAM |
| Venue | **T-RO 2025** |
| 论文链接 | [arXiv:2501.11893](https://arxiv.org/abs/2501.11893) |
| 代码 | [ACFR-RPG/DynoSAM](https://github.com/ACFR-RPG/DynoSAM) ✅ 实测 200 |
| 数据 | KITTI tracking / OMD / TartanAir / VIODE |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | 方向 1 备选（联合相机-物体评测） |
| 复现状态 | ⬜ 未开始 |

## 它做了什么 What it does

在因子图里**同时估计相机位姿与物体运动**，并开源了配套的评测协议，专门回答「动态 SLAM 到底该怎么评测」。

## 为什么复现它 Why

备选，但当点级方法不够用时它提供另一种信号来源：如果物体运动被显式估计出来，「这个物体还在不在」就有了模型化的答案，而不只是一个掩膜。它是我们判断「物体级 vs 点级」哪条路更值得走的依据。

## 复现目标（可验收）Goals

- [ ] 跑通官方示例数据集（先用最小的那个）
- [ ] 读它的评测协议：它如何定义动态 SLAM 的成功？
- [ ] 与任务书 §2 难点 4 的四个清理方法对照，写一段「点级 vs 物体级」的取舍结论

## 步骤 Steps

```bash
git clone https://github.com/ACFR-RPG/DynoSAM code/
# 需要 GPU + GTSAM；按仓库 README 安装（推荐 docker）
```

## 坑与注意 Pitfalls

- 依赖重（GPU、GTSAM），装环境可能占掉大部分时间 —— **这是备选，不要在它上面卡住主线**。
- 数据集体积大，先只下最小的一组。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
