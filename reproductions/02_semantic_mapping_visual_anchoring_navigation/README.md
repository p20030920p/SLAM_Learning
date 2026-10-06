<div align="center">

# D2 · 语义建图、视觉定位与导航

**地图里有什么，这个东西还是上次那个东西吗。**

![mapping](https://img.shields.io/badge/mapping-4%20%E4%B8%AA%E5%BC%80%E6%94%BE%E8%AF%8D%E6%B1%87%E5%BA%95%E5%BA%A7-22314E)
![anchoring](https://img.shields.io/badge/anchoring-%E6%95%B4%E5%9B%BE%E4%B8%8E%E5%88%86%E5%89%B2%E7%BA%A7%E6%A3%80%E7%B4%A2-1c7ed6)
![blocked](https://img.shields.io/badge/blocked-4%20%E4%B8%AA%E5%BA%95%E5%BA%A7%E5%8F%97%20GPU%20%E9%99%90%E5%88%B6-bf8700)

[目录](#目录) &nbsp;•&nbsp; [量纲](#一条量纲问题) &nbsp;•&nbsp; [导航](#导航)

*[复现区索引](../README.md) &nbsp;•&nbsp; [D1](../01_robust_localization_slam_dynamic/README.md) &nbsp;•&nbsp; [背景分析](../NOTES.md)*

</div>

|  |  |
| :--- | :--- |
| 三条线 | 语义建图（4 个开放词汇底座）、视觉锚定（整图与分割级检索）、导航 |
| 已跑通 | 02-01 3RScan 协议、02-07 AnyLoc、02-08 Revisit Anything |
| 受阻 | 4 个底座需要 16 至 24 GB 显存的 GPU，02-02 没有发布代码 |
| 一条警告 | 同一个数据集在两篇论文里差 30 分，差的是真值窗口不是方法 |

---

## 目录

| 编号 | 复现对象 | 角色 | 数据 | 状态 |
| :--- | :--- | :--- | :--- | :--- |
| [02-01](01_3rscan/) | 3RScan | 数据集：同房间多次扫描与物体重排标注 | 公开示例 | 半完成，全量需申请 |
| [02-02](02_oasis_map/) | OASIS-Map | 直接对手：语义对应做物体级变化检测 | 3RScan | 阻塞，代码未发布 |
| [02-03](03_concept_graphs/) | ConceptGraphs | 底座：开放词汇 3D 场景图 | Replica / ScanNet | 阻塞，需 16 至 24 GB 显存 |
| [02-04](04_dualmaps/) | DualMap | 底座：会自我编辑的开放词汇地图 | Replica | 阻塞，论文用 RTX 4090 |
| [02-05](05_hov_sg/) | HOV-SG | 分层开放词汇图与语言导航 | Replica / HM3D | 阻塞，四篇里算力最重 |
| [02-06](06_clio/) | Clio | 机载实时分层场景图 | Replica | 阻塞，论文用 RTX 3090 |
| [02-07](07_anyloc/) | AnyLoc | 视觉锚定：整图检索 | 17places | 完成，R@1 65.0 |
| [02-08](08_revisit_anything/) | Revisit Anything | 视觉锚定：分割级检索 | 17places | 完成，R@1 95.32 |

## 一条量纲问题

同一个 17Places 数据集、同一个 DINOv2 ViT-G14 骨干，两篇论文的数字差 30 分：

| 出处 | 真值窗口 | R@1 |
| :--- | :--- | ---: |
| AnyLoc（02-07） | 数据集自带，正负 5 帧 | 65.0 |
| Revisit Anything（02-08） | 仓库 gt.py 的 loc_rad = 15 | 95.3 |

候选集相差 5 倍，所以这两个数字不能互相排名。凡是跨论文比较 Recall 的地方，都要先确认真值判据一致。

## 导航

语言导航在 HOV-SG（受阻），仿真侧的导航在仓库的 src/ 里：Nav2 加 A* 规划器。
两个视觉锚定条目的作用是把「我在哪」这一环补上，它们在纯 CPU 上都能跑完。
