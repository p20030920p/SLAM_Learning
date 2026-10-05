<div align="center">

# 02-08 · Revisit Anything

**Revisit Anything: Visual Place Recognition via Image Segment Retrieval**

把图像检索下沉到「分割级」：先切片段，再按片段检索。

[![venue](https://img.shields.io/badge/venue-ECCV%202024-0b7285)](https://arxiv.org/abs/2409.18049)
![result](https://img.shields.io/badge/result-R%401%2095.32%20vs%2095.3-2ea043)
[![code](https://img.shields.io/badge/code-AnyLoc%2FRevisit--Anything-181717?logo=github&logoColor=white)](https://github.com/AnyLoc/Revisit-Anything)
![data](https://img.shields.io/badge/data-17places%20%C2%B7%20authors'%20Box-1c7ed6)
![compute](https://img.shields.io/badge/compute-CPU%20%C2%B7%20~25%20min-6f42c1)

[Quick start](#quick-start) &nbsp;•&nbsp; [Results](#results) &nbsp;•&nbsp; [Notes](#notes)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

**分割级检索**：先用 SAM 把图像切成片段，再对片段独立编码与检索，而不是比较整图描述符 —— 因此在部分重叠与动态遮挡下更稳。

car.md 难点 7 的假设就是「分割级检索优于整图检索」。这篇是这个假设的**最强已发表版本**，所以它同时是基线也是对手：复现它才知道「Recall@1 提升 10–15%」这个预期还有没有空间，以及它在**物体被移动**（而不只是视角变化）时表现如何 —— 后者才是我们的问题。

|  |  |
| :--- | :--- |
| **指标（17Places，406 库 / 406 查询）** | 本文件夹 · 论文 论文表 2, p.9 |
| **R@1** | **95.32** · 论文 95.3 |
| **R@5** | **98.28** · 论文 98.0 |
| **R@1…R@5** | 95.32 / 97.04 / 97.29 / 97.78 / 98.28 · 论文 — |
| **Platform** | CPU · 20 核 · Ubuntu 24.04 + ROS 2 Jazzy |
| **Reproduce** | [`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json) |

**配置**：官方默认实验 `exp0_global_SegLoc_VLAD_PCA_o3`（邻域聚合 order 3 + PCA），用随包发布的 **map** 词表与 PCA 模型；
论文表 2 里 (D)/(M) 两种词表在 17Places 上并列 95.3/98.0，所以这一行就是论文那一行。
**耗时**：纯 CPU 约 **25 分钟** —— 因为分割掩码与逐片段 DINO 特征是作者**预处理好的**（`17places_full.zip`，11.1 GB），
本机只跑了「聚合 + 检索」这一段，而表 2 量的正是这一段。
> ⚠️ **别拿它和 02-07 的 65.0 比大小**：同一个 17Places、同一个 DINOv2 ViT-G14 骨干，两篇论文差 30 分是因为
> **GT 窗口不同**（本仓库 `gt.py:63` 用 ±15 帧；AnyLoc 用数据集自带的 ±5 帧）。详见下面专节。

---

## Quick start

| 依赖 | 版本 / 说明 |
| :--- | :--- |
| Python | `.venvs/anyloc`：torch CPU + faiss-cpu + pytorch_lightning + wandb + pytorch_metric_learning + prettytable + pandas + h5py + 仓库自带 `sam`（`pip install -e sam`） |
| 数据 | 作者 Box 镜像的 `17places_full.zip`（11.1 GB，解压 16 GB）：`out/*.h5` 逐片段 DINO 特征 + SAM 掩码 + 已拟合 PCA 模型 |
| 耗时 | 约 **25 min**（纯 CPU）—— 分割与特征提取都是作者预处理好的，本机只跑聚合/检索段 |
| 补丁 | `workdir_data` 改本机路径；聚合路径写死的 CUDA 改成有卡用卡/无卡用 CPU |

```bash
# 1) 数据：作者 Box 镜像（11.1 GB）
curl -L -o data/raw/17places_full.zip "https://adelaideuniversity.app.box.com/index.php?rm=box_download_shared_file&shared_name=199q2lpvy3psm5qgfagvh25r9c51ey6b&file_id=f_1677181487259"
unzip -q data/raw/17places_full.zip -d data/raw/
# 2) 跑（必须在仓库根目录下跑：脚本用相对路径 ./cache）
cd code/Revisit-Anything
PYTHONPATH=$PWD/VLAD-BuFF ../../../.venvs/anyloc/bin/python place_rec_main.py \
  --dataset 17places --experiment exp0_global_SegLoc_VLAD_PCA_o3 --vocab-vlad map --save-results
```

```bash
git clone https://github.com/AnyLoc/Revisit-Anything code/
# 与 AnyLoc 共用 VPR-datasets-downloader；SAM 权重需要单独下载
```

## Results

*2026-10-06*

```
POSITIVES/TOTAL segVLAD for this dataset:  [387 394 395 397 399] / 406
Max Seg Logs:  [0.9532, 0.9704, 0.9729, 0.9778, 0.9828]
Script fully Executed! Check your results!
```

| 命令 | `python place_rec_main.py --dataset 17places --experiment exp0_global_SegLoc_VLAD_PCA_o3 --vocab-vlad map --save-results` |
| :--- | :--- |
| 结果落盘 | `data/raw/workdir_root/17places/out/results/global/exp0_global_SegLoc_VLAD_PCA_o3_17places_*/`（三份 pkl） |
| 结构化的结果 | [`results/segloc_17places.json`](results/segloc_17places.json) |

### 两处本地补丁（都不动算法，记在 [`work/local_patches.patch`](work/local_patches.patch)）

| 现象 | 处理 |
| :--- | :--- |
| `workdir_data` 指向作者家里的目录 `/home/kartikgarg/workdir` | 改成本文件夹的 `data/raw/workdir_root` |
| **聚合路径把 CUDA 写死**：`func_vpr.aggFt` 里 45 处 `.to('cuda')`、22 处 `device='cuda'` 默认值、`place_rec_main` 里 `torch.device("cuda")`，**没有 CPU 回退** | 引入 `_DEV = 'cuda' if torch.cuda.is_available() else 'cpu'` —— **有 CUDA 的机器行为完全不变**，无 CUDA 时走 CPU |

### 两个只有跑过才知道的细节

1. **只有 map 词表的 PCA 模型随包发布**：`out/` 里有 `..._order3_map.pkl` 与两个 `dinoNV` 变体，**没有** config 里 `pca_model_pkl`（domain 词表）那一份。
   所以 `--vocab-vlad domain` 会在缺文件处停下；改用随包的 map 词表即可，而论文表 2 里 (D)/(M) 在 17Places 上并列，比较口径不变。
2. **`indoor/c_centers.pt` 不在 checkout 里**（`17places/c_centers.pt` 在）：domain 词表要从作者 AnyLoc 的官方 HF Space 缓存取（本机已有，见 [02-07](../07_anyloc/)）。

## Notes

- [ ] 跑通，在 Pitts-**30k** 上得到 Recall@1 基线（⚠️ 原写 Pitts250k/Tokyo24-7，均不在 AnyLoc 论文的数据集列表中；
      Revisit Anything 与 AnyLoc 的可比点就是 Baidu Mall：75.2 → 78.5）
- [ ] 构造「同一地点但物体被移动」的查询对，测 Recall@1 下降幅度
- [ ] 与 02-07 AnyLoc（整图检索）对比，验证分割级检索的增益到底有多大
- [ ] 产出：整图 vs 分割级 在「内容变化」条件下的对比表

- SAM 推理需要 GPU；数据集先小规模验证再全量下。
- 它评测的是**视角/外观变化**，不是**物体移动** —— 「内容变化 split」要自己造，
  这正是 car.md 难点 7 与我们那道变化检测题目的公共工作量。

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |

复现这两篇时最容易踩的坑，是**它们的 17Places 数字不能互相印证，因为它们用的 GT 窗口不一样**：

| 出处 | 17Places 的「算对」判据 | 同一骨干在同一份数据上的 R@1 |
| :--- | :--- | ---: |
| **AnyLoc**（本目录 [02-07](../07_anyloc/)） | 数据集自带的 `ground_truth_new.npy`：每个 query 对应 **±5 帧**（6 个候选） | **65.0** |
| **Revisit Anything**（本目录） | 仓库 [`gt.py`](code/Revisit-Anything/gt.py) 第 63 行：`loc_rad = 15` → **±15 帧**（31 个候选） | **95.3** |

两者都自报「17Places 上的 AnyLoc」：Anyloc 论文表 III 是 65.0/80.5，Revisit Anything 论文表 2 的对照行是 95.3/97.3。
**差 30 分不是方法差异，是判据差异**（候选集从 6 个放宽到 31 个）。

这条对任务书是直接有用的：H 系列假设里凡是「拿不同论文的 Recall 互相排序」的做法，
都必须先确认 GT 判据一致 —— 否则排出来的名次是协议的名次。

> 复现口径：本文件夹追 Revisit Anything 的 **95.3 / 98.0**（SegVLAD-PreT，表 2, p.9），
> 所以 **必须**用它自己的 `loc_rad = 15`；[02-07](../07_anyloc/) 追 AnyLoc 的 65.0，用它自带的 ±5 帧 GT。
> 两个文件夹各按各自论文的口径，不做「统一到一套判据」的美化。

## Documentation

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本：[`reproduce.py`](reproduce.py) · 回测基线：[`baselines.json`](baselines.json)
- 本文件夹的脚本、协议与实测记录：[`work/`](work/)
- 复现区索引与约定：[`../README.md`](../README.md) · 状态账本：[`../../status.json`](../../status.json)

<!-- run_all.py 读下面这几行生成索引表，改动请保持同样的 | 键 | 值 | 形式 -->

| 元数据 | 内容 |
| :--- | :--- |
| 论文 | Revisit Anything: Visual Place Recognition via Image Segment Retrieval |
| 论文链接 | [arXiv:2409.18049](https://arxiv.org/abs/2409.18049) |
| 代码 | [AnyLoc/Revisit-Anything](https://github.com/AnyLoc/Revisit-Anything) ✅ 已克隆（commit 628508d） |
| 方向 | D2 · 语义建图、视觉定位与导航 |
| 任务书对应 | car.md 方向二 · 难点 7「动态环境下的 VPR」的直接对手 |
| 能否复现 | ✅ **能，纯 CPU**：作者把分割与特征提取都预处理好了，本机只跑聚合/检索段（表 2 量的就是这一段）。要自己从原图重建描述子才需要 GPU |
| 复现完成 | ☑ 2026-10-06 · R@1 95.32 / R@5 98.28（论文 95.3 / 98.0），`reproduce.py` 可重跑 |
| 复现顺序 | 16 |
| 项 | 内容 |
| 本机怎么跑 | 纯 CPU · `.venvs/anyloc`（torch CPU + faiss-cpu + pytorch_lightning + wandb + pytorch_metric_learning + prettytable + pandas + h5py + 仓库自带 `sam`）· 全流程约 **25 min** |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 表 2, p.9：17Places SegVLAD-PreT (D)/(M) **R@1 95.3 / R@5 98.0** |
| 数据 | 作者 Box 镜像的 `17places_full.zip`（11.1 GB，解压 16 GB）：`out/*.h5` 逐片段 DINO 特征 + SAM 掩码 + 已拟合 PCA 模型 |
