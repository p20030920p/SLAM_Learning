# 从 Windows 到作者入口

[English](RUNBOOK.md) | 中文

本机使用 Windows + WSL Ubuntu-22.04。文档分支在 `D:\workspace\be2\SLAM_Author_Originals`，实际编译和执行在 `/home/qzl/projects/SLAM_Author_Originals`。不要在已有主分支缓存里覆盖源代码或重跑输出。

## 1. 打开工作区

PowerShell：

```powershell
Set-Location D:\workspace\be2\SLAM_Author_Originals
git status --short
wsl -d Ubuntu-22.04 -u qzl
```

进入 Ubuntu 后：

```bash
export DOCS=/mnt/d/workspace/be2/SLAM_Author_Originals
export RUNTIME=/home/qzl/projects/SLAM_Author_Originals
cd "$RUNTIME"
```

如果在另一处重新克隆，使用专用分支并只初始化需要的作者子模块：

```bash
git clone --branch reproduce/author-originals --single-branch \
  https://github.com/p20030920p/SLAM_Learning.git SLAM_Author_Originals
cd SLAM_Author_Originals
git submodule update --init src/upstream/dufomap src/upstream/beautymap src/upstream/conceptgraphs src/upstream/hovsg src/upstream/dynamicmap
git -C src/upstream/dufomap submodule update --init --recursive
```

Linux 原生目录的另一套干净作者源码可以用以下脚本建立；已存在但提交不匹配或有修改时，脚本拒绝覆盖：

```bash
python3 "$DOCS/src/scripts/prepare_runtime.py" --runtime "$RUNTIME"
```

## 2. 检查已经完成的结果

```bash
cat "$RUNTIME/runs/lidar-evaluation-01/scores/run.log"
cat "$RUNTIME/runs/released-lidar-01/scores/run.log"
cat "$RUNTIME/runs/dufomap-cpp-original-command-01/record.json"
cat "$RUNTIME/runs/beautymap-original-command-01/record.json"
```

大点云本地位置：

- DUFOMap C++：`runs/dufomap-cpp-original-01/input/00/dufomap_output.pcd`
- BeautyMap：`runs/beautymap-original-01/input/00/beautymap_output.pcd`
- DUFOMap Python：`runs/dufomap-python-original-01/dufomap_output_voxel.pcd`
- 统一作者评价：`runs/lidar-evaluation-01/dataset/00/eval/`
- 四份公开数据：`runs/released-lidar-01/dataset/{00,05,av2,semindoor}/`

Windows 文件管理器也可以打开 `\\wsl.localhost\Ubuntu-22.04\home\qzl\projects\SLAM_Author_Originals`。

## 3. 原始 LiDAR 入口

新机器先准备作者依赖。Ubuntu 22.04 本轮成功工具链为 g++-11；推荐的 g++-10 失败记录见 evidence。

```bash
sudo apt-get update
sudo apt-get install -y g++-11 cmake libtbb-dev liblz4-dev liblzf-dev libpcl-dev libgoogle-glog-dev libgflags-dev
bash "$DOCS/src/scripts/setup_lidar.sh" "$RUNTIME"
git -C "$RUNTIME/upstream/dufomap" submodule update --init --recursive
cmake -S "$RUNTIME/upstream/dufomap" -B "$RUNTIME/build/dufomap-gcc11" -D CMAKE_CXX_COMPILER=g++-11
cmake --build "$RUNTIME/build/dufomap-gcc11" --parallel 2
cmake -S "$RUNTIME/upstream/dynamicmap/scripts" -B "$RUNTIME/build/dynamicmap"
cmake --build "$RUNTIME/build/dynamicmap" --target export_eval_pcd --parallel 2
```

