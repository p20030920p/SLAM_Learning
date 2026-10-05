<div align="center">

# 02-07 · AnyLoc

**通用视觉位置识别：一套 DINOv2 + VLAD 描述子跨数据集迁移 —— 论文数字绑 ViT-G14，但官方给了 17places 的 CPU 小规模入口。**

[![venue](https://img.shields.io/badge/venue-RA--L%202023-0b7285)](https://arxiv.org/abs/2308.00688)
![blocked](https://img.shields.io/badge/blocked-paper%20number%20needs%20ViT--G14%20on%20GPU-bf8700)
[![code](https://img.shields.io/badge/code-AnyLoc%2FAnyLoc-181717?logo=github&logoColor=white)](https://github.com/AnyLoc/AnyLoc)
![data](https://img.shields.io/badge/data-Baidu%20Mall%20%2F%20Pitts--30k%20%C2%B7%20public-1c7ed6)
![route](https://img.shields.io/badge/route-CPU%20route%20exists%3A%2017places-2ea043)

[结论](#一句话-verdict) &nbsp;•&nbsp; [怎么跑](#怎么跑-how-to-run) &nbsp;•&nbsp; [坑与注意](#坑与注意-pitfalls) &nbsp;•&nbsp; [记录](#记录-log)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py)*

</div>

---

## 一句话 Verdict

| | |
| :--- | :--- |
| **阻塞点** | 论文基线用 **ViT-G14（1.1B 参数）** 提特征，GPU 才现实（论文自报硬件：RTX 3090）；全量 Pitts-30k 是 10k 库 + 6.8k 查询 |
| **可行替代（尚未做）** | 官方 README 明确给了**小数据集 `17places`**（约 340 张图）的快速入口 —— **CPU 上做小规模检索是可行的**，只是慢。复现目标应写成「同一套评测口径下的 Recall@1」，不是全量 12 个数据集 |
| **实测证据** | 官方仓库已 clone 到 `code/AnyLoc`；`requirements.txt` 是 NGC 容器导出（含 `faiss-gpu`、CUDA 包），**不能直接 pip install**，要按 setup 脚本另配 |
| **要什么才能跑** | 论文数字：RTX 3090 级 GPU；小规模对照：CPU + 官方 17places 入口（小时级） |

## 关键设定 Settings

| 项 | 内容 |
| :--- | :--- |
| 怎么才能跑 | 论文数字要 RTX 3090 级 GPU；**CPU 可行替代**：官方 17places 小数据集（约 340 张图，小时级） |
| 论文 | AnyLoc: Towards Universal Visual Place Recognition |
| 论文链接 | [arXiv:2308.00688](https://arxiv.org/abs/2308.00688) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [AnyLoc/AnyLoc](https://github.com/AnyLoc/AnyLoc) ✅ 实测 200 |
| 数据 | 经 `VPR-datasets-downloader` 获取（Pitts-**30k** 等；⚠️ 原写 Pitts250k/Tokyo24-7，两者都**不在** AnyLoc 论文的 12 个数据集里） |
| 方向 | D2 · 语义建图、视觉定位与导航 |
| 任务书对应 | ⚠️ 补任务书缺掉的「视觉锚定」（原 T3 被删） |
| 复现顺序 | 15 |
| 能否复现 | 🟡 **CPU 可以跑，只是慢**：论文的表格要 ViT-G/14 提特征（GPU 才现实），但官方 README 明确给了**小数据集 17places** 的快速入口，CPU 上做小规模检索是可行的 —— 复现目标是「同一套评测口径下的 Recall@1」，不是全量 12 个数据集。 |
| 复现完成 | ⛔ 本机不可复现（无 GPU） |

---

## 它做了什么 What it does

用基础模型（DINOv2 等）的通用特征 + VLAD 聚合做视觉位置识别，**免训练**即可跨域工作，不需要为每个新环境重训。

## 为什么复现它 Why

任务书在 §0.2 明确承认原 T3「内容变化下的 VPR」**基本未保留** ——而「视觉锚定」正是老师给的 D2 的中间那一段。AnyLoc 是补这块缺口成本最低的入口：免训练、代码公开、数据集有统一下载器。

## 复现目标（可验收）Goals

- [ ] 跑通，在一个数据集上得到 recall@1 基线
- [ ] 构造一次「内容变化」测试：同一条路线，部分物体被移动/替换后重跑
- [ ] 记录 recall@1 的下降幅度（这就是原 T3 假设 H3 的直接检验）
- [ ] 产出：内容变化下的 VPR 性能曲线

## 怎么跑 How to run

```bash
git clone https://github.com/AnyLoc/AnyLoc code/
# 按仓库 README 用 VPR-datasets-downloader 拉数据，再跑 demo
```

## 复现怎么跑（本机，纯 CPU）

```bash
# 1) 图片：作者 OneDrive 的公开 release 现在跳登录页，改用同一作者组在 Revisit Anything
#    README 里挂的 Box 镜像（17places_only_dataset.zip，64,078,223 B）
curl -L -o data/raw/17places_only_dataset.zip \
  "https://adelaideuniversity.app.box.com/index.php?rm=box_download_shared_file&shared_name=199q2lpvy3psm5qgfagvh25r9c51ey6b&file_id=f_1677165155027"
# 2) 词表：作者官方 HF Space（他们 README 挂的 demo）里的 dinov2_vitg14/l31_value_c32/indoor/c_centers.pt
#    —— 197,425 B，32 簇 × 1536 维，正好是 ViT-G14 的隐藏维度，尺寸自证配置
# 3) 权重：dl.fbaipublicfiles.com 本机实测 1.3 kB/s（84 MB 要 18 小时），改用 Meta 官方 HF 镜像转换
python3 work/fetch_dinov2_weights.py dinov2_vitg14     # 转换 + 双重校验后才落盘
# 4) 跑
python3 work/run_17places.py                          # ~14.5 s/张，812 张约 3.3 h，每 25 张落一次盘
```

### 为什么权重那一步要自己转换（以及怎么证明它是对的）

`torch.hub.load('facebookresearch/dinov2', 'dinov2_vitg14')` 会去 `dl.fbaipublicfiles.com` 取 4.23 GB 的 `.pth`。
本机实测该源 **1.3 kB/s**（ViT-S 的 84 MB 都要 18 小时），而 HuggingFace 上 Meta 官方镜像有 **20 MB/s**。
所以 [`work/fetch_dinov2_weights.py`](work/fetch_dinov2_weights.py) 把 HF 的命名（`q_proj/k_proj/v_proj`、`down/gate/up_proj`）
还原成作者代码要的命名（`attn.qkv`、SwiGLU 的 `mlp.w12/w3`），**权重本身不变，只改键名**。

转换必须自证，脚本因此在落盘后跑两道校验，任何一道不过就**自动删除**文件：

| 校验 | 结果 |
| :--- | :--- |
| 作者自己的加载器（`vit_giant2` + `swiglufused`）严格加载 | **0 缺失 / 0 多余**，567 个张量、**1136 M 参数**（论文说 1.1 B） |
| 与 transformers 独立实现逐块比对（[`work/check_dinov2_conversion.py`](work/check_dinov2_conversion.py)） | 第 0 块余弦 **0.999981** → 第 39 块 **0.995534** |

第二道要解释一下：两个 fp32 实现跑 40 层网络本来就会漂移，**平滑衰减**是数值累积的特征；
如果是键名接错（比如 SwiGLU 的两半调换），第 0 块就会崩掉——而那里是 0.999981。

## 坑与注意 Pitfalls

- 数据集下载器拉的是外链，**先小规模验证一条**再全量下。
- 「内容变化 split」目前**不存在**，要自己造 —— 这既是工作量，也是原 T3 的贡献点所在。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |