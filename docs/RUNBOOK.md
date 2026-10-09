# Windows-to-author-workflow runbook

English | [中文](RUNBOOK.zh-CN.md)

Documentation: `D:\workspace\be2\SLAM_Author_Originals`. Native Linux runtime: `/home/qzl/projects/SLAM_Author_Originals`. Keep author sources, inputs and each run's outputs separate.

## 1. Before running

Start in Windows PowerShell, then enter Ubuntu-22.04 as qzl. Set `DOCS` and `RUNTIME` before Bash commands. Inspect existing outcomes and running tasks first; every new run needs a new name. Never start a second queue against the same outputs.

Original submodules are pinned. `prepare_runtime.py` refuses dirty or mismatched checkouts. g++-11 works on this host; the g++-10 failure remains recorded. [Environment](ENVIRONMENT.md).

## 2. LiDAR and semantic stages

Run original LiDAR entries, then original PCL export and scoring. The four releases and selected paper intervals have separate protocols. [Status](STATUS.md) · [Table IV](DUFOMAP_TABLE4.md) · [Historical Table III](KITTI_PAPER_PROTOCOL.md).

The semantic runtime uses complete 2,000-frame Replica sources, verified weights and method-specific GT. Original batch-144 commands and disclosed batch-16/sequential-residency variants must stay distinct. Follow [GPU recovery](CG_GPU_RECOVERY.md) for current queue names, not older completed/failed names below.

Each stage checks expected frame counts, finite features, exit codes and output hashes. A single-scene CSV is not the eight-scene mean. Saved-map viewing is a replay, not fresh inference. Missing LLaVA, original GPT-4 and HM3D stages stay incomplete.

## 3. Evidence and resources

Retain full commands, configuration diffs, logs, exit status and hashes. Do not overwrite partial outputs or retag failures as success. DeepSeek is a replacement-model variant with a USD 1 cap; keys stay outside Git.

Temporary swap is task-specific. Do not disable it while tasks run; existing swap files are verified, not reformatted. Cleanup commands below apply only after all related tasks finish and memory permits. No WSL/system configuration change is part of this documentation edit.

The command sequence below preserves the original runbook order. Original/default examples are recipes, not claims that every stage completed. [Full contextual runbook](RUNBOOK.zh-CN.md).

## 4. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```powershell
Set-Location D:\workspace\be2\SLAM_Author_Originals
git status --short
wsl -d Ubuntu-22.04 -u qzl
```

```bash
export DOCS=/mnt/d/workspace/be2/SLAM_Author_Originals
export RUNTIME=/home/qzl/projects/SLAM_Author_Originals
cd "$RUNTIME"
```

```bash
git clone --branch reproduce/author-originals --single-branch \
  https://github.com/p20030920p/SLAM_Learning.git SLAM_Author_Originals
cd SLAM_Author_Originals
git submodule update --init upstream/dufomap upstream/beautymap upstream/conceptgraphs upstream/hovsg upstream/dynamicmap
git -C upstream/dufomap submodule update --init --recursive
```

```bash
python3 "$DOCS/scripts/prepare_runtime.py" --runtime "$RUNTIME"
```

```bash
cat "$RUNTIME/runs/lidar-evaluation-01/scores/run.log"
cat "$RUNTIME/runs/released-lidar-01/scores/run.log"
cat "$RUNTIME/runs/dufomap-cpp-original-command-01/record.json"
cat "$RUNTIME/runs/beautymap-original-command-01/record.json"
```

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

```bash
mkdir -p "$RUNTIME/runs/manual-01/dufo" "$RUNTIME/runs/manual-01/beauty"
cp -a "$RUNTIME/data/00-pristine" "$RUNTIME/runs/manual-01/dufo/00"
cp -a "$RUNTIME/data/00-pristine" "$RUNTIME/runs/manual-01/beauty/00"
"$RUNTIME/build/dufomap-gcc11/dufomap_run" "$RUNTIME/runs/manual-01/dufo/00" "$RUNTIME/upstream/dufomap/assets/config.toml"
cd "$RUNTIME/upstream/beautymap"
"$RUNTIME/envs/lidar/bin/python" main.py --data_dir "$RUNTIME/runs/manual-01/beauty/00" --dis_range 40 --xy_resolution 1 --h_res 0.5
```

```bash
mkdir -p "$RUNTIME/runs/manual-python-01"
cd "$RUNTIME/runs/manual-python-01"
"$RUNTIME/envs/lidar/bin/python" "$RUNTIME/upstream/dufomap/main.py" --data_dir "$RUNTIME/data/00-pristine"
```

```bash
python3 "$DOCS/scripts/evaluate_lidar.py" --runtime "$RUNTIME" --name lidar-evaluation-manual-02
```

```bash
python3 "$DOCS/scripts/fetch_benchmark.py" --runtime "$RUNTIME"
python3 "$DOCS/scripts/run_released_lidar.py" --runtime "$RUNTIME" --name released-lidar-manual-02
```

```bash
python3 "$DOCS/scripts/fetch_benchmark.py" --runtime "$RUNTIME" --qualitative-only
"$RUNTIME/envs/lidar/bin/python" "$DOCS/scripts/run_dufo_qualitative.py" \
  --runtime "$RUNTIME" --name dufomap-qualitative-manual-01
```

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

```bash
cat "$RUNTIME/runs/conceptgraphs-replica-room0-none-batch16-04/record.json"
tail -c 1500 "$RUNTIME/runs/conceptgraphs-replica-room0-none-batch16-04/run.log"
cat "$RUNTIME/runs/conceptgraphs-room0-batch16-stages-04/outcomes.json"
cat "$RUNTIME/runs/conceptgraphs-room0-evaluation-cuda-05/outcomes.json"
```

```bash
python3 "$DOCS/scripts/run_cg_resource_frontend.py" --runtime "$RUNTIME" \
  --scene room1 --name cg-room1-manual-01 --sam-batch 16
python3 "$DOCS/scripts/run_cg_stages.py" --runtime "$RUNTIME" --scene room1 \
  --wait-record "$RUNTIME/runs/cg-room1-manual-01/record.json" --name cg-room1-stages-manual-01
```

```powershell
wsl -d Ubuntu-22.04 -u root -- python3 /mnt/d/workspace/be2/SLAM_Author_Originals/scripts/prepare_swap.py --runtime /home/qzl/projects/SLAM_Author_Originals --gib 48
```

```bash
sudo swapoff /home/qzl/projects/SLAM_Author_Originals/resources/author-temporary.swap
sudo rm -- /home/qzl/projects/SLAM_Author_Originals/resources/author-temporary.swap
```

```bash
"$RUNTIME/envs/downloads/bin/gdown" --continue --no-cookies \
  1NhQIM5PCH5L5vkZDSRq6YF1bRaSX2aem -O "$RUNTIME/downloads/conceptgraphs-Replica-semantic.zip.partial"
python3 "$DOCS/scripts/prepare_cg_semantic_gt.py" --runtime "$RUNTIME"
```

```bash
cat "$RUNTIME/runs/hovsg-room0-batch16-stages-03/outcomes.json"
```

```bash
cat "$RUNTIME/runs/hovsg-room0-batch16-stages-06/outcomes.json"
cat "$RUNTIME/runs/hovsg-replica-default-08/outcomes.json"
```

```bash
cat "$RUNTIME/runs/public-semantic-benchmark-09/outcomes.json"
tail -c 1500 "$RUNTIME/runs/public-semantic-benchmark-09/orchestration.log"
```

```bash
python3 "$DOCS/scripts/recover_after_restart.py" --runtime "$RUNTIME"
```

```powershell
wsl -d Ubuntu-22.04 -u root -- python3 /mnt/d/workspace/be2/SLAM_Author_Originals/scripts/prepare_swap.py --runtime /home/qzl/projects/SLAM_Author_Originals --gib 48
```

```bash
cat /proc/swaps
```

```bash
python3 "$DOCS/scripts/render_frontend_video.py" \
  --scene-root "$RUNTIME/data/replica-full/Replica/room0" \
  --validation "$RUNTIME/runs/conceptgraphs-room0-batch16-stages-04/validation.json" \
  --output "$RUNTIME/runs/room0-frontend-playback-manual-01"
```

```bash
python3 "$DOCS/scripts/open_cg_gui.py" --runtime "$RUNTIME" \
  --validation "$RUNTIME/runs/conceptgraphs-room0-batch16-stages-04/map-validation/validation.json" \
  --name cg-gui-manual-01 --software-rendering
```

```bash
cd "$RUNTIME/upstream/conceptgraphs/conceptgraph"
"$RUNTIME/envs/conceptgraphs/bin/python" scripts/visualize_cfslam_results.py \
  --result_path "$RUNTIME/data/replica-full/Replica/room0/pcd_saves/full_pcd_none_overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub_post.pkl.gz" --no_clip
```

```bash
python3 "$DOCS/scripts/collect_evidence.py" --runtime "$RUNTIME" --output "$RUNTIME/local/evidence-review-01"
```
