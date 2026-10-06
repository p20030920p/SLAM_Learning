<div align="center">

# 02-02 OASIS-Map

**OASIS-Map: Object-Level Change Detection in Multi-Session Mapping**

用语义对应匹配做物体级变化检测，表 I 专门有 Assoc. 列、表 III 专测身份保持。

[![venue](https://img.shields.io/badge/venue-arXiv%202026--07%2C%20under%20review-22314E)](https://arxiv.org/abs/2607.14899)
![status](https://img.shields.io/badge/status-blocked%3A%20no%20released%20code-cf222e)
[![code](https://img.shields.io/badge/code-project%20page%20says%20Code%20Soon-181717)](https://dynamic.robots.ox.ac.uk/projects/oasis-map/)
![needs](https://img.shields.io/badge/needs-the%20authors%20to%20publish-6f42c1)

[需求](#需求) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py)*

</div>

OASIS-Map 用语义对应匹配处理物体级变化检测，并专门评测物体身份是否保持。这个文件夹因此只做论文精读。

|  |  |
| :--- | :--- |
| 状态 | 无可复现对象 |
| 阻塞 | 项目页仍标注 Code Soon，论文本身也还在审稿 |
| 规则 | 本仓库的规则是有上游代码才复现 |
| 已产出 | 论文报告值与一处判断修正记在 paper_baseline.md |

---

## 需求

| 需要什么 | 说明 |
| :--- | :--- |
| 代码 | 作者发布实现 |
| 现状 | 项目页可达，但没有仓库链接 |

## 说明

- 论文精读修正了一处判断：它有 Unknown 类，所以「增加弃权类」不能当作我们的差异点。
- 记录的数字：3RScan moved-F1 0.353、static-F1 0.663；Car Park replaced-F1 0.783。

## 文档

- 论文自报数字与阻塞分析：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本：[`reproduce.py`](reproduce.py)，其中 `require()` 给出上面这条阻塞的可判定版本
- 本文件夹的实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
