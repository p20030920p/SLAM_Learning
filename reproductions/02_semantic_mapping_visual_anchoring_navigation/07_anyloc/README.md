<div align="center">

# 02-07 AnyLoc

**AnyLoc: Towards Universal Visual Place Recognition**

免训练、免微调的视觉位置识别：现成自监督特征加无监督聚合。

[![venue](https://img.shields.io/badge/venue-RA--L%202023-22314E)](https://arxiv.org/abs/2308.00688)
![result](https://img.shields.io/badge/result-R%401%2065.0%20vs%2065.0-2ea043)
[![code](https://img.shields.io/badge/code-AnyLoc%2FAnyLoc-181717?logo=github&logoColor=white)](https://github.com/AnyLoc/AnyLoc)
![compute](https://img.shields.io/badge/compute-CPU%20%C2%B7%20%E7%BA%A6%203.3%20h-6f42c1)

[快速开始](#快速开始) &nbsp;•&nbsp; [结果](#结果) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

AnyLoc 直接用现成的自监督特征加无监督聚合做位置识别，不做训练或微调。这条复现跑的是论文的完整配置，在纯 CPU 上完成。

|  |  |
| :--- | :--- |
| 结果 | 17 Places R@1 65.0 / R@5 80.5（论文表 III 65.0 / 80.5） |
| 配置 | DINOv2 ViT-G14，layer 31，value facet，VLAD 32 簇，indoor 词表 |
| 规模 | 406 库图 / 406 查询图，5 帧容差真值 |
| 耗时 | 约 3.3 h（CPU，14.5 s 每图） |
| 复现 | `python3 work/run_17places.py` |

---

## 快速开始

| 依赖 | 版本 |
| :--- | :--- |
| Python | `.venvs/anyloc`（torch CPU + faiss） |
| 权重 | ViT-G14，由 Meta 官方 HuggingFace 镜像转换而来 |
| 数据 | 17 Places，作者 Box 镜像 |

```bash
python3 reproductions/02_semantic_mapping_visual_anchoring_navigation/07_anyloc/work/fetch_dinov2_weights.py dinov2_vitg14
python3 reproductions/02_semantic_mapping_visual_anchoring_navigation/07_anyloc/work/run_17places.py
```

## 结果

| 真值 | R@1 | R@5 |
| :--- | ---: | ---: |
| 数据集自带（5 帧容差，论文口径） | 65.03 | 80.54 |
| 作者修订版 | 67.49 | 82.02 |

论文表 III 的 17 Places 行是 65.0 / 80.5，本复现与之一致。

## 说明

- 官方三处下载出口在本机不可用：OneDrive 公开链接跳登录页，dl.fbaipublicfiles.com 实测 1.3 kB/s，indoor 词表不在仓库里。分别改用同作者的 Box 镜像、Meta 的 HuggingFace 镜像与作者官方 HF Space 缓存。
- 权重转换有双重校验：作者加载器严格加载 0 缺失 0 多余，逐块特征余弦从第 0 块 0.999981 平滑衰减到第 39 块 0.995534。
- 上游的 `get_top_k_recall(use_percentage=True)` 返回的是分数而不是百分数，本复现按百分数记录。
- 同一数据集在 02-08 里报 95.3，因为那边的真值窗口是正负 15 帧，两者不能互比。

## 文档

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本与回测基线：[`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json)
- 本文件夹的脚本与实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
