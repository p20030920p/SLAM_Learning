# 02-04 · DualMap — 论文报告值 Paper-reported baseline

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | DualMap: Online Open-Vocabulary Semantic Mapping for Natural Language Navigation in Dynamic Changing Scenes |
| Venue / 年 | 本地 PDF 为 **arXiv:2506.01950v4 [cs.RO]（2025-12-15）**，首页**未标注任何会议/期刊**（全文检索 `ICRA`/`RA-L`/`RSS`/`CoRL`/`accepted` 均只命中参考文献）。仓库 README 记 RA-L 2025，但**本 PDF 自身无 venue 声明** |
| 本地 PDF | `Localise/01_task_books/materials/papers_pdf/079_DualMap.pdf`（主结果表在第 **6–8** 页：TABLE II / III 在 p.6，TABLE IV / V / VI 在 p.7，TABLE VII 在 p.8；附录表在第 9–13 页：TABLE VIII 在 p.9，TABLE IX / X / XI 在 p.10，TABLE XII 在 p.12，TABLE XIII / XIV 在 p.12–13） |
| 官方代码 | PDF 内给出项目页 `https://eku127.github.io/DualMap/`（p.1）；正文提到 "the released code"（p.9 附录 I）说明有代码发布，但**PDF 内未出现 github.com 仓库 URL**（仓库 README 指向 `github.com/Eku127/DualMap`） |
| 任务 | 在线 open-vocabulary 语义建图 + 自然语言导航。用 hybrid 分割前端（YOLOv8l-world 闭集检测 + FastSAM-s 开放词表）构建 concrete map，再抽象出只含 anchor 物体与 layout 的 abstract map 做候选检索，导航中在线更新的 dual-map 表示支持物体被移动后的重定位 |
| 数据集 | **Replica**（office0–office4、room0–room2，8 场景）与 **ScanNet**（ScanNet200 标注，scene0011_00、scene0050_00、scene0231_00、scene0378_00、scene0518_00 共 5 场景）用于语义分割与效率；**HM3DSem**（00829、00848、00880 三场景 + 每场景随机放 6 个 YCB 物体）用于静态/动态物体导航；**TUM RGBD** 的 `freiburg3_walking_static` 序列仅做定性（有人走动时建图不受影响）；**真实世界**两平台四场景（Wheeled: Meeting Room、Apartment；Quadruped: Indoor Hallway、Outdoor） |
| 指标 | **mIoU / F-mIoU / mAcc**：沿用 [5] 的标准定义（附录 eq. 8–10；mIoU = (1/C)Σ TPi/(TPi+FNi+FPi)，FmIoU = Σ[(TPi+FNi)/Σj(TPj+FNj)]·[TPi/(TPi+FNi+FPi)]，mAcc = (1/C)Σ TPi/(TPi+FPi)），**排除 wall/floor/ceiling 等背景类**。**ODR (Object Density Ratio)**：论文新提出 = 预测物体数 / 真值物体数，越接近 1 越好。**Avg. Mem / Peak Mem (MB)**、**TPF (s)**（time per frame）。**SR (Success Rate)**：agent 停在距被查询物体 **1 m 以内**的 query 比例；**动态场景额外要求 3 次尝试内找到目标**。所有表中数值均按数据集内各场景取平均 |
| 硬件 | **主实验：NVIDIA RTX 4090 GPU + Intel i7-12700KF CPU**（p.6 §V-A-4）。**补充实验：RTX 3080 Laptop GPU**（p.12 附录 V-B，TABLE XIV）。长时建图实验：RTX 4090 Desktop + 1280×720 输入（p.12 附录 V-C）。**论文未给出显存占用/VRAM 需求**，只给了系统自身的内存指标（MB）与 TPF |

## 论文报告的数字 Reported numbers

> 说明：**Ours / DualMap** = 论文自身方法；**ConceptGraphs [4]、HOV-SG [5]** = 论文复现的对比方法。TABLE XII 是同一批对比在 **ViT-H/14 vs Mobile-CLIP** 两种 backbone 下的完整版。

| 出处（表/图 + 页） | 数据集 / 场景 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| **TABLE II, p.6** | **Replica** | **Ours（自家）** | **mIoU / FmIoU / mAcc / ODR / Avg.Mem(MB) / Peak.Mem(MB) / TPF(s)** | **0.2538 / 0.5207 / 0.4024 / 0.97 / 3095.2 / 4564.0 / 0.276** |
| TABLE II, p.6 | Replica | ConceptGraphs（对比，论文复现） | 同上 | 0.1501 / 0.3858 / 0.3559 / 2.02 / 7148.9 / 23551.9 / 4.188 |
| TABLE II, p.6 | Replica | HOV-SG（对比，论文复现） | 同上 | 0.2050 / 0.4846 / 0.3835 / 3.81 / 73368.0 / 158126.6 / 42.005 |
| **TABLE II, p.6** | **ScanNet** | **Ours（自家）** | **mIoU / FmIoU / mAcc / ODR / Avg.Mem(MB) / Peak.Mem(MB) / TPF(s)** | **0.1604 / 0.3288 / 0.3794 / 2.56 / 2120.9 / 2820.2 / 0.163** |
| TABLE II, p.6 | ScanNet | ConceptGraphs（对比） | 同上 | 0.0882 / 0.3077 / 0.3538 / 6.97 / 9780.3 / 26155.2 / 6.301 |
| TABLE II, p.6 | ScanNet | HOV-SG（对比） | 同上 | 0.1333 / 0.3381 / 0.3714 / 20.34 / 9223.0 / 25735.0 / 8.039 |
| TABLE III (Static), p.6 | HM3DSem 00829/00848/00880 | **Ours（自家）** | 各场景 SR / 平均 SR（78 trials） | 73.1% / 69.2% / 69.2% → **Avg. SR 70.5%** |
| TABLE III (Static), p.6 | HM3DSem | ConceptGraphs（对比） | 各场景 SR / 平均 SR | 69.2% / 53.8% / 61.5% → 61.5% |
| TABLE III (Static), p.6 | HM3DSem | HOV-SG（对比） | 各场景 SR / 平均 SR（78 trials） | 53.8% / 46.2% / 57.7% → 52.6% |
| **TABLE III (Dynamic), p.6** | HM3DSem + YCB | **Ours — In-anchor relocation** | 各场景 SR / 平均 SR（54 trials） | 66.7% / 66.7% / 61.1% → **Avg. SR 64.8%** |
| **TABLE III (Dynamic), p.6** | HM3DSem + YCB | **Ours — Cross-anchor relocation** | 各场景 SR / 平均 SR（53 trials） | 55.6% / 61.1% / 64.7% → **Avg. SR 60.3%** |
| TABLE IV, p.7 | Replica | **Full System（自家完整版）** | FmIoU / mAcc / mIoU | 0.5207 / 0.4024 / 0.2538 |
| TABLE IV, p.7 | Replica | w/o Object Split Detection（消融） | FmIoU / mAcc / mIoU | 0.5065 / 0.3998 / 0.2496 |
| TABLE IV, p.7 | Replica | w/o YOLO Refinement（消融） | FmIoU / mAcc / mIoU | 0.5043 / 0.3886 / 0.2399 |
| TABLE IV, p.7 | Replica | w/o FastSAM（消融） | FmIoU / mAcc / mIoU | 0.4753 / 0.3685 / 0.2344 |
| TABLE IV, p.7 | Replica | w/o Weighted Feats（消融） | FmIoU / mAcc / mIoU | 0.4209 / 0.3348 / 0.1814 |
| TABLE V, p.7 | ScanNet | Obj.Merging✓ Stability✓ Closed-set Det.✓（= 本文配置） | ODR / TPF(s) | 2.56 / 0.163 |
| TABLE V, p.7 | ScanNet | Obj.Merging✓ Stability✓ Closed-set Det.✓ | ODR / TPF(s) | 2.41 / 0.3056 |
| TABLE V, p.7 | ScanNet | Obj.Merging✓ Stability✗ Closed-set Det.✓ | ODR / TPF(s) | 26.5 / 2.841 |
| TABLE V, p.7 | ScanNet | Obj.Merging✓ Stability✗ Closed-set Det.✗（= HOV-SG 配置） | ODR / TPF(s) | 34.2 / 27.04 |
| **TABLE VI, p.7** | HM3DSem（ycb 物体被搬迁后） | Random Pick（候选选择基线） | SR | 13.2% |
| **TABLE VI, p.7** | HM3DSem | Based on **M_a**（原 abstract map） | SR | 47.2% |
| **TABLE VI, p.7** | HM3DSem | Based on **M′_a**（在线更新后） | SR | **60.3%** |
| TABLE VII, p.8 | 真实世界 Wheeled / Meeting Room | DualMap | Static Trials / SR；Dynamic Trials / SR | 14 / **85.7%**；27 / **70.3%** |
| TABLE VII, p.8 | 真实世界 Wheeled / Apartment | DualMap | Static Trials / SR；Dynamic Trials / SR | 46 / 69.6%；33 / 51.5% |
| TABLE VII, p.8 | 真实世界 Quadruped / Indoor Hallway | DualMap | Static Trials / SR；Dynamic Trials / SR | 19 / 78.9%；27 / 55.6% |
| TABLE VII, p.8 | 真实世界 Quadruped / Outdoor | DualMap | Static Trials / SR；Dynamic Trials / SR | 12 / 75.0%；18 / 50.0% |
| TABLE XII, p.12 | Replica | DualMap(Ours), **ViT-H/14** | mIoU / FmIoU / mAcc / ODR / Avg.Mem / Peak.Mem / TPF | 0.2323 / 0.4859 / 0.3832 / 0.974 / 3281.5 / 4688.9 / 0.458 |
| TABLE XII, p.12 | Replica | DualMap(Ours), **Mobile-CLIP** | 同上 | 0.2538 / 0.5207 / 0.4024 / 0.967 / 3095.2 / 4564.0 / 0.276 |
| TABLE XII, p.12 | ScanNet | DualMap(Ours), ViT-H/14 | 同上 | 0.1611 / 0.3179 / 0.3632 / 2.55 / 2607.5 / 4428.6 / 0.306 |
| TABLE XII, p.12 | ScanNet | DualMap(Ours), Mobile-CLIP | 同上 | 0.1604 / 0.3288 / 0.3794 / 2.56 / 2120.9 / 2820.2 / 0.163 |
| TABLE XIII, p.12 | Replica（RTX 4090） | DualMap 总 TPF 分解 | 总 TPF(s) / Observation Generation / Mapping / Visualization | 0.2524 / 0.2183 / 0.0485 / 0.0341 |
| TABLE XIV, p.13 | Replica 1200×680 | DualMap on **RTX 4090 Desktop** | FmIoU / mAcc / mIoU / TPF(s) / Rel.FmIoU / Rel.TPF | 0.5508 / 0.4251 / 0.2508 / 0.2524 / 100.00% / 100.00% |
| TABLE XIV, p.13 | Replica 1200×680 | DualMap on **RTX 3080 Laptop** | 同上 | 0.5503 / 0.4256 / 0.2502 / 0.4045 / 99.92% / 160.26% |
| TABLE XIV, p.13 | Replica 960×540 | DualMap on RTX 3080 Laptop | 同上 | 0.5507 / 0.4259 / 0.2526 / 0.3221 / 99.98% / 127.61% |
| TABLE XIV, p.13 | Replica 640×360 | DualMap on RTX 3080 Laptop | 同上 | 0.5341 / 0.3941 / 0.2428 / 0.2717 / 96.97% / 107.65% |
| TABLE XIV, p.13 | Replica 320×180 | DualMap on RTX 3080 Laptop | 同上 | 0.2646 / 0.1437 / 0.0801 / 0.2538 / 48.04% / 100.55% |
| TABLE XI, p.10 | Replica | 特征权重 f_image=0.7 / f_text=0.3（论文最终选择） | FmIoU / mAcc / mIoU | 0.551 / 0.425 / 0.251 |
| TABLE XI, p.10 | ScanNet | 特征权重 f_image=0.7 / f_text=0.3 | FmIoU / mAcc / mIoU | 0.334 / 0.371 / 0.167 |
| TABLE IX, p.10 | HM3DSem（In-anchor 明细） | DualMap | 各场景成功数汇总 | 12/18、12/18、11/18 |
| TABLE X, p.10 | HM3DSem（Cross-anchor 明细） | DualMap | 各场景成功数汇总 | 10/18、12/18、10/17 |
| Fig. 12, p.13 | Replica（RTX 4090） | DualMap 运行时占比 | Model Inference / Other Modules / Visualization | 57.9% / 28.7% / 13.5% |
| §V-C, p.7（正文文字） | HM3DSem cross-anchor 失败案例 | DualMap | 失败归因占比 | false matches 28.3% / 超出导航尝试次数 9.4% / planning errors 1.9% |
| §V-C, p.6（正文文字） | Replica | DualMap vs HOV-SG / ConceptGraphs | mIoU 提升幅度 | +2.8%（vs HOV-SG）、+10.3%（vs ConceptGraphs）；peak memory 降低 >96%；TPF 降低 99.3% |

**论文自报但未给数值的超参**（供复现时参考）：Δτ = 0.05（anchor/volatile 判别 margin）、τ_a = 0.5、δ = 0.1 m（"on" 关系垂直距离阈值）、颜色直方图合并阈值 0.95、颜色直方图 16 等宽 bins。**τ1 与 τ2（abstract map 更新的 overlap 阈值）在 PDF 中未给出具体数值 —— 未找到**（检索 `τ1`、`τ2` 全 15 页，只在公式描述中出现符号，无数值）。

## 关键结论（论文自己声称的）

- **语义分割 SOTA + 效率碾压**：TABLE II 上 Replica FmIoU **0.5207**（HOV-SG 0.4846、ConceptGraphs 0.3858）、mIoU **0.2538**（比 HOV-SG 高 2.8%、比 ConceptGraphs 高 10.3%）；峰值内存 **4564.0 MB** 对比 HOV-SG **158126.6 MB**（>96% 降幅），TPF **0.276 s** 对比 HOV-SG **42.005 s**（99.3% 降幅）。
- **ODR 最接近真值**：Replica 上 ODR = **0.97**（ConceptGraphs 2.02、HOV-SG 3.81），即物体数量估计最准、过分割最少；ScanNet 上 ODR = **2.56**（ConceptGraphs 6.97、HOV-SG 20.34）。
- **导航成功率最高**：静态 HM3DSem 平均 SR **70.5%**（ConceptGraphs 61.5%、HOV-SG 52.6%）；动态场景 In-anchor **64.8%**、Cross-anchor **60.3%**，说明物体跨 anchor 搬家后仍能靠在线更新找回。
- **在线地图更新是跨 anchor 成功的关键**：TABLE VI 里用 **M′_a（更新后）** 的 SR **60.3%**，远高于用原 **M_a** 的 **47.2%** 与随机选的 **13.2%** —— 这是论文对 "地图修订有用" 最直接的量化证据。
- **降分辨率可救低端卡**：TABLE XIV 上 RTX 3080 Laptop 在 640×360 下 FmIoU 仅掉 ~3%（0.5341 vs 0.5508），TPF 0.2717 s；但降到 320×180 时 FmIoU 崩到 0.2646（48.04%）。

