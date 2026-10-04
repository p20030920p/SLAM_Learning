# 02-07 · AnyLoc

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | AnyLoc: Towards Universal Visual Place Recognition |
| Venue | **RA-L 2023**（ICRA 2024 展示） |
| 论文链接 | [arXiv:2308.00688](https://arxiv.org/abs/2308.00688) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [AnyLoc/AnyLoc](https://github.com/AnyLoc/AnyLoc) ✅ 实测 200 |
| 数据 | 经 `VPR-datasets-downloader` 获取（Pitts-**30k** 等；⚠️ 原写 Pitts250k/Tokyo24-7，两者都**不在** AnyLoc 论文的 12 个数据集里） |
| 方向 | D2 · 语义建图、视觉定位与导航 |
| 任务书对应 | ⚠️ 补任务书缺掉的「视觉锚定」（原 T3 被删） |
| 复现状态 | ⬜ 未开始（论文报告值已记录） |

| 复现顺序 | 11 |
| 能否复现 | ⛔ 本机不能：论文表格要 GPU 提特征；官方只提供 HF Space / Colab 的免 GPU 演示。 |
| 复现完成 | ⛔ 本机不可复现（无 GPU） |

## 它做了什么 What it does

用基础模型（DINOv2 等）的通用特征 + VLAD 聚合做视觉位置识别，**免训练**即可跨域工作，不需要为每个新环境重训。

## 为什么复现它 Why

任务书在 §0.2 明确承认原 T3「内容变化下的 VPR」**基本未保留** ——而「视觉锚定」正是老师给的 D2 的中间那一段。AnyLoc 是补这块缺口成本最低的入口：免训练、代码公开、数据集有统一下载器。

## 复现目标（可验收）Goals

- [ ] 跑通，在一个数据集上得到 recall@1 基线
- [ ] 构造一次「内容变化」测试：同一条路线，部分物体被移动/替换后重跑
- [ ] 记录 recall@1 的下降幅度（这就是原 T3 假设 H3 的直接检验）
- [ ] 产出：内容变化下的 VPR 性能曲线

## 步骤 Steps

```bash
git clone https://github.com/AnyLoc/AnyLoc code/
# 按仓库 README 用 VPR-datasets-downloader 拉数据，再跑 demo
```

## 坑与注意 Pitfalls

- 数据集下载器拉的是外链，**先小规模验证一条**再全量下。
- 「内容变化 split」目前**不存在**，要自己造 —— 这既是工作量，也是原 T3 的贡献点所在。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
