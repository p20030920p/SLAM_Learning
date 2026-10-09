# Environments and disclosed compatibility

English | [中文](ENVIRONMENT.zh-CN.md)

Use independent runtime environments. Installed versions describe this run, not a fully reconstructed paper-era environment. Do not reinstall over active environments.

## 1. Runtime

| Environment | Configuration |
| --- | --- |
| ConceptGraphs | Python 3.10.12; Torch 2.0.1/CUDA 11.8; PyTorch3D 0.7.4; Faiss 1.7.4 |
| HOV-SG | Original YAML, Python 3.9; unpinned dependencies resolved to Torch 2.8/OpenCLIP 3.3 |
| CUDA development | Separate CUDA 11.8 prefix; RTX 4070 SUPER architecture 8.9 |

[Installed CG packages](../../results/conceptgraphs-environment.txt) · [HOV packages](../../results/hovsg-environment.txt) · [Pinned sources](../../src/configs/upstreams.json).

CG's GSA/RAM and LLaVA dependency requests conflict. Disclosed compatibility uses RAM's Python package, Transformers 4.31 and timm 0.6.13; dependency diffs are preserved and method checkouts stay clean. GroundingDINO and chamferdist require working CUDA operators; import alone does not validate them.

## 2. Data and resource scope

Weights are copied and fully rehashed, not inherited predictions. Replica calibration uses native 1200×680 and depth scale 6553.5. Original LLaVA base weights and HM3D generation remain missing; DeepSeek does not fill that gap.

The host has about 19 GiB WSL RAM and a 12 GB GPU. Temporary swap and per-task cgroup limits are disclosed in run records; recent overrides are in [GPU recovery](CG_GPU_RECOVERY.md). Confirmed OOM/timeout attempts remain separate from successful runs. These resources do not reproduce paper timing or peak-memory results.

Below are the existing install/check commands, retained in source order. They are setup instructions, not commands to run over the current busy environment. [Runbook](RUNBOOK.md) · [Detailed environment history](ENVIRONMENT.zh-CN.md).

## 3. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```bash
mkdir -p "$RUNTIME/downloads" "$RUNTIME/tooling"
curl -L --fail https://micro.mamba.pm/api/micromamba/linux-64/latest -o "$RUNTIME/downloads/micromamba.tar.bz2"
tar -xjf "$RUNTIME/downloads/micromamba.tar.bz2" -C "$RUNTIME/tooling" bin/micromamba
"$RUNTIME/tooling/bin/micromamba" create -y -p "$RUNTIME/envs/hovsg" -f "$RUNTIME/upstream/hovsg/environment.yaml"
"$RUNTIME/envs/hovsg/bin/python" -m pip install -e "$RUNTIME/upstream/hovsg"
```

```bash
uv venv --python /usr/bin/python3.10 "$RUNTIME/envs/conceptgraphs"
export CGPY="$RUNTIME/envs/conceptgraphs/bin/python"
uv pip install --python "$CGPY" --extra-index-url https://download.pytorch.org/whl/cu118 \
  torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 numpy==1.26.4 setuptools wheel ninja
uv pip install --python "$CGPY" -c "$DOCS/src/configs/conceptgraphs-compat.txt" \
  tyro open_clip_torch wandb h5py openai hydra-core distinctipy ultralytics faiss-cpu==1.7.4 \
  open3d==0.18.0 scipy matplotlib imageio natsort supervision==0.6.0 ftfy opencv-python==4.8.1.78
```

```bash
export MAX_JOBS=2
uv pip install --python "$CGPY" --no-build-isolation --no-deps "$RUNTIME/dependencies/chamferdist"
uv pip install --python "$CGPY" -c "$DOCS/src/configs/conceptgraphs-compat.txt" --no-build-isolation -e "$RUNTIME/dependencies/gradslam"
uv pip install --python "$CGPY" --no-build-isolation -e "$RUNTIME/dependencies/Grounded-Segment-Anything/segment_anything"
uv pip install --python "$CGPY" --no-deps --no-build-isolation -e "$RUNTIME/dependencies/recognize-anything"
uv pip install --python "$CGPY" --no-build-isolation -e "$RUNTIME/upstream/conceptgraphs"
```

```bash
"$RUNTIME/tooling/bin/micromamba" create -y -p "$RUNTIME/envs/cuda118" -c nvidia/label/cuda-11.8.0 \
  cuda-nvcc cuda-cudart-dev cuda-driver-dev libcusparse-dev libcublas-dev libcusolver-dev libcurand-dev
export CUDA_HOME="$RUNTIME/envs/cuda118"
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib:${LD_LIBRARY_PATH:-}"
export TORCH_CUDA_ARCH_LIST=8.9
export AM_I_DOCKER=False
export BUILD_WITH_CUDA=True
uv --no-cache pip install --python "$CGPY" --reinstall --no-deps --no-build-isolation \
  -e "$RUNTIME/dependencies/Grounded-Segment-Anything/GroundingDINO"
"$CGPY" -c 'import torch; from groundingdino import _C; print(_C.__file__)'
```

```bash
python3 "$DOCS/src/scripts/build_chamfer_cuda.py" --runtime "$RUNTIME" --name chamferdist-cuda-manual-01
# GPU 空闲后，测试原评价所需的真实 CUDA 最近邻操作：
"$CGPY" "$DOCS/src/scripts/check_chamfer_cuda.py"
```

```bash
cat "$RUNTIME/replica-full-manifest.json"
cat "$RUNTIME/weights/SHA256SUMS"
```

```bash
export GSA_PATH="$RUNTIME/dependencies/Grounded-Segment-Anything"
ln -s "$RUNTIME/weights/sam_vit_h_4b8939.pth" "$GSA_PATH/sam_vit_h_4b8939.pth"
ln -s "$RUNTIME/weights/groundingdino_swint_ogc.pth" "$GSA_PATH/groundingdino_swint_ogc.pth"
ln -s "$RUNTIME/weights/ram_swin_large_14m.pth" "$GSA_PATH/ram_swin_large_14m.pth"
```
