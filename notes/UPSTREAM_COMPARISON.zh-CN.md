# 作者原库与本复现库：逐项对照

[English](UPSTREAM_COMPARISON.md) | [索引](README.zh-CN.md)

本文对照的是原有运行层及子集。新增独立原始流程的固定版本、完整公开数据和当前状态在 [作者复现分支](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals)；结果关联见 [新增分析](AUTHOR_RESULTS_ANALYSIS.zh-CN.md)。

本库是**作者核心的运行、适配、评价与证据组织层**。它没有重写四个算法，也没有完成四篇全部实验。对照时看固定快照与每次运行的实际副本，作者仓库当前默认分支可能已经改变。

## 1. 原库入口与固定版本

| 原库 | 本库固定源码快照 | 版本记录 |
| --- | --- | --- |
| [DUFOMap](https://github.com/KTH-RPL/dufomap) | [9e239ddd](https://github.com/KTH-RPL/dufomap/tree/9e239ddd5995136e14f5212f33382a6ebc59e518) | [upstreams.json](../configs/upstreams.json)；**实际执行作者 PyPI `dufomap==1.1.1`，不是声称从此 Git 提交编译** |
| [BeautyMap](https://github.com/MKJia/BeautyMap) | [98bce4a9](https://github.com/MKJia/BeautyMap/tree/98bce4a97db96ddd0d5342e31425c7679f58ba2e) | [upstreams.json](../configs/upstreams.json) |
| [ConceptGraphs](https://github.com/concept-graphs/concept-graphs) | [93277a02](https://github.com/concept-graphs/concept-graphs/tree/93277a02bd89171f8121e84203121cf7af9ebb5d) | [semantic.json](../configs/semantic.json) |
| [HOV-SG](https://github.com/hovsg/HOV-SG) | [d6e65a53](https://github.com/hovsg/HOV-SG/tree/d6e65a53c8be6faec3f01f00d1644d967f89e605) | [hovsg.json](../configs/hovsg.json) |
| [DynamicMap_Benchmark：评价器](https://github.com/KTH-RPL/DynamicMap_Benchmark) | [8b60f36a](https://github.com/KTH-RPL/DynamicMap_Benchmark/tree/8b60f36a735a910b8c54b7eb12438db76fb32460) | 原 PCL 地图评价与本库 SciPy 实现逐点对照 |
| [gradslam：ConceptGraphs 依赖](https://github.com/gradslam/gradslam) | [59ca872e](https://github.com/gradslam/gradslam/tree/59ca872e3d265ad09f63c4793d011fad67064452) | [semantic.json](../configs/semantic.json)；本次提供位姿建图不等于运行 gradslam 轨迹估计 |

SAM、CLIP 权重的仓库、revision、SHA256 同样在 `semantic.json`。CPU／语义／HOV 使用不同环境，不能混装锁定依赖。

## 2. 真正调用了作者的哪一段

| 方法 | 作者源码入口 | 本库入口与不变的核心 |
| --- | --- | --- |
| DUFOMap | [main.py](https://github.com/KTH-RPL/dufomap/blob/9e239ddd5995136e14f5212f33382a6ebc59e518/main.py)，Python binding | [adapters.py](../src/slam_learning/adapters.py)：调用 `run`、`oncePropagateCluster`、`outputMap`；作者占据／空域分类核心由 1.1.1 binding 执行 |
| BeautyMap | [main.py](https://github.com/MKJia/BeautyMap/blob/98bce4a97db96ddd0d5342e31425c7679f58ba2e/main.py)、`lib/bee_tree.py` | [adapters.py](../src/slam_learning/adapters.py)：复制作者源码到本次 `author-code/`，调用其 `main.py`；二进制占据、地面适应和恢复核心保留 |
| ConceptGraphs | [generate_gsa_results.py](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/conceptgraph/scripts/generate_gsa_results.py)、[cfslam_pipeline_batch.py](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/conceptgraph/slam/cfslam_pipeline_batch.py) | [run_conceptgraphs.py](../scripts/run_conceptgraphs.py)：作者 class-agnostic SAM／CLIP 前端、空间／语义关联和融合 |
| HOV-SG | [application/semantic_segmentation.py](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/application/semantic_segmentation.py)、[hovsg/graph/graph.py](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/hovsg/graph/graph.py) | [run_hovsg.py](../scripts/run_hovsg.py)：载入作者配置，构造 `Graph`，调用 `create_feature_map()`；保存原生分段点云和特征 |

作者 README 中 ConceptGraphs 有无检测器两条路径；本次只走 `class_set=none`。HOV-SG 的层级图 `application/create_graph.py` 是另一条更完整路径，本次没有执行它。

[ConceptGraphs 固定 README](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/README.md) · [HOV-SG 固定 README](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/README.md)。

作者 README 的命令形式如下，便于与包装器的实际 `commands` 对照；其工作目录分别是作者 checkout、数据和权重需按各 README 准备。这些不是在本库根目录直接运行的命令。

| 作者流程 | 原入口形式 | 本库为何包一层 |
| --- | --- | --- |
| DUFOMap | `python main.py --data_dir data/00`，另有 C++ `dufomap_run` | 锁 binding 与参数，统一记录、独立输出与评价 |
| BeautyMap | `python main.py --data_dir data/00 --dis_range 40 --xy_resolution 1 --h_res 0.5` | 隔离补丁、移除 GT 字段、固定输入与运行证据 |
| ConceptGraphs | `python scripts/generate_gsa_results.py ... --class_set none --stride 5`，再 `python slam/cfslam_pipeline_batch.py ... stride=5` | 原库先 `cd conceptgraph`；本库已先按源索引每5帧暂存40观测，内部 `stride=1` 避免再次每5帧采样 |
| HOV-SG | `python application/semantic_segmentation.py main.dataset=replica main.dataset_path=Replica/office0 main.save_path=data/sem_seg/office0` | 本库直接调用同一 `Graph.create_feature_map()` 核心，记录 room0 子集、适配和产物；未执行后续官方语义评分 |

## 3. 我们改动或选择了什么

| 方法 | 适配／设置 | 为什么；对比较有什么限制 |
| --- | --- | --- |
| DUFOMap | 统一 PCD／VIEWPOINT 读取、范围过滤 0.2–50 m、隔离输出；参数 `resolution=0.1,d_s=0.2,d_p=1,threads=2` | `d_p=1` 对照论文；缓存作者 demo 的 `d_p=2` 是另一个工作点。未改 binding 核心，不能以此保证和论文时期二进制完全一致 |
| BeautyMap | Python `map` 迭代器转 list；`dtype=int` 显式改 `np.int64`；扫描和原始地图物理移除 GT intensity、保留 XYZ／VIEWPOINT | 解决读取兼容与 Windows 位掩码溢出，防止标签泄漏；参数仍为 `dis_range=40,xy_resolution=1,h_res=0.5`。补丁只落在每次副本，原库缓存保持干净 |
| ConceptGraphs | TkAgg→Agg；跳过本次无用的 GroundingDINO／RAM 初始化；固定本地 CLIP 权重；SAM batch 144→36，仍用 12×12 提示格 | 适应无头运行和 12 GiB GPU；**没有证明 batch 改动后掩码与 144 完全一致**。保持基线关联阈值 1.2 等声明设置，另存 1.0／1.4 探索对照 |
| HOV-SG | RGB／depth 调至 640×360，内参 x/y 分别缩放；SAM batch36、CLIP batch4；40 观测暂存集再 `skip_frames=5` | 实际处理源帧 0,25,…175 共 8 次。40 观测尝试 exit137、原因未确认。分割／融合阈值来自固定作者配置，不能声称全量结果或原分辨率数值等价 |

补丁：[BeautyMap](../results/reference/beautymap-wsl/compatibility.patch) · [ConceptGraphs](../results/reference/conceptgraphs-wsl/compatibility.patch) · [HOV-SG](../results/reference/hovsg-wsl/compatibility.patch)。BeautyMap 的 `.patch` 是替换摘要和计数，不是可直接交给 `git apply` 的完整 unified diff；实际副本可以用下面的命令逐文件比对。

## 4. 复现程度与结果差距

| 项目 | 原论文／原库完整目标 | 本库达到的范围与差距 |
| --- | --- | --- |
| DUFOMap | 动态感知建图、多数据评价及效率 | 完整公开 KITTI-00 **teaser**，141 扫描／17,362,230 标注点；不等于 KITTI00 完整原始行驶序列。SA/DA/AA 实测 97.979798/98.702895/98.340682%，论文 97.96/98.72/98.34% |
| BeautyMap | 动态点移除、多场景比较 | 同一 teaser，SA/DA/HA 实测 96.952945/98.338247/97.640683%，论文 96.76/98.38/97.56%。未达到全部 0.01 百分点容差 |
| ConceptGraphs | 开放词汇对象图、语义评价、LLM 关系／规划等 | room0 源帧 0,5,…195，共 40 观测、39 对象，提供绝对姿态；未运行完整 Replica 语义评价、ConceptGraphs-Detect、LLM 关系图或导航 |
| HOV-SG | 对象／房间／楼层层级图、查询、导航和语义评价 | 八观测分段特征核心，50 分段、166,777 点；未完成完整层级、语义 benchmark、导航或在线更新 |

LiDAR 使用 5 cm 地图近邻评价，原作者 PCL 与本库 SciPy 对已保存地图逐点零分歧；这排除该次地图上的评价实现差异，仍不能解释全部论文时期差距。DUFOMap AA 是几何平均，BeautyMap HA 是调和平均。

语义对象／分段数只证明产物存在，不是准确率。本库新增的四个部分表面、受限查询、位姿扰动、来源记录和 RViz 回放属于自己的诊断层；它们不替代作者官方 benchmark，也不代表 H1 已实现。[详细成绩](../docs/RESULTS.zh-CN.md) · [语义边界](../docs/SEMANTIC.zh-CN.md) · [研究关联](../docs/STUDY.zh-CN.md)。

## 5. 本机怎样打开原库和实际运行副本

**PowerShell**：打开 WSL 源码目录，选原库 README 或源码查看；当前个人分支没有复制这些大缓存。

```powershell
explorer.exe '\\wsl.localhost\Ubuntu-22.04\home\qzl\projects\SLAM_Learning\.cache\upstream'
wsl -d Ubuntu-22.04 -u qzl
```

**WSL Bash**：核对原库提交和干净状态，再读固定 README。

```bash
cd /home/qzl/projects/SLAM_Learning
git -C .cache/upstream/conceptgraphs rev-parse HEAD
git -C .cache/upstream/conceptgraphs status --short
less .cache/upstream/conceptgraphs/README.md
```

退出 `less` 按 `q`。将 `conceptgraphs` 换成 `beautymap`、`dufomap`、`hovsg` 查看其他原库。不要在 `.cache/upstream` 里直接改代码，运行器会检查固定版本／干净状态。

以已存在的 ConceptGraphs 基线为例：

```bash
cat results/runs/conceptgraphs-7795d7b47007/compatibility.patch
diff -u .cache/upstream/conceptgraphs/conceptgraph/scripts/generate_gsa_results.py \
  results/runs/conceptgraphs-7795d7b47007/author-code/conceptgraph/scripts/generate_gsa_results.py
cat results/runs/conceptgraphs-7795d7b47007/record.json
```

`diff` 返回 1 表示有差异，正常；2 才是读取等错误。运行记录的 `commands` 给实际完整命令，不要用 README 的占位数据路径冒充该次运行。

BeautyMap 比 `utils/pcdpy3.py`、`main.py`、`lib/bee_tree.py`；HOV 比 `hovsg/utils/clip_utils.py`，同时看 `effective-config.yaml`、`derived-input.json` 和 `frame_observations.json`。

**实际运行命令只用[Windows 操作手册](WINDOWS_START.zh-CN.md)的包装入口**；直接照原库 README 重跑需要另备数据、权重和环境，会失去本库自动记录与隔离。先读对照，再决定是否单独做作者原配方实验。
