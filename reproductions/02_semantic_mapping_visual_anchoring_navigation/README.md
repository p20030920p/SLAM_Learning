<div align="center">

# D2 · 语义建图、视觉定位与导航

**地图里有什么？这个东西还是上次那个东西吗？—— 表示层（开放词汇地图）与视觉锚定两条线，本机受 GPU 硬件限制。**

![mapping](https://img.shields.io/badge/mapping-%E8%AF%AD%E4%B9%89%E5%BB%BA%E5%9B%BE%20%C2%B7%204%20%E4%B8%AA%E5%BA%95%E5%BA%A7-22314E)
![anchoring](https://img.shields.io/badge/anchoring-%E8%A7%86%E8%A7%89%E9%94%9A%E5%AE%9A%20%C2%B7%20%E6%95%B4%E5%9B%BE%20%2F%20%E5%88%86%E5%89%B2%E7%BA%A7%E6%A3%80%E7%B4%A2-1c7ed6)
![navigation](https://img.shields.io/badge/navigation-%E5%AF%BC%E8%88%AA%20%C2%B7%20HOV--SG%20%2B%20Gazebo%20%E4%BE%A7%20Nav2-6f42c1)
![blocked](https://img.shields.io/badge/blocked-%E6%9C%AC%E6%9C%BA%E6%97%A0%20GPU%EF%BC%9A4%20%E4%B8%AA%E5%BA%95%E5%BA%A7%E5%8F%97%E9%98%BB-bf8700)
![rule](https://img.shields.io/badge/rule-%E6%9C%89%E5%BA%93%E6%89%8D%E5%A4%8D%E7%8E%B0-2ea043)

[要回答的问题](#本方向要回答的问题) &nbsp;•&nbsp; [目录](#目录-index) &nbsp;•&nbsp; [顺序与产出](#顺序-与-产出) &nbsp;•&nbsp; [记录](#记录-notes)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [D1 方向](../01_robust_localization_slam_dynamic/README.md) &nbsp;•&nbsp; [传感器契合度](../NOTES.md) &nbsp;•&nbsp; [论文报告值](../PAPER_BASELINES.md)*

</div>

|  |  |
| :--- | :--- |
| **三条线** | 语义建图（4 个开放词汇底座）· 视觉锚定（整图检索 / 分割级检索）· 导航（HOV-SG + Gazebo 侧 Nav2） |
| **已跑通** | 02-01 3RScan 工具链与 A/B 协议 · 02-07 AnyLoc · 02-08 Revisit Anything |
| **受阻** | 4 个底座（02-03/04/05/06）要 16–24 GB 显存的 GPU；02-02 没有发布代码 |
| **一条量纲警告** | 同一个 17Places，AnyLoc 报 65.0、Revisit Anything 报 95.3 —— 差的是 **GT 窗口**（±5 帧 vs ±15 帧），不是方法 |

---


**Semantic mapping, visual anchoring and navigation** · семантическое картирование,
визуальная привязка и навигация

对应任务书《退化与高变动场景下的鲁棒定位与预判停车》的 §0 地图层（关键帧稀疏语义 +
ROI 实例级）、§2 难点 5（算力受限下的稀疏语义表示）、§4.1「修订语义」，
以及那道**物体级变化检测**题目（多会话物体身份与变化）。

---

## 本方向要回答的问题

> 地图里有什么？这个东西**还是上次那个东西**吗？它变了没有？
> 我能不能靠这张语义地图知道自己在哪里、并且用它导航？

三段关键词各对应一组资源：

| 关键词 | 复现对象 |
| :--- | :--- |
| **语义建图** | ConceptGraphs · DualMap · HOV-SG · Clio |
| **视觉锚定（视觉定位 / 位置识别）** | AnyLoc（+ 任务书里被删掉的 T3 方向） |
| **导航** | HOV-SG（语言导航）；Gazebo 侧在 [`../../src/`](../../src/) 的 Nav2 + A\* |

> ⚠️ **任务书在这里有两个缺口**：视觉锚定基本没写（原 T3 被删），导航只有「停车」没有「走」。
> 本目录的 02-07 与 02-05 就是补这两个缺口的入口。

---

## 目录 Index

| 编号 | 复现对象 | 角色 | 数据 | 算力 | 状态 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [02-01](01_3rscan/) | 3RScan | **数据集**：同房间多次扫描 + 物体重排标注 | 3RScan（需申请） | — | 🟢 已跑通（本机有 1 对会话） |
| [02-02](02_oasis_map/) | OASIS-Map | **直接对手**：语义对应做物体级变化检测 | 3RScan / 自采 | GPU | ⛔ 上游代码未发布（Code Soon），按规则只能做论文精读 |
| [02-03](03_concept_graphs/) | ConceptGraphs | 底座：开放词汇 3D 场景图 | Replica / ScanNet | GPU | ⛔ 本机无 GPU（SAM+CLIP+LLaVA-7B，≥16–24 GB 显存 + GPT-4） |
| [02-04](04_dualmaps/) | DualMap | 底座：会**自我编辑**的开放词汇地图 | 公开 + 自采 | GPU | ⛔ 本机无 GPU（论文用 RTX 4090） |
| [02-05](05_hov_sg/) | HOV-SG | 分层开放词汇图 **+ 语言导航** | Replica / HM3D | GPU | ⛔ 本机无 GPU（SAM + 3×CLIP ViT-H-14，四篇里最重） |
| [02-06](06_clio/) | Clio | 机载实时分层场景图（算力受限路线） | 自采 / 公开 | GPU | ⛔ 本机无 GPU（论文用 RTX 3090 / Spot 上的 4090 Laptop） |
| [02-07](07_anyloc/) | AnyLoc | **视觉锚定**：通用视觉位置识别（整图检索） | Pitts250k / Tokyo24-7 等 | GPU | ⛔ 官方仓库已克隆；论文数字绑 ViT-G14，无 GPU |
| [02-08](08_revisit_anything/) | Revisit Anything | **视觉锚定**：分割级检索（SAM 片段） | VPR-datasets-downloader | GPU | ⛔ 本机无 GPU（ViT-G + SAM ViT-H + 6.65 GB 描述子库） |

> **这张表的"状态"列在 2026-10-05 从 ⬜ 改成 ⛔，是信息增加，不是退步**：
> 每个文件夹里现在都有一份 `reproduce.py`，它的 `require()` 直接返回**具体缺什么**
> （缺的是哪张卡、哪个数据集、还是上游根本没发代码），
> 依据是各文件夹 `paper_baseline.md` 里对着原文记下的硬件与数据要求。
> 换句话说：**要开工时不用重新调研，缺的只是硬件。**

> **car.md 的优先建议**里，难点 7（动态环境下的 VPR）正是
> [02-07](07_anyloc/) 与 [02-08](08_revisit_anything/) 这一对：
> 整图检索 vs 分割级检索，可以直接对比「内容变化」下的 Recall@1。

---

## 顺序 与 产出

```
02-01 3RScan（二次访问协议）──→ 02-02 OASIS-Map 论文精读（无代码）
                                        │
02-03 ConceptGraphs ──┬─→ 02-04 DualMap ┤  提供「物体 + 身份」的实现载体
                      ├─→ 02-05 HOV-SG ─┤
                      └─→ 02-06 Clio ───┘
                                        ↓
                        会话 A 建图 → 会话 B 重访 → 变化判定
                                        ↓
                        02-07 AnyLoc：视觉锚定作为定位侧对照
```

**硬性产出**：

1. 一份可执行的**二次访问协议**（会话 A 建图 / 会话 B 变化后重访 / 容差半径写死）
2. 跨会话**身份一致率**与**变化检测 P/R/F1**（分 5 类：出现 / 消失 / 移动 / 替换 / 未变）
3. **可观测性分层 F1** —— 按「充分可见 / 部分可见 / 视场外或被遮挡」分档报告
4. 若做 OASIS-Map 对比：明确它报的 F1 与我们复现口径的差异

> 指标定义与协议草案见文献工作区（本机 `Localise/`，未推送到 GitHub）的
> `Practice_slam/04_topic_object_change_detection.md` §8。

---

## 记录 Notes

- **OASIS-Map 代码尚未发布**（项目页标注 Code Soon），02-02 目前只能按论文复现。
- 语义建图底座大多需要 GPU 与较大的模型权重；先把 02-01 的协议定死，
  再决定用哪个底座承载——否则会在换底座上耗掉全部时间。
- 物体身份的**容差半径**必须写死在报告里，不能事后调。
