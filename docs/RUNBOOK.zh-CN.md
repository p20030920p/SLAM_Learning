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
cat "$RUNTIME/runs/dufomap-cpp-original-command-01/record.json"
cat "$RUNTIME/runs/beautymap-original-command-01/record.json"
```

大点云本地位置：

- DUFOMap C++：`runs/dufomap-cpp-original-01/input/00/dufomap_output.pcd`
- BeautyMap：`runs/beautymap-original-01/input/00/beautymap_output.pcd`
- DUFOMap Python：`runs/dufomap-python-original-01/dufomap_output_voxel.pcd`
- 统一作者评价：`runs/lidar-evaluation-01/dataset/00/eval/`

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

## 4. 语义方法的原始命令

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
cd "$RUNTIME/upstream/conceptgraphs/conceptgraph"
"$RUNTIME/envs/conceptgraphs/bin/python" scripts/generate_gsa_results.py \
  --dataset_root "$RUNTIME/data/replica-full/Replica" \
  --dataset_config "$RUNTIME/upstream/conceptgraphs/conceptgraph/dataset/dataconfigs/replica/replica.yaml" \
  --scene_id room0 --class_set none --stride 5
```

完整对象融合、Detect 分支、语义 GT 评价和场景图的参数按 [固定版作者 README](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/README.md) 逐阶段执行，并用 `record_command.py` 保存证据。原版 LLaVA 与 HM3D 数据尚缺，见 [范围表](SCOPE.zh-CN.md)。

## 5. 证据和预算

直接执行作者入口时可加外层记录器；它不导入算法、不替换算法函数。输出目录必须新建，`--artifact` 可要求关键输出存在，`--timeout` 会记录超时。

```bash
python3 "$DOCS/scripts/collect_evidence.py" --runtime "$RUNTIME" --output "$DOCS/evidence"
```

DeepSeek 设置文件为 `config/deepseek-budget.json`，本轮总上限 1 美元。密钥仅从本地环境变量 `DEEPSEEK_API_KEY` 读取；所有调用必须共享同一 `DEEPSEEK_BUDGET_LEDGER` 账本。预算模块不会自动接管原版 GPT-4 调用，必须在单独的替代实验副本中显式接入，不能直接运行原版关系图入口而误调用其他服务。
