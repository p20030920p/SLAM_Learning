# 语义环境与兼容性

本机已经建立两个独立环境：`$RUNTIME/envs/conceptgraphs`（Python 3.10.12）和 `$RUNTIME/envs/hovsg`（Python 3.9）。打开作者入口的命令见 [运行手册](RUNBOOK.zh-CN.md)。精确已安装版本保存在 [ConceptGraphs 清单](../evidence/conceptgraphs-environment.txt) 与 [HOV-SG 清单](../evidence/hovsg-environment.txt)；环境安装日志保留在 evidence/setup-logs。

## HOV-SG

本轮首先直接使用固定版本作者 YAML。作者未固定的 pip 依赖解析到 Torch 2.8.0 / OpenCLIP 3.3.0 等版本；这只是本轮环境，不等于论文当年的完整锁定环境。原始语义入口已经通过导入，实际运行另见状态文档。

在新的独立目录安装，micromamba 等价于作者 conda 环境创建方式：

```bash
mkdir -p "$RUNTIME/downloads" "$RUNTIME/tooling"
curl -L --fail https://micro.mamba.pm/api/micromamba/linux-64/latest -o "$RUNTIME/downloads/micromamba.tar.bz2"
tar -xjf "$RUNTIME/downloads/micromamba.tar.bz2" -C "$RUNTIME/tooling" bin/micromamba
"$RUNTIME/tooling/bin/micromamba" create -y -p "$RUNTIME/envs/hovsg" -f "$RUNTIME/upstream/hovsg/environment.yaml"
"$RUNTIME/envs/hovsg/bin/python" -m pip install -e "$RUNTIME/upstream/hovsg"
```

HM3D 数据生成还需按原 README 安装 habitat-sim；它不属于本轮已完成部分。不要覆盖已有环境来重做安装。

## ConceptGraphs

作者规定的关键组合是 Torch 2.0.1 + CUDA 11.8、PyTorch3D 0.7.4、Faiss 1.7.4。新环境先装这些，再安装固定依赖源码。以下摘出关键命令；完整原始安装顺序见 [固定版 README](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/README.md)。

```bash
uv venv --python /usr/bin/python3.10 "$RUNTIME/envs/conceptgraphs"
export CGPY="$RUNTIME/envs/conceptgraphs/bin/python"
uv pip install --python "$CGPY" --extra-index-url https://download.pytorch.org/whl/cu118 \
  torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 numpy==1.26.4 setuptools wheel ninja
uv pip install --python "$CGPY" -c "$DOCS/config/conceptgraphs-compat.txt" \
  tyro open_clip_torch wandb h5py openai hydra-core distinctipy ultralytics faiss-cpu==1.7.4 \
  open3d==0.18.0 scipy matplotlib imageio natsort supervision==0.6.0 ftfy opencv-python==4.8.1.78
```

PyTorch3D 使用作者指定的 [原始 conda 包](https://anaconda.org/pytorch3d/pytorch3d/0.7.4/download/linux-64/pytorch3d-0.7.4-py310_cu118_pyt201.tar.bz2)。本机将该包的 `lib/python3.10/site-packages` 安装到新环境，另装 iopath/fvcore。没有从旧实验继承预测结果。

GSA 的固定提交为 `a4d76a2b`，LLaVA 为 `8fc54a09`，其他实际提交见 [来源配置](../config/upstreams.json)。安装依赖的关键调用：

```bash
export MAX_JOBS=2
uv pip install --python "$CGPY" --no-build-isolation --no-deps "$RUNTIME/dependencies/chamferdist"
uv pip install --python "$CGPY" -c "$DOCS/config/conceptgraphs-compat.txt" --no-build-isolation -e "$RUNTIME/dependencies/gradslam"
uv pip install --python "$CGPY" --no-build-isolation -e "$RUNTIME/dependencies/Grounded-Segment-Anything/segment_anything"
uv pip install --python "$CGPY" --no-deps --no-build-isolation -e "$RUNTIME/dependencies/recognize-anything"
uv pip install --python "$CGPY" --no-build-isolation -e "$RUNTIME/upstream/conceptgraphs"
```

当前固定 ConceptGraphs 的 `ram` 导入与推荐旧 GSA 的 Tag2Text 子模块布局不一致。本轮安装 [RAM 作者的 Python 包](https://github.com/xinyu1205/recognize-anything)，统一 Transformers 4.31 / timm 0.6.13 的依赖配置；兼容修改 diff 保留，四个方法源码不修改。不能把“源码未改”误写成“整个依赖环境与论文完全一致”。

GroundingDINO 要编译 CUDA 算子；仅安装可导入的 CPU 占位包不能完成 Detect 分支。独立 NVIDIA 开发环境的实际安装与构建：

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

RTX 4070 SUPER 使用 8.9 架构；其他 GPU 应按设备调整。扩展验证需要先导入 Torch，直接单独导入 `_C` 的 `libc10.so` 错误不代表编译未成功。首次缺失 CUDA 头文件的失败日志也已保留。

## 数据与权重

SAM 与 CLIP 沿用已下载的原始模型文件，复制到本任务后重新计算 SHA-256；不是复用旧输出。GroundingDINO / RAM 按作者链接下载，哈希见 [权重清单](../evidence/weights-SHA256SUMS.txt)。相机 JSON 按固定版 Replica YAML 转写字段，分辨率 1200×680、深度尺度 6553.5。

本机完整 Replica 的恢复和检查不需要再次下载：

```bash
cat "$RUNTIME/replica-full-manifest.json"
cat "$RUNTIME/weights/SHA256SUMS"
```

原版 LLaVA-7B-v0 还缺授权基础权重；当前未安装或执行它的完整推理链。DeepSeek 不会自动补上这个缺口。

GSA 入口期望权重直接位于 `$GSA_PATH` 根目录。RAM 的根目录路径尤其容易与旧 Tag2Text 布局混淆：

```bash
export GSA_PATH="$RUNTIME/dependencies/Grounded-Segment-Anything"
ln -s "$RUNTIME/weights/sam_vit_h_4b8939.pth" "$GSA_PATH/sam_vit_h_4b8939.pth"
ln -s "$RUNTIME/weights/groundingdino_swint_ogc.pth" "$GSA_PATH/groundingdino_swint_ogc.pth"
ln -s "$RUNTIME/weights/ram_swin_large_14m.pth" "$GSA_PATH/ram_swin_large_14m.pth"
```

本机已存在的链接不需重建，`ln -s` 不带覆盖选项。CUDA 扩展已通过 Torch 导入后的 `_C` 检查；Detect 完整执行仍需单独记录，不能用扩展能导入代替建图完成。
