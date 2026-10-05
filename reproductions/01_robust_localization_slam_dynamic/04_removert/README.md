<div align="center">

# 01-04 · Removert

**先删可疑点，再用多分辨率距离图像把误删的静态点回滚 —— 官方实现的 DA 比基准重实现高 47.7 个百分点，「Removert 最保守」是重实现的产物。**

[![venue](https://img.shields.io/badge/venue-IROS%202020-22314E)](https://doi.org/10.1109/IROS45743.2020.9340856)
![result](https://img.shields.io/badge/result-DA%2089.25%20vs%2041.53%20port-2ea043)
[![code](https://img.shields.io/badge/code-irapkaist%2Fremovert-181717?logo=github&logoColor=white)](https://github.com/irapkaist/removert)
![data](https://img.shields.io/badge/data-KITTI%2000%20%C2%B7%20Zenodo-1c7ed6)
![compute](https://img.shields.io/badge/compute-ROS%201%20Noetic%20%C2%B7%20micromamba-6f42c1)

[结论](#一句话-verdict) &nbsp;•&nbsp; [复现结果](#复现结果-results) &nbsp;•&nbsp; [怎么跑](#怎么跑-how-to-run) &nbsp;•&nbsp; [坑与注意](#坑与注意-pitfalls) &nbsp;•&nbsp; [记录](#记录-log)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

---

## 一句话 Verdict

| 同一份 141 帧、同一个点级评测器 | SA | DA | AA |
| :--- | ---: | ---: | ---: |
| **官方仓库 irapkaist/removert** | **99.62** | **89.25** | **94.29** |
| 基准里的重实现 | 99.44 | 41.53 | 64.26 |

论文原文没有编号表格（作者仓库里的 PDF 全文 `TABLE` 命中 0 次），所以对标的是官方实现自己的输出。

## 关键设定 Settings

| 项 | 内容 |
| :--- | :--- |
| 本机怎么跑 | ROS 1 Noetic（micromamba）· 官方 `removert_removert`，141 帧 **76 s** |
| 论文 | Removert: Remove then Revert — Static Map Building in Challenging Environment |
| 论文链接 | [doi:10.1109/IROS45743.2020.9340856](https://doi.org/10.1109/IROS45743.2020.9340856) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文没有编号表格（原因见下） |
| 代码 | [irapkaist/removert](https://github.com/irapkaist/removert) ✅ **官方仓库已编译并跑通** |
| 数据 | KITTI 00（DynamicMap_Benchmark 的 Zenodo 免注册包，141 帧） |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §2 难点 4 高变动场景的地图维护；§6 并行实验 H1′（排名稳定性） |
| 复现顺序 | 5 |
| 能否复现 | ✅ 能，但要 ROS 1：官方仓库跑通；原论文没有数字表，对上的是官方仓库自己的输出。 |
| 复现完成 | ☑ 2026-10-05 · 官方实现 SA/DA/AA = 99.62 / 89.25 / 94.29 |

---

## 它做了什么 What it does

先从距离图像里删掉「可疑」的点，再用多分辨率距离图像把**被误删的静态点回滚回来**（remove then revert）。

## 为什么复现它 Why

**四个方法里唯一带显式回滚步骤的。** 回滚本质上就是在保护静态结构，所以如果 H1′ 成立（F1 高 ≠ 定位好），Removert 应该是表现最稳的对照组。
本轮结果让它的地位更重要了：**它并不"保守"——保守的是基准里那份重实现。**

## 复现目标（可验收）Goals

- [x] **用作者自己的仓库编译并跑通**，产出清理后的地图
- [x] 记录它一次运行到底产出哪几个地图、各自是什么含义（这一步推翻了"一个方法一个数字"的假设）
- [x] 与基准的无 ROS 重实现在**同一份数据、同一个评测器**下对比
- [ ] 交给 01-02，看回滚是否真的换来了更低的配准失败率（依赖 KITTI 完整序列）
- [ ] 记录 revert 步骤单独删掉/救回了多少点（需要改上游参数跑两次）

## 怎么跑 How to run

```bash
# 0. 一次性：ROS 1 Noetic 环境（本机是 ROS 2 Jazzy、无 sudo、无 Docker）
micromamba create -y -p reproductions/.venvs/ros1noetic \
  -c https://conda.anaconda.org/robostack-staging -c conda-forge \
  ros-noetic-ros-base ros-noetic-catkin ros-noetic-pcl-ros ros-noetic-cv-bridge \
  ros-noetic-tf ros-noetic-image-transport ros-noetic-jsk-recognition-msgs \
  pcl eigen boost-cpp "empy=3.3.4"        # empy>=4 breaks Noetic's message generation

# 1. 克隆官方仓库 + 编译（打的是 PCL/OpenCV API 漂移补丁，见 work/local_patches.patch）
git clone https://github.com/irapkaist/removert code/removert
micromamba run -p reproductions/.venvs/ros1noetic \
  bash reproductions/tools/build_ros1_catkin.sh \
       reproductions/.ws/removert_ws removert <本文件夹>/code/removert

# 2. 一条命令跑完（重建序列 → 生成参数 → 跑官方节点 → 评测 + 回测）
python3 reproductions/run_all.py --only 01-04
```

底层三步是：`02_kiss_icp/work/make_kitti_seq.py`（把基准的世界系点云反变换回扫描）→
`work/gen_params.py`（复制上游 `config/params_kitti.yaml`，只改路径与序列区间）→
`work/run_official.sh`（roscore + `rosparam load` + 官方 `removert_removert` 节点）。

## 坑与注意 Pitfalls

| 坑 | 症状 | 处理 |
| :--- | :--- | :--- |
| **ROS 2 环境污染 ROS 1** | 编译成功，运行时 `symbol lookup error: undefined symbol: image_transport::ImageTransport` | ROS 1/ROS 2 同名库（`libimage_transport.so`…）被 Jazzy 抢先加载。`reproductions/tools/ros1_env.sh` 会把 `/opt/ros/jazzy*` 从各搜索路径里剥掉 |
| **OpenCV 4 没有 `<opencv/cv.h>`** | 编译期 `fatal error: opencv/cv.h` | 补丁删掉这个 OpenCV 1.x umbrella header（`opencv2/opencv.hpp` 已在下一行） |
| **PCL ≥ 1.11 换了智能指针** | `setIndices(boost::shared_ptr<...>)` 无匹配重载 | 4 处改成 `pcl::IndicesPtr` / `pcl::make_shared` |
| **PCL 的 VTK 依赖没导出** | 链接期 `libvtksys-9.2.so.1: DSO missing from command line` | 构建脚本加 `-I$ENV/include/vtk-9.2` 与 `-Wl,--copy-dt-needed-entries` |
| **上游参数文件是给 KITTI 09 调的** | 直接跑会用 1300–1600 帧 | 我们只跑 0–140，其余参数一律保留上游默认值 |

> 所有补丁都在 [`work/local_patches.patch`](work/local_patches.patch)，只碰 API 兼容性，**不碰算法**。
> `code/` 目录里是被打过补丁的上游源码，`git -C code/removert diff` 可复核。

## 复现结果 Results

### 一、官方实现 vs 基准重实现：同一份数据、同一个评测器

跑法：官方 `removert_removert`（141 帧 KITTI 00，`keyframe_gap=1`）→
用 `01_dynamicmap_benchmark/work/evaluate.py` 打分（`min_dis=0.05`，两种实现交叉验证一致）。

| 输出 | SA [%] | DA [%] | AA [%] | HA [%] | 点数 |
| :--- | ---: | ---: | ---: | ---: | ---: |
| **官方 · `StaticMapScansideMapGlobal.pcd`**（run() 最后一步） | **99.6179** | **89.2523** | **94.2928** | **94.1506** | 4,628,181 |
| 官方 · map-side 最细分辨率（revert 之前） | 95.1474 | 98.9675 | 97.0387 | 97.0199 | 3,976,241 |
| 基准重实现（Kin-Zhang 无 ROS 版） | 99.4361 | 41.5313 | 64.2628 | 58.591 | 16,722,918 |
| 基准表 I, p.5 / DUFOMap 表 I, p.5 | 99.44 | 41.53 | 64.26 | — | — |

**三条结论：**

1. **静态保留率几乎一样（99.62 vs 99.44，差 0.2 pp），动态剔除率差 47.7 pp。**
   基准那份重实现漏掉了官方代码能删掉的一半以上动态点
   （`missed_dynamic` 56,120 → 官方口径下 GT 动态点总量 95,983）。
   → 任何基于基准重实现的**方法排名都低估了 Removert**：它从"最保守的一个"变成 AA 第二。
2. **"Removert 的分数"必须先说清是哪个输出。** 同一次运行的两个上游输出
   （scan-side 合并 vs map-side 最细分辨率）分处精度/召回两个对角：
   SA 99.62/DA 89.25 与 SA 95.15/DA 98.97。本文件引用的是 scan-side 合并图，
   因为它是 `Removerter::run()` 的最后一步、也是"清理后的静态地图"最直白的对应物。
3. **官方输出点数只有重实现的 1/3.6，却拿到更高的 DA。**
   评测器用 0.05 m 最近邻判定"这个 GT 点还在不在"，本该惩罚稀疏地图；
   官方地图仍然赢，说明重实现多出来的那些点**不在评测器看的位置上**。

### 二、原文拿到了，但它没有数字表

原文就在作者自己的仓库里（`gkim-2020-iros.pdf`，4.76 MB）：

| 尝试过的路径 | 结果 |
| :--- | :--- |
| 作者 README 里的 `irapkaist.ac.kr/...` 链接 | ❌ DNS 解析失败 |
| OpenAlex | ✅ `is_oa: false` / `oa_status: closed` / 无仓库全文 |
| 我据此下的结论 | ❌ **"取不到"——错** |
| **克隆作者仓库** | ✅ **PDF 就在里面** |

**教训**：OpenAlex 的 `is_oa` 说的是**出版商侧**的开放获取，它看不到"作者把 PDF 放进自己 GitHub 仓库"。
**先克隆仓库，再下结论。**

拿到之后的结果比"拿不到"更值得记：**这篇论文没有一张编号表格**（全文 `TABLE` 命中 0 次）。
它的 "quantitative analysis" 指的是**图 8 / 图 9**——KITTI 03 上 TP/FP/FN 随 revert 迭代变化的曲线。
论文自己的措辞也是定性的："qualitatively competes or outperforms"。

→ **所以 Removert 没有可对标的自报数字**：不是我们拿不到原文，是原文自己没报。

### 三、阻塞已解除：ROS 1 不再是理由

先前本文件夹把「ROS 1 + 无 Docker + 无 sudo」写成"原始代码不能跑、只能跑重实现"。
现在这条不成立了：

| | 之前 | 现在 |
| :--- | :--- | :--- |
| ROS 1 | ❌ 不能装（要 sudo / Docker） | ✅ micromamba + robostack，装进 `reproductions/.venvs/ros1noetic`，不需要 root |
| 官方仓库 | ❌ 只读参考 | ✅ 已编译（3 个 API 补丁，均有记录）并跑出结果 |
| 数据 | ❌ 以为要注册 KITTI | ✅ 上游自己的参数只要求 KITTI 格式的 `.bin` + `poses.txt`，基准的 Zenodo 包可以反变换出来 |

→ 于是 01-03 ERASOR 也走同一条路（同一个环境、同一套工具脚本），见
[`../03_erasor/README.md`](../03_erasor/README.md)。

### 四、它和 ERASOR 不再是一条轴的两个极端

用**官方实现**的数字重排（同一份 KITTI 00，同一个点级评测器）：

| 方法 | SA [%] | DA [%] | AA [%] |
| :--- | ---: | ---: | ---: |
| **Removert（官方，scan-side）** | 99.62 | 89.25 | 94.29 |
| Removert（基准重实现） | 99.44 | 41.53 | 64.26 |

原先"一个几乎不删、一个删得过多"的对照关系是**重实现的产物**，不是方法的性质。
这句话直接改写了任务书 §6 H1′ 的前提：**要比较排序稳定性，先要确认每个方法跑的是它自己的代码。**

## 记录 Log

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| 2026-10-05 | 跑基准重实现，命中基准表 I 行 | 99.4361 / 41.5313 / 64.2628 | ✅ 基准可复现 |
| 2026-10-05 | 在作者仓库里找到原文 PDF | 全文无编号表格 | 该方法没有可对标的论文数字 |
| 2026-10-05 | 用 micromamba/robostack 建 ROS 1 Noetic 环境 | `rosversion -d` → noetic | ROS 1 阻塞解除 |
| 2026-10-05 | 编译官方仓库 | 3 处 PCL/OpenCV API 补丁 | 算法源码未改 |
| 2026-10-05 | 官方节点跑 KITTI 00（141 帧） | 76 s，4,628,181 点静态图 | 官方实现可跑通 |
| 2026-10-05 | 同数据同评测器对比两种实现 | 官方 DA 89.25 vs 重实现 41.53（+47.7 pp） | **基准重实现低估了 Removert** |