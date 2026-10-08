# 从 Windows 到作者入口

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
git submodule update --init upstream/dufomap upstream/beautymap upstream/conceptgraphs upstream/hovsg upstream/dynamicmap
git -C upstream/dufomap submodule update --init --recursive
```

Linux 原生目录的另一套干净作者源码可以用以下脚本建立；已存在但提交不匹配或有修改时，脚本拒绝覆盖：

```bash
python3 "$DOCS/scripts/prepare_runtime.py" --runtime "$RUNTIME"
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
bash "$DOCS/scripts/setup_lidar.sh" "$RUNTIME"
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

`scripts/evaluate_lidar.py` 固定读取本轮三次真实运行的路径，用于重现已发布的评价。新建评价目录，不覆盖旧目录：

```bash
python3 "$DOCS/scripts/evaluate_lidar.py" --runtime "$RUNTIME" --name lidar-evaluation-manual-02
```

四份公开数据的完整运行记录在 `runs/released-lidar-01`。准备额外三份作者数据并重跑两种原始入口与作者评价：

```bash
python3 "$DOCS/scripts/fetch_benchmark.py" --runtime "$RUNTIME"
python3 "$DOCS/scripts/run_released_lidar.py" --runtime "$RUNTIME" --name released-lidar-manual-02
```

已有下载会校验后复用；运行目录名必须新建。四份公开数据全部完成不代表论文所有消融、完整 KITTI 序列或定位系统实验完成。

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

完整对象融合、Detect 分支、语义 GT 评价和场景图的参数按 [固定版作者 README](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/README.md) 逐阶段执行，并用 `record_command.py` 保存证据。原版 LLaVA 与 HM3D 数据尚缺，见 [范围表](SCOPE.zh-CN.md)。

### 本机 12 GB GPU 的兼容运行

原始 SAM 批量 144 的共享显存占用与试验记录见 [状态文档](STATUS.zh-CN.md)。本机已完成 `conceptgraphs-replica-room0-none-batch16-04`，只把单批提示点改为 16。原始 checkout 保持干净，入口副本与单行 diff 保留在 `$RUNTIME/variants/`；不要把此结果称为原始默认批量结果。

```bash
cat "$RUNTIME/runs/conceptgraphs-replica-room0-none-batch16-04/record.json"
tail -c 1500 "$RUNTIME/runs/conceptgraphs-replica-room0-none-batch16-04/run.log"
cat "$RUNTIME/runs/conceptgraphs-room0-batch16-stages-04/outcomes.json"
cat "$RUNTIME/runs/conceptgraphs-room0-evaluation-cuda-05/outcomes.json"
```

自动队列结束或停止、GPU 空闲后，若 room1 仍无前端输出，可亲自执行：

```bash
python3 "$DOCS/scripts/run_cg_resource_frontend.py" --runtime "$RUNTIME" \
  --scene room1 --name cg-room1-manual-01 --sam-batch 16
python3 "$DOCS/scripts/run_cg_stages.py" --runtime "$RUNTIME" --scene room1 \
  --wait-record "$RUNTIME/runs/cg-room1-manual-01/record.json" --name cg-room1-stages-manual-01
```

脚本拒绝覆盖已有前端或三维结果。后续阶段先检查全部 400 个预期输出、1024 维特征及有限数值，再调用作者原始三维融合、RGB PointFusion 和评价。评价副本只显式选择当前场景，保留 diff，不能拿单场景结果当八场景均值。

首次映射的 14 GiB cgroup OOM 记录在 `conceptgraphs-room0-batch16-stages-02/diagnostics/`，294 个部分动画检查点保存在该运行的 `partial-outputs/`。第二次关闭动画后完成 400 帧，但仍在最终序列化触发 17G/10G 限制；截断文件已归档，不能评价。当前重试保留作者默认 `save_objects_all_frames=False`，显式使用每任务 12G RAM / 48G swap。

本机已启用 48 GiB 的任务专用临时交换文件。重启 WSL 后需要重新启用；既有文件会核对清单，不重新格式化。在 Windows PowerShell 执行：

```powershell
wsl -d Ubuntu-22.04 -u root -- python3 /mnt/d/workspace/be2/SLAM_Author_Originals/scripts/prepare_swap.py --runtime /home/qzl/projects/SLAM_Author_Originals --gib 48
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
python3 "$DOCS/scripts/prepare_cg_semantic_gt.py" --runtime "$RUNTIME"
```

本机已完成时直接读取 `conceptgraphs-semantic-gt-manifest.json`，无需重下。HOV-SG 原始网格 GT 使用 `scripts/fetch_replica_gt.py --runtime "$RUNTIME"`，在完整解压 CRC 成功前不能用于报告评价完成。

本机两套 GT 均已准备好。原始网格的目录名带下划线，如 `room_0`；本地 `replica-original-manifest.json` 保存 RGB-D 名称到原始 GT 名称的对应，不重命名数据。

HOV-SG 串行任务进度：

```bash
cat "$RUNTIME/runs/hovsg-room0-batch16-stages-03/outcomes.json"
```

该任务先运行完整 2000 帧输入的原始特征图入口（skip_frames=10、SAM 批量 16），检查 PLY 与 1024 维特征对应关系，再运行作者语义评价。评价工作目录独立，作者生成的颜色 JSON 不写进源码。单场景结果、资源配置和未完成阶段都分别记录。

其余 7 个公开场景由 `public-semantic-benchmark-05` 串行排队：先等待 room0 重试验证，然后加入作者原版 ConceptGraphs-Detect。首个 HOV-SG 或 Detect 流程未通过时，不在另外 7 个场景重复同一失败；SAM-only ConceptGraphs 可以继续。只有对应方法的 8 个场景全部成功，才调用未经修改的作者八场景评价入口。旧队列的等待、替换或前序失败均保留记录。

