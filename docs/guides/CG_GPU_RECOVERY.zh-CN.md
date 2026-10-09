# Detect 首帧停滞与显存兼容记录

[English](CG_GPU_RECOVERY.md) | 中文

更新：2026-10-09，莫斯科。已完成的五条 CG 语义链路及原始分数不变；本页新增的是资源诊断和三帧契约检查。

| 运行 | 真实终态 | 能说明什么 |
| --- | --- | --- |
| 队列 08，office1 Detect | 我们主动取消，原进程 exit -15，未产出帧 | 多次非阻塞栈采样停在 SAM `get_rel_pos`；没有确认 CUDA OOM 或算法错误 |
| 独立 CUDA/KNN 小算例 02 | exit 0 | 小型 CUDA 算子可执行，不保证完整模型显存足够 |
| 原入口单帧、缓存回收阈值 0.7 | 300 秒超时，无输出 | 该缓存设置没有解决这次首帧停滞 |
| 分阶段 GPU 驻留，独立三帧 | exit 0，91.35 秒含加载 | 三帧均保存掩码、图像及有限的 1024 维特征；尚非完整前端或语义评价 |

[取消诊断](../../results/runs/cg-office1-gpu-diagnosis-01/diagnosis.json)、[取消前的栈](../../results/runs/cg-office1-gpu-diagnosis-01/stack-before-cancellation.log)、[CUDA 小算例](../../results/runs/chamferdist-cuda-probe-02/record.json)、[缓存试验](../../results/runs/conceptgraphs-detect-allocator-smoke-01/record.json)、[三帧原记录](../../results/runs/conceptgraphs-detect-offload-smoke-01/record.json)、[产物检查](../../results/runs/conceptgraphs-detect-offload-smoke-01/validation.json)。缓存试验超时记录的 exit_code 仍为 null；它由超时状态解释，不能改填成功或 OOM。

## 1. 兼容方案改变什么

`run_cg_offloaded_frontend.py` 在独立副本中，将 RAM、GroundingDINO、CLIP 在各自推理前移到 CUDA，完成后移回 CPU 并释放未用缓存；SAM 保持 CUDA 驻留。所有模型前向仍在原 CUDA 设备执行，保留原权重、精度、提示点、阈值、累计类别和选帧方式。副本没有修改作者 checkout。

[完整 diff](../../results/configuration-diffs/variants/conceptgraphs-detect-offload-smoke-01/model-residency-compatibility.diff)与[实际执行副本](../../results/configuration-diffs/variants/conceptgraphs-detect-offload-smoke-01/generate_gsa_results.py)均由原记录绑定 SHA-256。三帧对应原 RGB-D 的 0、5、10 帧，检测数为 12、12、14；这个计数不是实例准确率。

结果支持“该驻留方案能通过本次首帧并连续保存三帧”。尚未证明停滞的唯一原因、与默认驻留方式数值等价、完整场景资源上界或论文运行性能。后续结果必须注明资源变体，不能拿它的耗时作原版速度比较。

## 2. 当前完整任务

`public-semantic-benchmark-09` 已核验复用 SAM-only 的 room0/office0/office1 及 Detect 的 room0/office0，从头重跑 office1 Detect，再继续其余五场景。新 Detect 前端显式启用上述驻留方案，RAM/swap 限额 16G/48G，每场前端时限 14400 秒；SAM-only 仍是此前披露的批量 16 方案。

只有全部场景成功，才执行各自的原八场景评价。

HOV 旧默认 05、后续 07 的等待调度器已为隔离诊断而取消，均未启动作者阶段。新默认 `hovsg-room0-batch16-stages-06` 等待 CG 09，再以默认 200 帧采样、SAM 批量 16、16G/48G、特征时限 21600 秒运行；后续 `hovsg-replica-default-08` 仅在默认 room0 通过后继续。运行中日志不作为完成证据上传。

从 Windows 查看当前状态：

```powershell
wsl -d Ubuntu-22.04 -u qzl
```

```bash
export RUNTIME=/home/qzl/projects/SLAM_Author_Originals
cat "$RUNTIME/runs/public-semantic-benchmark-09/outcomes.json"
cat "$RUNTIME/runs/public-semantic-benchmark-09-office1-detect-frontend/record.json"
tail -c 1500 "$RUNTIME/runs/public-semantic-benchmark-09-office1-detect-frontend/run.log"
cat "$RUNTIME/runs/hovsg-room0-batch16-stages-06/outcomes.json"
cat "$RUNTIME/runs/hovsg-replica-default-08/outcomes.json"
```

不要重复启动同名任务。再次重启后先核对 boot、进程和记录，再保留旧产物并使用新运行名恢复。[结果边界](../reports/STATUS.zh-CN.md)与[完整使用命令](RUNBOOK.zh-CN.md)。
