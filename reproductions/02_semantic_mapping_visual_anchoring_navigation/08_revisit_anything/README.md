<div align="center">

# 02-08 · Revisit Anything

**把检索下沉到「分割级」：每张图先切片段，再按片段检索 —— 同样有官方 17places 入口，全量要 6.65 GB 描述子库。**

[![venue](https://img.shields.io/badge/venue-ECCV%202024-0b7285)](https://arxiv.org/abs/2409.18049)
![blocked](https://img.shields.io/badge/blocked-needs%20GPU%20for%20ViT--G%20%2B%20SAM%20ViT--H-bf8700)
[![code](https://img.shields.io/badge/code-AnyLoc%2FRevisit--Anything-181717?logo=github&logoColor=white)](https://github.com/AnyLoc/Revisit-Anything)
![data](https://img.shields.io/badge/data-Baidu%20Mall%20%2F%20Pitts--30k%20%C2%B7%20public-1c7ed6)
![route](https://img.shields.io/badge/route-CPU%20route%20exists%3A%2017places-2ea043)

[结论](#一句话-verdict) &nbsp;•&nbsp; [怎么跑](#怎么跑-how-to-run) &nbsp;•&nbsp; [坑与注意](#坑与注意-pitfalls) &nbsp;•&nbsp; [记录](#记录-log)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py)*

</div>

---

## 一句话 Verdict

| | |
| :--- | :--- |
| **阻塞点** | ViT-G（1.1B）+ SAM ViT-H 提片段描述子；全量 Pitts-30k 的描述子库 **6.65 GB**，检索 **251 ms/query**（论文表 7） |
| **可行替代（尚未做）** | 仓库自己建议先用 **17places**（约 340 张图）跑通；DINOv2 + SAM 在 CPU 上是**分钟级/张**，整套小数据集是**小时级** —— 可行但要有耐心 |
| **实测证据** | 论文全文 29 页 grep `GPU`/`NVIDIA`/`RTX`/`A100`/`V100` **0 命中** —— 它从未说明硬件，门槛是按模型与描述子规模推的 |
| **要什么才能跑** | 论文数字：一块 GPU；小规模对照：CPU + 17places（小时级） |

## 关键设定 Settings

| 项 | 内容 |
| :--- | :--- |
| 怎么才能跑 | 论文数字要 GPU（ViT-G + SAM ViT-H + 6.65 GB 描述子库）；**CPU 可行替代**：官方建议的 17places |
| 论文 | Revisit Anything: Visual Place Recognition via Image Segment Retrieval |
| 论文链接 | [arXiv:2409.18049](https://arxiv.org/abs/2409.18049) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [AnyLoc/Revisit-Anything](https://github.com/AnyLoc/Revisit-Anything) ✅ 实测 200 |
| 数据 | 经 `VPR-datasets-downloader` 获取（与 AnyLoc 共用） |
| 方向 | D2 · 语义建图、视觉定位与导航 |
| 任务书对应 | car.md 方向二 · 难点 7「动态环境下的 VPR」的直接对手 |
| 复现顺序 | 16 |
| 能否复现 | 🟡 **CPU 可以跑，只是慢**：仓库自己建议先用 **17places**（约 340 张图）跑通；DINOv2 + SAM 在 CPU 上是分钟级/张，整套小数据集是小时级 —— 可行但要有耐心。 |
| 复现完成 | ⛔ 本机不可复现（无 GPU） |

---

## 它做了什么 What it does

**分割级检索**：先用 SAM 把图像切成片段，再对片段独立编码与检索，而不是比较整图描述符 —— 因此在部分重叠与动态遮挡下更稳。

## 为什么复现它 Why

car.md 难点 7 的假设就是「分割级检索优于整图检索」。这篇是这个假设的**最强已发表版本**，所以它同时是基线也是对手：复现它才知道「Recall@1 提升 10–15%」这个预期还有没有空间，以及它在**物体被移动**（而不只是视角变化）时表现如何 —— 后者才是我们的问题。

## 复现目标（可验收）Goals

- [ ] 跑通，在 Pitts-**30k** 上得到 Recall@1 基线（⚠️ 原写 Pitts250k/Tokyo24-7，均不在 AnyLoc 论文的数据集列表中；
      Revisit Anything 与 AnyLoc 的可比点就是 Baidu Mall：75.2 → 78.5）
- [ ] 构造「同一地点但物体被移动」的查询对，测 Recall@1 下降幅度
- [ ] 与 02-07 AnyLoc（整图检索）对比，验证分割级检索的增益到底有多大
- [ ] 产出：整图 vs 分割级 在「内容变化」条件下的对比表

## 怎么跑 How to run

```bash
git clone https://github.com/AnyLoc/Revisit-Anything code/
# 与 AnyLoc 共用 VPR-datasets-downloader；SAM 权重需要单独下载
```

## 坑与注意 Pitfalls

- SAM 推理需要 GPU；数据集先小规模验证再全量下。
- 它评测的是**视角/外观变化**，不是**物体移动** —— 「内容变化 split」要自己造，
  这正是 car.md 难点 7 与我们那道变化检测题目的公共工作量。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |