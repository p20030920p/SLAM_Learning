# Detect GPU recovery

English | [中文](CG_GPU_RECOVERY.zh-CN.md)

The five completed CG semantic runs retain their original scores. This page records resource diagnostics, not an accuracy improvement.

## 1. Observations

| Run | Outcome | Interpretation |
| --- | --- | --- |
| Queue 08, office1 Detect | Deliberately cancelled, exit -15, no frame | Stack samples stayed in SAM `get_rel_pos`; no confirmed CUDA OOM |
| CUDA/KNN probe 02 | Exit 0 | Small CUDA operations work; full-model memory remains unresolved |
| Allocator threshold 0.7 | 300-second timeout, no output | Did not resolve this stall; timeout exit code remains null |
| Sequential GPU residency, three frames | Exit 0, 91.35 s including loading | Valid masks/images and finite 1024-D features; not a full scene |

## 2. Compatibility change

`run_cg_offloaded_frontend.py` moves RAM, GroundingDINO and CLIP to CUDA for their forward passes, then back to CPU. SAM remains on CUDA. Weights, precision, prompts, thresholds, accumulated classes and frame selection stay fixed in a separate source copy.

Frames 0/5/10 produced 12/12/14 detections. Counts are not instance accuracy. Default numerical equivalence, the sole stall cause, full-scene resource bounds and paper runtime are unproven.

[Diff](../../results/configuration-diffs/variants/conceptgraphs-detect-offload-smoke-01/model-residency-compatibility.diff) · [Smoke record](../../results/runs/conceptgraphs-detect-offload-smoke-01/record.json) · [Validation](../../results/runs/conceptgraphs-detect-offload-smoke-01/validation.json).

## 3. Pending queue

Queue 09 verifies and reuses the five completed chains, then restarts office1 Detect and remaining scenes. Detect uses 16G RAM / 48G swap and a 14,400-second frontend limit; SAM-only retains batch 16. Only complete scene sets qualify for original eight-scene evaluation.

HOV default 06 waits for CG 09, with 200-frame sampling, SAM batch 16 and a 21,600-second feature limit. Follower 08 advances only after room0 validates. Cancelled waiting schedulers never started author stages.

Do not start duplicate task names. After reboot, inspect boot/process/record state and preserve partial outputs before a new run. [Runbook](RUNBOOK.md) · [Chronological diagnostics](CG_GPU_RECOVERY.zh-CN.md).

## 4. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

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