## 跨会话身份 / 地图修订：论文报告了什么

**地图修订：有量化结果（但是单次会话内的在线更新，不是跨会话）。**

- **TABLE VI, p.7**（最关键）：物体被搬迁后，候选选择策略从 `Random Pick` **13.2%** → `Based on M_a`（未更新）**47.2%** → `Based on M′_a`（在线更新后）**60.3%** SR。
- **TABLE III (Dynamic), p.6**：In-anchor relocation **64.8%**（54 trials）、Cross-anchor relocation **60.3%**（53 trials）。定义见 §V-A-1：In-anchor = 物体在同一 anchor 内移动（如桌上杯子挪位）；Cross-anchor = 物体跨 anchor 移动（如从桌子到架子）。
- **TABLE IX / TABLE X, p.10**：逐次搬迁的明细成功记录（In-anchor 12/18、12/18、11/18；Cross-anchor 10/18、12/18、10/17），每个 YCB 物体在 in-anchor 和 cross-anchor 各被搬 3 次。
- **§IV-D Map Update Mechanism, p.5**：新 anchor 与已有 anchor 算几何 overlap `s_overlap`，> τ1 则当作同一 anchor 的额外观测更新点云与特征（size-weighted average，eq. 7），> τ2 则额外替换 volatile 特征列表。**但 τ1/τ2 数值论文未给**。

**跨会话物体身份：论文未报告。**

DualMap 的 dual-map 更新发生在**一次连续的在线建图/导航会话内**（机器人边导航边累积 `M_local_c` 并合并进 `M_a`）。全文检索 `cross-session`、`multi-session`、`across session`、`revisit`、`second visit`、`repeat visit`、`relocaliz`、`identity`、`re-identify`、`change detection` 均**未命中任何跨会话实验或指标**。它也没有 "物体没动但标签应该变" 的评测 —— 它测的是 "物体移动了、系统能否在 3 次尝试内找回来"，而不是 "同一个物体在多次访问间是否保持同一 ID"。

（补充：论文 §VI Limitations 明确列出第一、二条限制为 "does not perform camera pose estimation and instead relies on external localization systems" 与 "does not yet incorporate human-object interactions"。）

## 对我们的复现意味着什么