```bash
cat "$RUNTIME/runs/public-semantic-benchmark-05/outcomes.json"
tail -n 20 "$RUNTIME/runs/public-semantic-benchmark-05/orchestration.log"
```

Detect 的原始命令保留 `--class_set ram --box_threshold 0.2 --text_threshold 0.2 --stride 5 --add_bg_classes --accumu_classes --exp_suffix withbg_allclasses`。其映射使用 `mask_conf_threshold=0.25`、`skip_bg=False`，沿用作者命令生成的后缀 `ram_withbg_allclasses_overlap_maskconf0.25_simsum1.2_dbscan.1`。README 的评价示例额外写了 `_masksub`，与映射命令不一致；这里显式传入实际文件名，不复制或伪造结果。Detect 复用同场景原始 RGB PointFusion 表面前，必须提供成功的记录并重新核对文件 SHA-256。

重启后先检查旧进程，避免把遗留的 running 当作当前仍在执行：

```bash
python3 "$DOCS/scripts/recover_after_restart.py" --runtime "$RUNTIME"
```

它只根据不同的 WSL boot_id 标记中断，保留所有文件，不推断运行成功，不覆盖已有结果。对未完成前端，需先检查最后完整帧和当前入口的 start 参数，再决定续跑；不要直接重复启动同名队列。

### 打开作者可视化窗口

已完成的前端可以先播放本机 Windows 文件：`D:\workspace\be2\SLAM_Recordings\author-originals\room0-rgb-and-sam-playback.mp4`。它是 400 帧 RGB／SAM 对照，40 秒、10 fps，仅展示已保存二维产物。视频、源图哈希与编码命令保存在 `runs/room0-frontend-playback-02/`；Git 仅提交轻量清单。

重做回放时输出目录必须新建：

```bash
python3 "$DOCS/scripts/render_frontend_video.py" \
  --scene-root "$RUNTIME/data/replica-full/Replica/room0" \
  --validation "$RUNTIME/runs/conceptgraphs-room0-batch16-stages-04/validation.json" \
  --output "$RUNTIME/runs/room0-frontend-playback-manual-01"
```

三维映射完成后，在 WSL 中执行：

本机已经验证的地图可通过带哈希检查和资源限额的入口打开，`--name` 必须新建：

```bash
python3 "$DOCS/scripts/open_cg_gui.py" --runtime "$RUNTIME" \
  --validation "$RUNTIME/runs/conceptgraphs-room0-batch16-stages-04/map-validation/validation.json" \
  --name cg-gui-manual-01 --software-rendering
```

已完成的原版窗口实录：[60 秒视频](../evidence/videos/conceptgraphs-room0-original-window.mp4)。本机 Windows 文件在 `D:\workspace\be2\SLAM_Recordings\author-originals\conceptgraphs-room0-original-window.mp4`。录制内容为 RGB → `i` 实例颜色 → 左键拖动旋转 → `r` RGB → 鼠标滚轮。查看器只对显示点云做作者原代码的 0.05 m 下采样；无文本查询或关系图。`q` 关闭窗口，`v` 保存相机参数到本次工作目录。

直接调用作者查看器的等价命令：

```bash
cd "$RUNTIME/upstream/conceptgraphs/conceptgraph"
"$RUNTIME/envs/conceptgraphs/bin/python" scripts/visualize_cfslam_results.py \
  --result_path "$RUNTIME/data/replica-full/Replica/room0/pcd_saves/full_pcd_none_overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub_post.pkl.gz" --no_clip
```

窗口内按 `r` 看 RGB、`i` 看实例，鼠标旋转/缩放查看结构。要使用 `f` 输入文本查询，去掉 `--no_clip`，并先确认 GPU 空闲。none 分支不提供背景类别或关系图；`g` 只有真实关系文件存在时才有意义。

作者 `scripts/animate_mapping_save.py --input_folder <objects_all_frames 下本次运行文件夹>` 可以导出 RGB、二维分割、三维 RGB 和三维实例动画，但需要另一次成功启用 `save_objects_all_frames=True` 的运行。当前重试关闭了这个高内存可选项。前次失败的部分检查点缺少完整元数据，不能用来伪装完整视频；原脚本还按列表顺序配 RGB，导出前需检查检查点索引与源帧对齐。最终地图成功后可先按上面的窗口命令手动录制 RGB／实例视图。

## 5. 证据和预算

本机第三次建图与 RGB 参考表面已成功，第一次原评价因 chamferdist 缺少 CUDA 支持退出。扩展已补编；`conceptgraphs-room0-evaluation-cuda-05` 等待 HOV-SG 后验证真实 GPU KNN，再重跑原评价。它用 `--reuse-chain` 对原地图／RGB 文件重新核对 SHA-256，原失败记录保持原样。自动队列仍在运行时不要重复启动评价。

直接执行作者入口时可加外层记录器；它不导入算法、不替换算法函数。输出目录必须新建，`--artifact` 可要求关键输出存在，`--timeout` 会记录超时。

```bash
python3 "$DOCS/scripts/collect_evidence.py" --runtime "$RUNTIME" --output "$DOCS/evidence"
```

DeepSeek 设置文件为 `config/deepseek-budget.json`，本轮总上限 1 美元。密钥仅从本地环境变量 `DEEPSEEK_API_KEY` 读取；所有调用必须共享同一 `DEEPSEEK_BUDGET_LEDGER` 账本。预算模块不会自动接管原版 GPT-4 调用，必须在单独的替代实验副本中显式接入，不能直接运行原版关系图入口而误调用其他服务。
