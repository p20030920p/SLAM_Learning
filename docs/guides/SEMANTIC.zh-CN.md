# ConceptGraphs 前端复现

[English](SEMANTIC.md) | 中文

本轮扩展：[配对结果](../research/PAIRED_RESULTS.zh-CN.md) 补受限标注、97 个建图单元、简单对照及收窄的候选 H1。先前基线 PDF 保留其记录的源快照，配对研究 PDF 是本轮扩展。

2026 年 10 月 8 日，固定源码的作者 **class-agnostic ConceptGraphs** 前端已在本机 WSL2 Ubuntu 22.04、RTX 4070 SUPER 执行。Replica `room0` 的 40 次观测得到 **39 个后处理对象**；4 个 CLIP 文本查询各返回 3 个候选对象及其世界坐标。[运行记录](../../results/reference/conceptgraphs-wsl/record.json)、[输出](../../results/reference/conceptgraphs-wsl/summary.json)、[原生建图日志](../../results/reference/conceptgraphs-wsl/mapping.log)。

这建立了可执行的 RGB-D 分割、对象关联／融合、坐标查询基线。查询正确率、语义榜单分数、动态场景性能、导航成功率**尚未评价**。返回坐标不证明找对目标。相机到世界的位姿由数据提供，不是 SLAM 估计结果；本次也未运行 LLaVA 描述、LLM 场景图构建或规划。

## 运行独立环境

在 `~/projects/SLAM_Learning` 中完成 [Linux 环境](REPRODUCE.zh-CN.md)后：

```bash
bash src/scripts/setup/setup_semantic.sh
.venv-semantic/bin/python src/scripts/methods/run_conceptgraphs.py
```

CPU 的 `src/uv.lock` 环境与语义环境分开。[语义依赖](../../src/configs/environments/semantic/requirements.txt)固定已安装发行版，[semantic.json](../../src/configs/semantic.json)固定作者提交、权重、PyTorch3D 二进制和参数。实测 Python 3.10.12、PyTorch 2.0.1+cu118、PyTorch3D 0.7.4。脚本校验作者推荐的 Linux 二进制 SHA-256，只安装到项目语义环境，不要求系统 CUDA 工具链。这套安装步骤已实际执行。

## 数据与位姿

[作者说明](https://github.com/concept-graphs/concept-graphs)使用 [NICE-SLAM 渲染的 Replica 轨迹](https://github.com/cvg/nice-slam/blob/master/scripts/download_replica.sh)。公开 ZIP 为 12,442,855,671 字节；HTTP Range 只获取来源帧 `000000、000005、…、000195`、深度和 `traj.txt`，没有宣称整个压缩包的 SHA-256。Zip CRC 校验下载成员，[清单](../../results/reference/conceptgraphs-wsl/dataset-manifest.json)保存提取文件 SHA-256、压缩包长度和 ETag。

对应的 40 个原始位姿矩阵按观测顺序紧凑排列。作者 loader 对子集取 stride 1，相当于对原始前 200 个条目取 stride 5。建图采用作者的 480×640 图像设置、缩放后的内参和提供的世界位姿。它是短小的静态渲染场景，不是实机部署，也不是完整 Replica 论文评价。

每次运行获得独立的 RGB-D 子集与作者源码副本，不会把旧检测或旧地图当作新结果。权重和 RGB-D 数据不进入 Git。

## 兼容性与资源适配

[完整补丁](../../results/reference/conceptgraphs-wsl/compatibility.patch)记录无窗口 Matplotlib、在 `class_set=none` 下跳过未使用的 GroundingDINO／RAM 导入和初始化、本地权重路径、SAM 分批。几何、关联公式和判断阈值未打补丁。

作者默认一次处理 144 个 SAM 采样提示。在本机 12 GiB 显卡上，首帧显存饱和并停滞，因此主动中止并保留[中止运行](../../results/reference/conceptgraphs-wsl-batch144-interrupted/record.json)。成功运行保留 12×12 采样网格，分成每批 36 点。分批是明确的资源适配，未宣称与未适配参考产生逐位相同的掩膜。40 个输入全部完成分割后，才进入建图。

Meta 下载停滞后，SAM ViT-H 从固定修订的 Hugging Face 镜像获取；CLIP ViT-H 来自 LAION 模型库。两者加载前检查完整文件哈希；镜像来源和修订明确写在配置中。没有用父进程数据宣称完整系统速度或显存峰值。

## 基线告诉了我们什么？

作者建图日志记录对象增加、过滤和合并。这些操作处理 RGB-D 与基础模型特征，已经超出使用已知对象身份的玩具模型；但最终对象数量本身不能衡量碎片化或正确关联。公布的查询分数是余弦相似度，不是校准概率。

配对扩展已补四个部分表面目标、固定特征位姿误差对及阈值对照。完整身份真值、动态语义召回、匹配覆盖／延迟仍待完成。[结果与限制](../research/PAIRED_RESULTS.zh-CN.md)。H1 保持候选，留出确认尚未开始。

## HOV-SG：第四篇建图核心

`bash src/scripts/setup/setup_hovsg.sh` 准备独立 `.venv-hovsg`，再运行 `.venv-hovsg/bin/python src/scripts/methods/run_hovsg.py`。它共享已经校验的 Replica 子集／权重，安装固定的 [HOV-SG 依赖](../../src/configs/environments/hovsg/requirements.txt)，无需 PyTorch3D。

原安装快照含 HF Hub 2.x／OpenAI 1.3.7 依赖冲突。安装配方改用 HF Hub 0.23.5 加载本地权重，移除未用且不兼容的 httpx2，并运行 `uv pip check`。历史运行环境记录保持原样。

成功运行处理源帧 0,25,...175，共 8 次观测，产生 50 分段及 166,777 参考点。RGB／深度缩放为 640×360，两个内参轴分别缩放；SAM 批量 36、CLIP 批量 4。作者几何合并和特征筛选实际执行，阈值不变。未执行楼层／房间层级、语义 mIoU 或导航。50 分段不能与 39 对象排名。

首次 40 观测完成前端后，合并进程被终止，退出码 137；未确认原因，不声称已确诊 OOM。[失败记录](../../results/reference/hovsg-wsl-interrupted/record.json)与[成功记录](../../results/reference/hovsg-wsl/record.json)独立保留。成功建图进程测得 PyTorch 分配峰值 10,030,088,704 字节，不含驱动分配。四文本查询返回坐标候选，正确性未评价。[论文卡／视频／PDF](../papers/hovsg.zh-CN.md)。

ConceptGraphs 实际批处理入口读取绝对 `dataset.poses`，绕过加载器默认归一化；39 个保存相机矩阵已与给定位姿核对，历史世界坐标正确，无须额外第一帧变换。两种语义视频都回放最终地图，不表现为在线演化。[录制及坐标审计](RECORDING.zh-CN.md)。

修正安装已再次实际执行，142 个安装包通过兼容检查。新的[依赖解决后重复运行](../../results/reference/hovsg-wsl-resolved/record.json)完成 8 观测，复得 50 分段／166,777 点；地图 PLY 与分段特征 NPY 和先前核心运行字节一致。这次本机重复不能证明其他硬件／设置下确定性。
