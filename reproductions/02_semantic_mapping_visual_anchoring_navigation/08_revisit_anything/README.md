<div align="center">

# 02-08 Revisit Anything

**Revisit Anything: Visual Place Recognition via Image Segment Retrieval**

把图像检索下沉到分割级：先切片段，再按片段检索。

[![venue](https://img.shields.io/badge/venue-ECCV%202024-22314E)](https://arxiv.org/abs/2409.18049)
![result](https://img.shields.io/badge/result-R%401%2095.32%20vs%2095.3-2ea043)
[![code](https://img.shields.io/badge/code-AnyLoc%2FRevisit--Anything-181717?logo=github&logoColor=white)](https://github.com/AnyLoc/Revisit-Anything)
![compute](https://img.shields.io/badge/compute-CPU%20%C2%B7%20%E7%BA%A6%2025%20min-6f42c1)

[快速开始](#快速开始) &nbsp;•&nbsp; [结果](#结果) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

Revisit Anything 把每张图切成片段，对片段做特征与检索，再用相似度加权折算回图像级结果。作者发布了预处理好的片段特征，所以这条复现在纯 CPU 上二十分钟量级即可完成。

|  |  |
| :--- | :--- |
| 结果 | 17Places R@1 95.32 / R@5 98.28（论文表 2 的 95.3 / 98.0） |
| 配置 | exp0_global_SegLoc_VLAD_PCA_o3，map 词表与 PCA 模型 |
| 数据 | 作者 Box 镜像的 17places_full.zip（11.1 GB） |
| 耗时 | 约 25 min（CPU） |
| 复现 | `python3 place_rec_main.py --dataset 17places ...` |

---

## 快速开始

| 依赖 | 版本 |
| :--- | :--- |
| Python | `.venvs/anyloc`，含 pytorch_lightning / h5py / 仓库自带 sam |
| 数据 | 17places_full.zip，解压 16 GB |

```bash
cd reproductions/02_semantic_mapping_visual_anchoring_navigation/08_revisit_anything/code/Revisit-Anything
PYTHONPATH=$PWD/VLAD-BuFF ../../../.venvs/anyloc/bin/python place_rec_main.py \
  --dataset 17places --experiment exp0_global_SegLoc_VLAD_PCA_o3 --vocab-vlad map --save-results
```

## 结果

| 指标 | 本文件夹 | 论文表 2 |
| :--- | ---: | ---: |
| R@1 | 95.32 | 95.3 |
| R@5 | 98.28 | 98.0 |

完整的 R@1 到 R@5 是 95.32 / 97.04 / 97.29 / 97.78 / 98.28。

## 说明

- 本仓库的真值窗口是正负 15 帧（gt.py 的 loc_rad = 15），与 02-07 的正负 5 帧不同，因此 95.3 与 65.0 是同数据不同判据，不能互相排名。
- 只有 map 词表的 PCA 模型随数据包发布，domain 词表那份没有，所以命令用 map，论文表 2 里两种词表在该数据集上并列。
- 上游在聚合路径里写死了 CUDA，没有 CPU 回退，本地补丁把它改成有卡用卡、无卡用 CPU。

## 文档

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本与回测基线：[`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json)
- 本文件夹的脚本与实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