- **可复现的前提**：
  - **GPU（硬性）**：主实验用 **NVIDIA RTX 4090（24 GB）**；补充实验证明 **RTX 3080 Laptop（16 GB）在 640×360 下可用**（TABLE XIV，FmIoU 0.5341 / TPF 0.2717 s）。也就是说论文自己给出了**16 GB 显存级别的最低可用配置**。**本机无 GPU → 仍不可直接复现**，但论文是我们这四篇里唯一明确给出低端卡降级方案的。
  - **数据集**：Replica + ScanNet（scene0011_00 等 5 个场景，用 ScanNet200 标注）+ **HM3DSem（00829/00848/00880）**。HM3DSem 属于 Habitat-Matterport 3D 系列，**通常需要签署 access agreement** 才能下载；YCB 物体模型需要在 Habitat 里手动摆放（Fig. 7）。
  - **依赖**：YOLOv8l-world + FastSAM-s + **MobileCLIP-S2** + GPT-4（仅用于离线生成一个 indoor 类名列表，prompt 已在附录 I 全文给出，**可以一次生成后固定，不必每次跑**）。类名列表本身也在 PDF 里给全了，这点对复现很友好。
  - **代码**：项目页 `https://eku127.github.io/DualMap/`，README 指向 `github.com/Eku127/DualMap`（带 ROS 支持）。
- **目标数字**（建议验收线，优先级从高到低）：
  1. **TABLE II, p.6, Replica**：`FmIoU = 0.5207`、`mIoU = 0.2538`、`mAcc = 0.4024`、`ODR = 0.97`、`TPF = 0.276 s`（RTX 4090，MobileCLIP-S2）。
  2. **TABLE XIV, p.13**：若只有低端卡，对齐 640×360 行的 `FmIoU = 0.5341`（注意：该行的分辨率与主表不同，**不能与 0.5207 直接比较**）。
  3. **TABLE VI, p.7**：地图修订的 `SR = 60.3%`（M′_a）—— 这是我们 "地图修订" 课题最该对照的单点。
  4. **TABLE III, p.6**：静态 `Avg. SR = 70.5%`。
- **对不上的可能原因**：
  - **CLIP backbone 差异**：主表用 **MobileCLIP-S2**（TABLE XII 里 ViT-H/14 与 Mobile-CLIP 结果不同，Replica FmIoU 0.4859 vs 0.5207）。用错 backbone 直接对不上。
  - **分辨率未在主表声明**：TABLE II 只说 "at the original image resolutions"，TABLE XIV 才出现 1200×680 等具体分辨率，且 TABLE XIV 的 FmIoU（0.5508）高于 TABLE II（0.5207）——**两套数字的评测配置不同**，混用会得出错误结论。
  - **场景划分**：Replica 用 office0–office4 + room0–room2（8 场景），ScanNet 用 ScanNet200 的 5 个场景 —— 与 ConceptGraphs/HOV-SG 论文自己报的 ScanNet/Replica 数字**不是同一套评测代码**（DualMap 是复现基线后重新测的）。
  - **背景类排除**：论文明确排除 `wall`/`floor`/`ceiling`，不排除会得到完全不同的 mIoU。
  - **HM3DSem 的 YCB 摆放是人工的**（Fig. 7、TABLE VIII 列出 YCB 型号 003 cracker box / 005 tomato soup can / 011 banana / 019 pitcher base / 024 bowl / 025 mug / 029 plate / 037 scissors），位置无法精确复刻。
  - **τ1、τ2 未给数值**，map update 的触发条件无法精确复刻。
  - Hybrid 前端（YOLOv8l-world 输出顺序、FastSAM 随机性）与 GPU 浮点非确定性会带来逐帧差异。
- **阻塞风险**：
  - **本机无 GPU → 完全阻塞**。语义分割与 TPF 指标必须在 GPU 上测；TPF 更是强依赖硬件（TABLE XIV 显示 3080 Laptop 比 4090 慢 1.6×）。
  - **HM3DSem 需要 access agreement**（Matterport 条款），导航相关结果（TABLE III/V/VI）都建立在它之上；若拿不到，只能复现 Replica/ScanNet 的分割部分。
  - **Habitat Simulator + YCB 动态摆放**的工程量不小（论文自建了基于 Habitat 的动态摆放工具）。
  - 论文 §VI 自承：不做位姿估计，依赖外部定位（真实实验用 FastLIO2）；室外场景性能明显下降；未建模人物交互。
  - 本 PDF 是 **arXiv v4（2025-12）**，数字可能随版本变动，引用时需锁版本。
