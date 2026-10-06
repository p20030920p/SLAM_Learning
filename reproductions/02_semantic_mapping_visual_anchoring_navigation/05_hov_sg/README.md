<div align="center">

# 02-05 HOV-SG

**Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation**

分层开放词汇图加语言导航。

[![venue](https://img.shields.io/badge/venue-RSS%202024-22314E)](https://arxiv.org/abs/2403.17846)
![status](https://img.shields.io/badge/status-blocked%3A%20heaviest%20of%20the%20four-cf222e)
[![code](https://img.shields.io/badge/code-hovsg%2FHOV--SG-181717?logo=github&logoColor=white)](https://github.com/hovsg/HOV-SG)
![needs](https://img.shields.io/badge/needs-a%20GPU%20%28paper%20states%20none%29-6f42c1)

[需求](#需求) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py)*

</div>

HOV-SG 把场景做成分层开放词汇图，并用语言指令做导航。它是四篇 D2 底座里算力最重的一个。

|  |  |
| :--- | :--- |
| 状态 | 本机不可复现 |
| 阻塞 | 每个 3D segment 需要 SAM 掩码与三种 CLIP ViT-H-14 编码 |
| 数据 | ScanNet 为注册制，HM3D-Semantics 公开 |
| 依据 | 论文表 VII 单场景特征 99 至 479 MB |

---

## 需求

| 需要什么 | 说明 |
| :--- | :--- |
| GPU | 一块显卡，具体门槛论文没有写 |
| 数据 | ScanNet 的访问权限 |

## 说明

- 论文只给了一句定性说明，称建图过程耗时，不适合实时建图，没有写硬件与耗时。
- 这是本批里唯一需要猜显卡规模的一篇。

## 文档

- 论文自报数字与阻塞分析：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本：[`reproduce.py`](reproduce.py)，其中 `require()` 给出上面这条阻塞的可判定版本
- 本文件夹的实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