本机已有只读用途的原始输入 `data/00-pristine`。新机器从作者提供的 [00.zip](https://zenodo.org/records/10886629/files/00.zip) 解压后放到这个位置。每次运行复制一套输入，防止算法生成物互相影响。以下 `manual-01` 必须是新的目录名：

```bash
mkdir -p "$RUNTIME/runs/manual-01/dufo" "$RUNTIME/runs/manual-01/beauty"
cp -a "$RUNTIME/data/00-pristine" "$RUNTIME/runs/manual-01/dufo/00"
cp -a "$RUNTIME/data/00-pristine" "$RUNTIME/runs/manual-01/beauty/00"
"$RUNTIME/build/dufomap-gcc11/dufomap_run" "$RUNTIME/runs/manual-01/dufo/00" "$RUNTIME/upstream/dufomap/assets/config.toml"
cd "$RUNTIME/upstream/beautymap"
"$RUNTIME/envs/lidar/bin/python" main.py --data_dir "$RUNTIME/runs/manual-01/beauty/00" --dis_range 40 --xy_resolution 1 --h_res 0.5
```

默认 Python 演示另跑，输出位置是当前目录：

```bash
mkdir -p "$RUNTIME/runs/manual-python-01"
cd "$RUNTIME/runs/manual-python-01"
"$RUNTIME/envs/lidar/bin/python" "$RUNTIME/upstream/dufomap/main.py" --data_dir "$RUNTIME/data/00-pristine"
```

`src/scripts/evaluate_lidar.py` 固定读取本轮三次真实运行的路径，用于重现已发布的评价。新建评价目录，不覆盖旧目录：

```bash
python3 "$DOCS/src/scripts/evaluate_lidar.py" --runtime "$RUNTIME" --name lidar-evaluation-manual-02
```

四份公开数据的完整运行记录在 `runs/released-lidar-01`。准备额外三份作者数据并重跑两种原始入口与作者评价：

```bash
python3 "$DOCS/src/scripts/fetch_benchmark.py" --runtime "$RUNTIME"
python3 "$DOCS/src/scripts/run_released_lidar.py" --runtime "$RUNTIME" --name released-lidar-manual-02
```

已有下载会校验后复用；运行目录名必须新建。四份公开数据全部完成不代表论文所有消融、完整 KITTI 序列或定位系统实验完成。

### 论文消融与无标注传感器示例

DUFOMap 表 IV 五组精度消融已完成，[论文逐项对照](../reports/DUFOMAP_TABLE4.zh-CN.md)提供 PowerShell 重做命令和原始日志。它使用作者 TOML 参数，不替换算法函数。

KTH campus（Leica，18 帧）和 twofloor（Livox，3305 帧）来自同一作者 Zenodo 发布版，**没有精度 GT**。下载与原始默认参数运行：

```bash
python3 "$DOCS/src/scripts/fetch_benchmark.py" --runtime "$RUNTIME" --qualitative-only
"$RUNTIME/envs/lidar/bin/python" "$DOCS/src/scripts/run_dufo_qualitative.py" \
  --runtime "$RUNTIME" --name dufomap-qualitative-manual-01
```

两份数据单独保存于 `data/benchmark-qualitative`，完成标准是完整帧数、原始入口退出成功、有限点坐标和文件哈希。点数减少不是动态剔除准确率；不要把它们加入有标签评分表。读取 `runs/dufomap-released-qualitative-01/outcomes.json` 判断本机是否已经完成。

## 4. 语义方法的原始命令

独立环境与 CUDA 构建说明见 [环境文档](ENVIRONMENT.zh-CN.md)。

完整 Replica 在 `data/replica-full/Replica`。下载、CRC、帧数与 SHA-256 核验见本地 `replica-full-manifest.json`。必须有完整 2000 帧，不能把旧的少帧示例当作完整数据。只读数据与算法写入的输出要逐项记录。

HOV-SG 作者环境首先按其 YAML 创建，另行安装 habitat-sim 用于 HM3D；Replica 语义入口自身不需要仿真器。未执行的命令不等于完成状态。

```bash
cd "$RUNTIME/upstream/hovsg"
"$RUNTIME/envs/hovsg/bin/python" application/semantic_segmentation.py \
  main.dataset=replica main.scene_id=room0 \
  main.dataset_path="$RUNTIME/data/replica-full/Replica/room0" \
  main.save_path="$RUNTIME/runs/hovsg-manual-01" \
  models.clip.checkpoint="$RUNTIME/weights/laion2b_s32b_b79k.bin" \
  models.sam.checkpoint="$RUNTIME/weights/sam_vit_h_4b8939.pth" \
  hydra.run.dir="$RUNTIME/runs/hovsg-manual-01/hydra"
```

ConceptGraphs 原始 detector-free 入口；原版 SAM 每批 144 个点，不悄悄调小：

```bash
export GSA_PATH="$RUNTIME/dependencies/Grounded-Segment-Anything"
export WANDB_MODE=disabled
export HF_HUB_CACHE="$RUNTIME/cache/huggingface/hub"
cd "$RUNTIME/upstream/conceptgraphs/conceptgraph"
"$RUNTIME/envs/conceptgraphs/bin/python" scripts/generate_gsa_results.py \
  --dataset_root "$RUNTIME/data/replica-full/Replica" \
  --dataset_config "$RUNTIME/upstream/conceptgraphs/conceptgraph/dataset/dataconfigs/replica/replica.yaml" \
  --scene_id room0 --class_set none --stride 5
```

完整对象融合、Detect 分支、语义 GT 评价和场景图的参数按 [固定版作者 README](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/README.md) 逐阶段执行，并用 `record_command.py` 保存证据。原版 LLaVA 与 HM3D 数据尚缺，见 [范围表](../reports/SCOPE.zh-CN.md)。

### 本机 12 GB GPU 的兼容运行

原始 SAM 批量 144 的共享显存占用与试验记录见 [状态文档](../reports/STATUS.zh-CN.md)。本机已完成 `conceptgraphs-replica-room0-none-batch16-04`，只把单批提示点改为 16。原始 checkout 保持干净，入口副本与单行 diff 保留在 `$RUNTIME/variants/`；不要把此结果称为原始默认批量结果。

```bash
cat "$RUNTIME/runs/conceptgraphs-replica-room0-none-batch16-04/record.json"
tail -c 1500 "$RUNTIME/runs/conceptgraphs-replica-room0-none-batch16-04/run.log"
cat "$RUNTIME/runs/conceptgraphs-room0-batch16-stages-04/outcomes.json"
cat "$RUNTIME/runs/conceptgraphs-room0-evaluation-cuda-05/outcomes.json"
```

自动队列结束或停止、GPU 空闲后，若 room1 仍无前端输出，可亲自执行：

```bash
python3 "$DOCS/src/scripts/run_cg_resource_frontend.py" --runtime "$RUNTIME" \
  --scene room1 --name cg-room1-manual-01 --sam-batch 16
python3 "$DOCS/src/scripts/run_cg_stages.py" --runtime "$RUNTIME" --scene room1 \
  --wait-record "$RUNTIME/runs/cg-room1-manual-01/record.json" --name cg-room1-stages-manual-01
```

脚本拒绝覆盖已有前端或三维结果。后续阶段先检查全部 400 个预期输出、1024 维特征及有限数值，再调用作者原始三维融合、RGB PointFusion 和评价。评价副本只显式选择当前场景，保留 diff，不能拿单场景结果当八场景均值。

首次映射的 14 GiB cgroup OOM 记录在 `conceptgraphs-room0-batch16-stages-02/diagnostics/`，294 个部分动画检查点保存在该运行的 `partial-outputs/`。第二次关闭动画后完成 400 帧，但仍在最终序列化触发 17G/10G 限制；截断文件已归档，不能评价。

当前重试保留作者默认 `save_objects_all_frames=False`，显式使用每任务 12G RAM / 48G swap。

本机已启用 48 GiB 的任务专用临时交换文件。重启 WSL 后需要重新启用；既有文件会核对清单，不重新格式化。在 Windows PowerShell 执行：

```powershell
wsl -d Ubuntu-22.04 -u root -- python3 /mnt/d/workspace/be2/SLAM_Author_Originals/src/scripts/prepare_swap.py --runtime /home/qzl/projects/SLAM_Author_Originals --gib 48
```

它不修改 fstab 或 WSL 配置。所有任务结束且内存允许后，在 Ubuntu 中清理本任务文件；不要在任务运行中关闭：

```bash
sudo swapoff /home/qzl/projects/SLAM_Author_Originals/resources/author-temporary.swap
sudo rm -- /home/qzl/projects/SLAM_Author_Originals/resources/author-temporary.swap
```

ConceptGraphs 语义 GT 的本机校验命令如下，公开文件 ID 来自固定作者 README：

```bash
"$RUNTIME/envs/downloads/bin/gdown" --continue --no-cookies \
  1NhQIM5PCH5L5vkZDSRq6YF1bRaSX2aem -O "$RUNTIME/downloads/conceptgraphs-Replica-semantic.zip.partial"
python3 "$DOCS/src/scripts/prepare_cg_semantic_gt.py" --runtime "$RUNTIME"
```

本机已完成时直接读取 `conceptgraphs-semantic-gt-manifest.json`，无需重下。HOV-SG 原始网格 GT 使用 `src/scripts/fetch_replica_gt.py --runtime "$RUNTIME"`，在完整解压 CRC 成功前不能用于报告评价完成。

本机两套 GT 均已准备好。原始网格的目录名带下划线，如 `room_0`；本地 `replica-original-manifest.json` 保存 RGB-D 名称到原始 GT 名称的对应，不重命名数据。

HOV-SG 串行任务进度：

```bash
cat "$RUNTIME/runs/hovsg-room0-batch16-stages-03/outcomes.json"
```

该默认采样任务使用 2000 帧输入中的 200 帧（skip_frames=10、SAM 批量 16），已在融合阶段超时，没有最终地图。原始评价的颜色表应选择作者提交的 `upstream/hovsg/hovsg/labels/class_id_colors.json`，包含 -1 与 0；不要选择运行时生成的 1..101 颜色表。评价工作目录独立，生成文件不写进源码。

03 特征任务融合期间将 RAM 限额从 12G 临时提高到 16G，原有 7200 秒超时不变。新版 `run_hovsg_stages.py` 提供 `--feature-timeout`（默认 21600 秒）和 `--evaluation-timeout`（默认 7200 秒）；它们只影响新启动任务，并记录到 outcomes。已有任务未结束时不要重复启动。

默认 06 已等待 CG 队列 09 结束，采用 16G/48G、特征 21600 秒和评价 7200 秒；可只读查看，不再重复启动：

```bash
cat "$RUNTIME/runs/hovsg-room0-batch16-stages-06/outcomes.json"
cat "$RUNTIME/runs/hovsg-replica-default-08/outcomes.json"
```

后者只在默认 room0 成功且通过原始产物哈希／日志检查后，才继续剩余七场景；每场景仍为 200 帧、SAM 批量 16，沿用 16G/48G 与 21600 秒特征时限。出现未解决失败即停止，不重复套用失败设置。源入口为 `src/scripts/run_hovsg_public_scenes.py`。全部通过后只汇总八个原单场景分数，不冒充另一个未经修改的八场景评价器。

当前 CG 串行队列为 `public-semantic-benchmark-09`：核验复用 SAM-only 的 room0/office0/office1 和 Detect 的 room0/office0；保留旧中断和主动取消记录，从头重跑 office1 Detect，再继续其余 5 场景。新 Detect 显式采用分阶段 GPU 驻留，16G/48G、前端时限 14400 秒；[三帧检查与完整 diff](CG_GPU_RECOVERY.zh-CN.md)。

只在对应方法的 8 场景全部成功后，调用未经修改的作者八场景评价入口，限额 12G/48G。旧队列与中断输出均保留，不能直接启动同名任务覆盖。

```bash
cat "$RUNTIME/runs/public-semantic-benchmark-09/outcomes.json"
tail -c 1500 "$RUNTIME/runs/public-semantic-benchmark-09/orchestration.log"
```

06 曾开启 `--hov-home-fallback`：默认采样失败后，另用 `pipeline.skip_frames=100` 均匀取 20/2000 帧，保留原分辨率和 SAM 批量 16。地图及修正颜色表路径后的原评价均已完成，mIoU 34.7500%、F-mIoU 62.8725%。

输出与首次失败分别保存在 `public-semantic-benchmark-06-room0-hov-home` 和 `hovsg-room0-home-evaluation-author-palette-01`，不计作默认采样或八场景 HOV benchmark。[结果与只读命令](../reports/HOVSG_HOME_RESULTS.zh-CN.md)。

队列正在运行时不要手动并发启动 GPU 任务。

Detect 的原始命令保留 `--class_set ram --box_threshold 0.2 --text_threshold 0.2 --stride 5 --add_bg_classes --accumu_classes --exp_suffix withbg_allclasses`。其映射使用 `mask_conf_threshold=0.25`、`skip_bg=False`，沿用作者命令生成的后缀 `ram_withbg_allclasses_overlap_maskconf0.25_simsum1.2_dbscan.1`。

README 的评价示例额外写了 `_masksub`，与映射命令不一致；这里显式传入实际文件名，不复制或伪造结果。Detect 复用同场景原始 RGB PointFusion 表面前，必须提供成功的记录并重新核对文件 SHA-256。

重启后先检查旧进程，避免把遗留的 running 当作当前仍在执行：

```bash
python3 "$DOCS/src/scripts/recover_after_restart.py" --runtime "$RUNTIME"
```

它只根据不同的 WSL boot_id 标记中断，保留所有文件，不推断运行成功。08 的恢复入口为 `src/scripts/resume_public_semantics.py`；此次对缺少退出码的前端保留全部旧输出后从头重跑，未把 400/400 日志当成功。完成结果按记录与全部输出 SHA-256 复用。[详细状态与中断证据](../reports/CONCEPTGRAPHS_SCENE_RESULTS.zh-CN.md)。

临时交换文件不会跨重启自动启用。恢复重任务前检查；如果缺少任务目录的交换文件，退出 qzl shell 后从 PowerShell 运行下面已有文件复用命令。它不修改 `fstab` 或 WSL 全局配置。

```powershell
wsl -d Ubuntu-22.04 -u root -- python3 /mnt/d/workspace/be2/SLAM_Author_Originals/src/scripts/prepare_swap.py --runtime /home/qzl/projects/SLAM_Author_Originals --gib 48
```

```bash
cat /proc/swaps
```

### 打开作者可视化窗口

已完成的前端可以先播放本机 Windows 文件：`D:\workspace\be2\SLAM_Recordings\author-originals\room0-rgb-and-sam-playback.mp4`。它是 400 帧 RGB／SAM 对照，40 秒、10 fps，仅展示已保存二维产物。视频、源图哈希与编码命令保存在 `runs/room0-frontend-playback-02/`；Git 仅提交轻量清单。

重做回放时输出目录必须新建：

```bash
python3 "$DOCS/src/scripts/render_frontend_video.py" \
  --scene-root "$RUNTIME/data/replica-full/Replica/room0" \
  --validation "$RUNTIME/runs/conceptgraphs-room0-batch16-stages-04/validation.json" \
  --output "$RUNTIME/runs/room0-frontend-playback-manual-01"
```

三维映射完成后，在 WSL 中执行：

本机已经验证的地图可通过带哈希检查和资源限额的入口打开，`--name` 必须新建：

```bash
python3 "$DOCS/src/scripts/open_cg_gui.py" --runtime "$RUNTIME" \
  --validation "$RUNTIME/runs/conceptgraphs-room0-batch16-stages-04/map-validation/validation.json" \
  --name cg-gui-manual-01 --software-rendering
```

已完成的原版窗口实录：[60 秒视频](../../results/videos/conceptgraphs-room0-original-window.mp4)。本机 Windows 文件在 `D:\workspace\be2\SLAM_Recordings\author-originals\conceptgraphs-room0-original-window.mp4`。

录制内容为 RGB → `i` 实例颜色 → 左键拖动旋转 → `r` RGB → 鼠标滚轮。查看器只对显示点云做作者原代码的 0.05 m 下采样；无文本查询或关系图。

`q` 关闭窗口，`v` 保存相机参数到本次工作目录。

直接调用作者查看器的等价命令：

```bash
cd "$RUNTIME/upstream/conceptgraphs/conceptgraph"
"$RUNTIME/envs/conceptgraphs/bin/python" scripts/visualize_cfslam_results.py \
  --result_path "$RUNTIME/data/replica-full/Replica/room0/pcd_saves/full_pcd_none_overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub_post.pkl.gz" --no_clip
```

窗口内按 `r` 看 RGB、`i` 看实例，鼠标旋转/缩放查看结构。要使用 `f` 输入文本查询，去掉 `--no_clip`，并先确认 GPU 空闲。none 分支不提供背景类别或关系图；`g` 只有真实关系文件存在时才有意义。

作者 `scripts/animate_mapping_save.py --input_folder <objects_all_frames 下本次运行文件夹>` 可以导出 RGB、二维分割、三维 RGB 和三维实例动画，但需要另一次成功启用 `save_objects_all_frames=True` 的运行。当前重试关闭了这个高内存可选项。

前次失败的部分检查点缺少完整元数据，不能用来伪装完整视频；原脚本还按列表顺序配 RGB，导出前需检查检查点索引与源帧对齐。最终地图成功后可先按上面的窗口命令手动录制 RGB／实例视图。

## 5. 证据和预算

新增 KITTI 原始帧段下载、作者预处理重做命令及 ScanNet 本人申请步骤见 [数据文档](DATA_ACCESS.zh-CN.md)。任务已在运行时，先检查 `runs/kitti-selected-inputs-01/outcomes.json` 与 `runs/kitti-author-selected-02/outcomes.json`，不要重复启动同一任务。

本机第三次建图、RGB 表面及修复 CUDA 依赖后的原始评价均已成功，`conceptgraphs-room0-evaluation-cuda-05` 保存 room0 原评分。[五项指标与独立 CPU 复查命令](../reports/CONCEPTGRAPHS_ROOM0_RESULTS.zh-CN.md)。

重试前用 `--reuse-chain` 核对地图／RGB 的 SHA-256，原失败记录保持原样。自动队列仍在运行时不要重复启动 GPU 评价。

直接执行作者入口时可加外层记录器；它不导入算法、不替换算法函数。输出目录必须新建，`--artifact` 可要求关键输出存在，`--timeout` 会记录超时。

```bash
python3 "$DOCS/src/scripts/collect_evidence.py" --runtime "$RUNTIME" --output "$RUNTIME/local/evidence-review-01"
```

先收集到 Git 之外的本机审阅目录。收集器可能包含运行中的状态，只把已结束、哈希已核对的轻量证据挑选进分支；不要直接向 Git 工作目录持续写入后台日志。大地图、权重和设备原片留在运行目录，完整提交一次已验证的阶段后检查 `git status --short`。

DeepSeek 设置文件为 `src/configs/deepseek-budget.json`，本轮总上限 1 美元。密钥仅从本地环境变量 `DEEPSEEK_API_KEY` 读取；所有调用必须共享同一 `DEEPSEEK_BUDGET_LEDGER` 账本。预算模块不会自动接管原版 GPT-4 调用，必须在单独的替代实验副本中显式接入，不能直接运行原版关系图入口而误调用其他服务。
