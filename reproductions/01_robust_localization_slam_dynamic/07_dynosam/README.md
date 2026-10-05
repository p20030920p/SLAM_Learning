<div align="center">

# 01-07 · DynoSAM

**在因子图里同时估计相机位姿与物体运动，并开源配套的评测协议 —— 本机卡在「上游在 configure 阶段就要 CUDA」，与数据无关。**

[![venue](https://img.shields.io/badge/venue-T--RO%202025-0b7285)](https://arxiv.org/abs/2501.11893)
![blocked](https://img.shields.io/badge/blocked-CUDA%20required%20at%20cmake%20configure-cf222e)
[![code](https://img.shields.io/badge/code-ACFR--RPG%2FDynoSAM-181717?logo=github&logoColor=white)](https://github.com/ACFR-RPG/DynoSAM)
![data](https://img.shields.io/badge/data-OMD%20%C2%B7%20open%20index%20%C2%B7%20no%20signup-1c7ed6)
![needs](https://img.shields.io/badge/needs-a%20CUDA%20GPU-6f42c1)

[结论](#一句话-verdict) &nbsp;•&nbsp; [怎么跑](#怎么跑-how-to-run) &nbsp;•&nbsp; [坑与注意](#坑与注意-pitfalls) &nbsp;•&nbsp; [记录](#记录-log)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py)*

</div>

---

## 一句话 Verdict

| | |
| :--- | :--- |
| **阻塞点** | 上游在 **configure 阶段**就要 CUDA：`dynosam_nn/CMakeLists.txt:3` 写 `LANGUAGES C CXX CUDA`，`:105` 编 `.cu`，`:128-129` 无条件链接 TensorRT 与 `cudart`；`FeatureTracker.hpp:33` 还无保护地 include `<opencv2/cudaoptflow.hpp>` |
| **实测证据** | 本机无 `nvcc`、无 `NvInfer.h`、系统 OpenCV `cvconfig.h` 写着 `/* #undef HAVE_CUDA */`。**运行时开关救不了** —— 不用 TensorRT 的路径本来就是默认（`FrontendParams.yaml:62 prefer_provided_object_detection: true`） |
| **要什么才能跑** | 一块 CUDA GPU。**不是数据问题**：`data.acfr.usyd.edu.au` 是开放索引，OMD S4U 共 552 帧约 8.3 GB，免注册 |
| **记录** | [`work/feasibility.md`](work/feasibility.md) —— 逐文件、逐行的证据 |

## 关键设定 Settings

| 项 | 内容 |
| :--- | :--- |
| 怎么才能跑 | 一块 CUDA GPU。**不是数据问题** —— OMD S4U 552 帧约 8.3 GB，`data.acfr.usyd.edu.au` 开放索引免注册 |
| 论文 | DynoSAM: Open-Source Smoothing and Mapping Framework for Dynamic SLAM |
| 论文链接 | [arXiv:2501.11893](https://arxiv.org/abs/2501.11893) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [ACFR-RPG/DynoSAM](https://github.com/ACFR-RPG/DynoSAM) ✅ 实测 200 |
| 数据 | KITTI tracking / OMD / TartanAir / VIODE |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | 方向 1 备选（联合相机-物体评测） |
| 复现顺序 | 20 |
| 能否复现 | 🟡 **原来的判读要改**：CUDA 不是死结 —— `nvcc` 可以**在没有 GPU 的机器上安装**（已实测：conda-forge `cuda-nvcc` 装上 CUDA 13.4 编译器），`-DDYNOSAM_NN_USE_TRT=OFF` 又能去掉 TensorRT，两者一起就把 configure 阶段的 CUDA 门去掉了。真正剩下的是**一整套 ROS 2 + GTSAM 工作区**（上游对着 ROS 2 Kilted 写，本机是 Jazzy）。 |
| 复现完成 | ⛔ 本机不可复现（无 GPU） |

---

## 它做了什么 What it does

在因子图里**同时估计相机位姿与物体运动**，并开源了配套的评测协议，专门回答「动态 SLAM 到底该怎么评测」。

## 为什么复现它 Why

备选，但当点级方法不够用时它提供另一种信号来源：如果物体运动被显式估计出来，「这个物体还在不在」就有了模型化的答案，而不只是一个掩膜。它是我们判断「物体级 vs 点级」哪条路更值得走的依据。

## 复现目标（可验收）Goals

- [ ] 跑通官方示例数据集（先用最小的那个）
- [ ] 读它的评测协议：它如何定义动态 SLAM 的成功？
- [ ] 与任务书 §2 难点 4 的四个清理方法对照，写一段「点级 vs 物体级」的取舍结论

## 怎么跑 How to run

```bash
git clone https://github.com/ACFR-RPG/DynoSAM code/
# 需要 GPU + GTSAM；按仓库 README 安装（推荐 docker）
```

## 坑与注意 Pitfalls

- 依赖重（GPU、GTSAM），装环境可能占掉大部分时间 —— **这是备选，不要在它上面卡住主线**。
- 数据集体积大，先只下最小的一组。

## 可行性评估（2026-10-05，只读，未尝试编译）

完整证据见 [`work/feasibility.md`](work/feasibility.md)。结论：**这台机器连 `cmake` configure 都过不去**，
而且挡住它的不是运行时选项，是构建期硬依赖：

| 证据 | 内容 |
| :--- | :--- |
| `dynosam_nn/CMakeLists.txt:3` | `project(dynosam_nn LANGUAGES C CXX CUDA)` |
| `dynosam_nn/CMakeLists.txt:105,128-129` | 编译 `.cu` 源文件，并无条件链接 TensorRT 与 `CUDA::cudart` |
| `FeatureTracker.hpp:33` + `FeatureTracker.cc:60` | 无条件 `#include <opencv2/cudaoptflow.hpp>` 并调用 `cv::cuda::SparsePyrLKOpticalFlow::create()`（**没有** `DYNO_CUDA_OPENCV_ENABLED` 保护，检测器那边才有） |
| `dynosam/CMakeLists.txt:32,143` | 核心库 `dynosam` 依赖 `dynosam_nn` |
| 本机实测 | `nvcc` 不存在、无 `/usr/local/cuda*`、无 `NvInfer.h`、系统 OpenCV `cvconfig.h` 写着 `/* #undef HAVE_CUDA */` |

**两个看着像出路、实际不是的**：

1. **运行时开关救不了**：不用 TensorRT 的路径**本来**就是默认
   （`config/FrontendParams.yaml:62 prefer_provided_object_detection: true`，
   用数据集自带的掩码；`feature_detector_type` 也能改成 `GFTT`）——
   但这些都在 configure/compile 之后才起作用。
2. **数据不是阻塞**：`data.acfr.usyd.edu.au` 是开放索引，免注册；
   OMD S4U 共 552 帧约 8.3 GB。下下来在这台机器上也是白下。

> 顺带记录一个上游文档 bug：`README.md:208-209` 与 `:304` 把
> `prefer_provided_object_detection` 的语义写反了（代码为准），
> `README.md:247`/`:309` 与 `dynosam_nn/README.md:10` 是对的。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| 2026-10-05 | 克隆官方仓库（commit 8c20caa），逐文件核对构建依赖 | 见 `work/feasibility.md` | **CUDA 是构建期硬依赖，本机不可跑** |
| 2026-10-05 | 检查数据集与测试是否有 CPU 出路 | OMD 免注册可下（8.3 GB）；gtest 全都要链接核心库 | 数据集不是阻塞，测试也不是出路 |