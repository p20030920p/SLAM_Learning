# 01-02 · KISS-ICP

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | KISS-ICP: In Defense of Point-to-Point ICP — Simple, Accurate, and Robust Registration If Done the Right Way |
| Venue | **RA-L 2023** |
| 论文链接 | [arXiv:2303.04754](https://arxiv.org/abs/2303.04754) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [PRBonn/kiss-icp](https://github.com/PRBonn/kiss-icp) ✅ 实测 200 |
| 数据 | KITTI odometry（需注册，免费） |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §6 并行实验 —— 下游定位器 |
| 复现状态 | ⬜ 未开始（论文报告值已记录） |

## 它做了什么 What it does

极简的纯点对点 ICP 里程计：没有训练、没有特征、没有回环，参数极少，靠自适应对应距离与运动补偿把 ICP 做到不需要调参。

## 为什么复现它 Why

H1′ 需要一把**不含学习成分、完全可复现**的尺子来量「清理后的地图还能不能定位」。KISS-ICP 是最好的一把：`pip install` 即可，CPU 几分钟跑完一条 KITTI 序列。

## 复现目标（可验收）Goals

- [ ] 在**原始未清理**的地图上跑出基线轨迹，记录 ATE / RPE
- [ ] 把四个方法清理后的地图分别当配准目标重跑，得到四组数字
- [ ] 定义并实现「配准失败率」（例如：单帧 ICP 未收敛、或 ATE 超过阈值的比例）
- [ ] 输出：F1 排名 vs 配准失败率排名（这是 H1′ 的直接证据）

## 步骤 Steps

```bash
pip install kiss-icp
kiss_icp_pipeline /path/to/kitti/sequence    # 基线：直接在原始序列上跑

# 关键一步要自己写：kiss-icp 原生是里程计，把「清理后的全局地图」当配准目标
# 是另一种用法。在 work/ 下写适配脚本，把地图与序列喂给它的 registration 接口。
```

## 坑与注意 Pitfalls

- **最大的坑**：kiss-icp 的入口是里程计，而我们要的是「在已有地图里定位」。
  需要自己写适配（用它的配准模块逐帧对齐到清理后的地图），这部分工作量要预留。
- KITTI 需要注册才能下载，先办。
- 记录硬件（核数）与耗时，否则「快慢」没有意义。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
