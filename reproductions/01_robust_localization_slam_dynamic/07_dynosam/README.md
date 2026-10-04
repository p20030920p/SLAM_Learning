# 01-07 · DynoSAM

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | DynoSAM: Open-Source Smoothing and Mapping Framework for Dynamic SLAM |
| Venue | **T-RO 2025** |
| 论文链接 | [arXiv:2501.11893](https://arxiv.org/abs/2501.11893) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [ACFR-RPG/DynoSAM](https://github.com/ACFR-RPG/DynoSAM) ✅ 实测 200 |
| 数据 | KITTI tracking / OMD / TartanAir / VIODE |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | 方向 1 备选（联合相机-物体评测） |
| 复现状态 | ⛔ **本机不可跑**：上游在 `cmake` configure 阶段就要求 CUDA 工具链（`nvcc`/TensorRT/`cudaoptflow.hpp`），与数据无关 —— 见 [`work/feasibility.md`](work/feasibility.md) |

| 复现顺序 | 16 |
| 能否复现 | ⛔ 本机不能：`cmake` configure 阶段就要 CUDA / TensorRT（dynosam_nn），与数据无关。 |
| 复现完成 | ⛔ 本机不可复现（无 GPU） |

## 它做了什么 What it does

在因子图里**同时估计相机位姿与物体运动**，并开源了配套的评测协议，专门回答「动态 SLAM 到底该怎么评测」。

## 为什么复现它 Why

备选，但当点级方法不够用时它提供另一种信号来源：如果物体运动被显式估计出来，「这个物体还在不在」就有了模型化的答案，而不只是一个掩膜。它是我们判断「物体级 vs 点级」哪条路更值得走的依据。

## 复现目标（可验收）Goals

- [ ] 跑通官方示例数据集（先用最小的那个）
- [ ] 读它的评测协议：它如何定义动态 SLAM 的成功？
- [ ] 与任务书 §2 难点 4 的四个清理方法对照，写一段「点级 vs 物体级」的取舍结论

## 步骤 Steps

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
