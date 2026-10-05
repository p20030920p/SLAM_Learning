<div align="center">

# 02-05 · HOV-SG

**分层开放词汇图 + 语言导航 —— 四篇 D2 底座里算力最重的一个（SAM 掩码 + 三路 CLIP ViT-H-14 编码）。**

[![venue](https://img.shields.io/badge/venue-RSS%202024-0b7285)](https://arxiv.org/abs/2403.17846)
![blocked](https://img.shields.io/badge/blocked-heaviest%20of%20the%20four%20D2%20bases-cf222e)
[![code](https://img.shields.io/badge/code-hovsg%2FHOV--SG-181717?logo=github&logoColor=white)](https://github.com/hovsg/HOV-SG)
![data](https://img.shields.io/badge/data-ScanNet%20%C2%B7%20registration--gated-1c7ed6)
![needs](https://img.shields.io/badge/needs-a%20GPU%20%28bar%20unstated%20by%20the%20paper%29-6f42c1)

[结论](#一句话-verdict) &nbsp;•&nbsp; [怎么跑](#怎么跑-how-to-run) &nbsp;•&nbsp; [坑与注意](#坑与注意-pitfalls) &nbsp;•&nbsp; [记录](#记录-log)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py)*

</div>

---

## 一句话 Verdict

| | |
| :--- | :--- |
| **阻塞点** | 每个 3D segment 都要 SAM 掩码 + **三种 CLIP ViT-H-14 编码**（global RGB、masked-with-background、masked-without-background）+ DBSCAN 聚类 |
| **实测证据** | 论文**没写硬件也没写耗时**，只给了一句定性警告：建图过程 *"time-consuming, rendering the method unsuitable for real-time mapping"*。门槛只能从它的特征存储规模推（表 VII：单场景 99–479 MB 特征）—— 预计不低于 DualMap 的级别 |
| **数据也要过一道** | ScanNet 是**注册制**（不是直链），所以即便有卡也得先申请 |
| **要什么才能跑** | 一块 GPU（具体门槛论文没给，是本批里唯一"连要多大卡都要猜"的一篇）+ ScanNet 访问权 |

## 关键设定 Settings

| 项 | 内容 |
| :--- | :--- |
| 怎么才能跑 | 一块 GPU（论文没写门槛，是本批唯一「要多大卡都要猜」的一篇）+ ScanNet 注册访问权 |
| 论文 | Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation |
| 论文链接 | [arXiv:2403.17846](https://arxiv.org/abs/2403.17846) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [hovsg/HOV-SG](https://github.com/hovsg/HOV-SG) ✅ 实测 200 |
| 数据 | Replica / HM3D-Semantics（公开） |
| 方向 | D2 · 语义建图、视觉定位与导航 |
| 任务书对应 | §0 地图层；D2 的「导航」那一段 |
| 复现顺序 | 19 |
| 能否复现 | ⛔ 按论文规模不现实：habitat-sim 本身可以 headless 跑，CLIP/SAM 在 CPU 上也能推理，但 HM3DSem 是数千帧的大场景，CPU 上不现实。 |
| 复现完成 | ⛔ 本机不可复现（无 GPU） |

---

## 它做了什么 What it does

构建**分层**的开放词汇 3D 场景图（楼层 / 房间 / 物体），并在这个图上做**语言接地的导航**：说一句「去厨房的桌子旁边」就能规划。

## 为什么复现它 Why

一举覆盖 D2 的两段：语义建图 **和** 导航。任务书在导航这一段是空的（决策层只有「停车」），HOV-SG 是补上「目标级导航」最直接的入口；同时它每个场景只建一张静态图，修订能力缺失 —— 又是一个对照样本。

## 复现目标（可验收）Goals

- [ ] 在一个 Replica/HM3D 场景上跑通，得到分层场景图
- [ ] 跑通一次语言导航查询，记录它如何把语言映射到图上节点
- [ ] 明确写出：同一场景二次建图时，节点与身份是否保持（预计不保持）
- [ ] 产出：场景图 + 一次导航查询的复现记录

## 怎么跑 How to run

```bash
git clone https://github.com/hovsg/HOV-SG code/
# 依赖 Habitat / Replica / HM3D，流水线较长；按仓库 README 分步验证
```

## 坑与注意 Pitfalls

- 流水线长、依赖多，**按阶段验收**（先出场景图，再出导航），不要一次跑到底。
- 它自带仿真环境（Habitat），与本仓库的 Gazebo 是两套东西，不要混。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |