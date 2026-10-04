# 01-02 · KISS-ICP 代码思路（逐行读官方仓库）

> 代码来源：**https://github.com/PRBonn/kiss-icp**（论文 README 给出的官方地址），本地 commit `1ffa7d7`（2026-05-04）；
> 运行用的是 PyPI `kiss-icp==1.3.0`，两者同源。下面每条都标了**文件:行号**。
> 论文：*KISS-ICP: In Defense of Point-to-Point ICP — Simple, Accurate, and Robust Registration If Done the Right Way*，RA-L 2023。

---

## 0 · 一句话

**KISS-ICP 里没有任何特征、没有描述子、没有回环检测、没有位姿图。**
它就是一个**点到点 ICP**（`Registration.cpp:138`），配一张体素哈希图（`VoxelHashMap`）。
论文的贡献不是"加了什么模块"，而是**把 ICP 的三个老问题各自用一行机制解决掉**，
使得**整套系统只有 7 个参数、而且不需要按数据集调**。

它自己要反驳的成见写在标题里：point-to-point ICP 被认为"不如 point-to-plane 准"。

---

## 1 · 主循环只有 9 步 —— `cpp/kiss_icp/pipeline/KissICP.cpp:35-68`

```cpp
RegisterFrame(frame, timestamps):
  preprocessed = preprocessor_.Preprocess(frame, timestamps, last_delta_);   // ① 去运动畸变
  [source, frame_downsample] = Voxelize(preprocessed);                       // ② 两级下采样
  sigma = adaptive_threshold_.ComputeThreshold();                            // ③ 自适应阈值 σ
  initial_guess = last_pose_ * last_delta_;                                  // ④ 匀速模型预测
  new_pose = registration_.AlignPointsToMap(source, local_map_,
                                            initial_guess,
                                            3.0 * sigma,   // max_correspondence_dist
                                            sigma);        // kernel
  model_deviation = initial_guess.inverse() * new_pose;                      // ⑤ 预测偏差
  adaptive_threshold_.UpdateModelDeviation(model_deviation);                 // ⑥ 反馈给阈值
  local_map_.Update(frame_downsample, new_pose);                             // ⑦ 更新地图
  last_delta_ = last_pose_.inverse() * new_pose;                             // ⑧ 更新速度模型
  last_pose_  = new_pose;                                                    // ⑨
```

**这 9 行就是全文。** 下面拆开说。

---

## 2 · 机制一：自适应阈值 —— 它凭什么"免调参"

ICP 最要命的参数是"最近邻搜索半径"：太小 → 匹配不上；太大 → 匹配到错误点。
KISS-ICP 的做法是**不设这个参数，而是在线估出来**。

### 阈值怎么来 — `cpp/kiss_icp/core/Threshold.cpp` + `Threshold.hpp:38`

```cpp
// Threshold.hpp:38
inline double ComputeThreshold() const { return std::sqrt(model_sse_ / num_samples_); }

// Threshold.cpp — UpdateModelDeviation
model_error = delta_trans + 2.0 * max_range_ * std::sin(theta / 2.0);
             //  ↑ 平移量        ↑ 旋转在最大量程处对应的弦长
if (model_error > min_motion_threshold_) { model_sse_ += model_error²; num_samples_++; }
```

**σ = 运动模型残差的 RMS。**

它的物理含义很漂亮：σ 衡量的是"**上一帧的匀速预测有多准**"。
机器人走得稳 → σ 小 → 匹配窗口收紧 → 精度高；走得乱 → σ 大 → 窗口放宽 → 不容易跟丢。
**所以"搜索半径"这个参数被换成了一个观测量。**

那个 `if (model_error > min_motion_threshold_)`（默认 0.1 m）是关键的一行：
**机器人停着不动时不把样本计进去**，否则 σ 会被拖到 0，阈值塌缩。

### 阈值怎么用 — `KissICP.cpp:50-54`

同一个 σ 用在两个地方：
- `3.0 * sigma` → ICP 最近邻的最大距离
- `sigma` → 鲁棒核的宽度

**一个量同时定这两件事**，所以只有一处需要标定。

---

## 3 · 机制二：两级体素下采样 —— `KissICP.cpp:70-75`

```cpp
const auto frame_downsample = VoxelDownsample(frame, voxel_size * 0.5);  // 进地图
const auto source           = VoxelDownsample(frame_downsample, voxel_size * 1.5);  // 进 ICP
```

一帧点云被降采样**两次、两个尺度**：
- **0.5×** 的送给地图（地图要稠密一点，才有足够结构）
- **1.5×** 的送给 ICP（配准只要够用就行，点数越少越快）

地图本身是**体素哈希**，每个体素最多留 20 个点（`max_points_per_voxel: 20`）——
这就是它的"局部地图"，**没有关键帧的概念**，所以不存在"关键帧怎么选"这个问题。

---

## 4 · 机制三：匀速模型 + 去畸变 —— `KissICP.cpp:47`、`core/Preprocessing.cpp`

```cpp
initial_guess = last_pose_ * last_delta_;   // last_delta_ = 上一帧的位姿增量
```

初值直接拿"**上一帧怎么动，这一帧还怎么动**"。简单到不能再简单，但它同时干了两件事：
1. 给 ICP 一个好初值（省迭代次数）；
2. `Preprocess(frame, timestamps, last_delta_)` 用它做**逐点去运动畸变**——
   一帧激光是在 0.1 s 内扫出来的，车在这 0.1 s 里动了，用 `last_delta_` 把每个点按时间戳折算回同一时刻。

> 论文标题里的 "If Done the Right Way" 有一半指的就是这里：**同一个 ICP，初值和去畸变做对了，精度就上来了。**

---

## 5 · 机制四：Geman-McClure 鲁棒核 —— `core/Registration.cpp:96-98`

```cpp
auto GM_weight = [&](const double &residual2) {
    return square(kernel_scale) / square(kernel_scale + residual2);   // σ² / (σ² + r²)
};
```

**没有 RANSAC、没有外点剔除、没有语义掩码。** 动态物体、错误匹配、噪声，全部靠这一个权重函数压下去：
残差 r 远大于 σ 的点，权重按 1/r² 衰减——**它还在参与优化，只是说不上话**。

这正是论文"在动态场景里也能用"的原因：**它不识别动态物体，只是不信任残差大的点**。

### ICP 本体只有 4 个公式 —— `Registration.cpp:138-167`

```cpp
TransformPoints(initial_guess, source);                     // 论文式 (9)
for (j = 0; j < max_num_iterations_; ++j) {
    correspondences = DataAssociation(source, voxel_map, max_distance);   // 式 (10)
    [JTJ, JTr] = BuildLinearSystem(correspondences, kernel_scale);        // 式 (11)
    dx = JTJ.ldlt().solve(-JTr);
    TransformPoints(Sophus::SE3d::exp(dx), source);                       // 式 (12)
    if (dx.norm() < convergence_criterion_) break;
}
return T_icp * initial_guess;
```

**点到点，没有任何几何特征**（没有法向量、没有平面拟合）。论文的主张就是：
point-to-point 只要把上面几件事做对，**精度不输并且更鲁棒**。

---

## 6 · 论文里的 7 个参数（`config/basic.yaml` + `advanced.yaml`）

| 参数 | 默认 | 作用 |
| :--- | ---: | :--- |
| `voxel_size` | 1.0 m | 体素边长（地图与下采样都用它派生） |
| `max_range` | 100.0 m | 预处理裁剪，同时是旋转项的量程 |
| `min_range` | 0.0 m | 预处理裁剪 |
| `deskew` | True | 是否逐点去运动畸变 |
| `max_points_per_voxel` | 20 | 体素哈希里每个体素保留的点数 |
| `initial_threshold` | 2.0 m | 自适应阈值 σ 的初始值（**只有前几帧用**） |
| `min_motion_th` | 0.1 m | 低于这个运动量的帧不计入 σ 统计 |

**注意里面没有"最大匹配距离"，也没有"迭代次数"** —— 前者被自适应阈值取代，后者在 `advanced.yaml` 里。
这就是它敢说"同一个参数跑所有数据集"的底气。

---

## 7 · 效果（论文自报）

| 数据集 | 指标 | 值 |
| :--- | :--- | ---: |
| KITTI 00–10 | 平均相对平移误差 | **0.50 %** |
| KITTI 11–21 | 平均相对平移误差 | 0.61 %（无公开 GT，只能提交官方评测） |
| MulRan KAIST | 相对平移误差 / ATE | 2.28 % / 17.40 m |
| Newer College 01-short | 相对平移误差 | 0.51 % |
| KITTI-raw（CV 去畸变） | 相对平移误差 | 0.49 % @ 38 Hz |

---

## 8 · 复现时要注意的

1. **它的官方指标是 KITTI odometry 的那一套**（`cpp/kiss_icp/metrics/Metrics.cpp:35`）：
   段长 `{100, 200, …, 800} m`，起点每 10 帧取一个，逐段算相对位姿误差再除以段长。
   **段长最短 100 m** —— 这条直接决定了我们手上那段 108 m 的数据只能出 2 个样本（见 README）。
2. **`kiss-icp==1.3.0` 在 NumPy 2 下会在写 TUM 轨迹时崩**（`pipeline.py:130` 对 `(N,1)` 形状的时间戳调 `float()`）。
   崩点在**指标算完之后**，只需补一行（见 `work/local_patches.patch`）。
3. **KITTI 数据加载器会调 `correct_kitti_scan`**（`datasets/kitti.py`），对 HDL-64E 做固定的运动补偿旋转——
   喂进去的必须是**传感器系**的原始扫描，不是世界系累积地图。
