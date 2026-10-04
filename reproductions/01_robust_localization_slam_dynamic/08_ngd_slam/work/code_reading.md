# 01-08 · NGD-SLAM 代码思路（逐行读官方仓库）

> 读的是论文自己给的仓库：**https://github.com/yuhaozhang7/NGD-SLAM**（论文 p.1 给出）。
> 本地 commit：`a93a14c`。下面每一条都标了**文件名:行号**，可以逐条核对。
> 论文：*NGD-SLAM: Towards Real-Time Dynamic SLAM without GPU*，IROS 2025。

---

## 0 · 一句话

**NDG-SLAM = ORB-SLAM3 + 一个 YOLO 语义线程 + 被改写的 `Tracking.cc`。**

`src/` 里 27 个 `.cc` 中，只有 `YOLO.cc` 是新文件，其余全是 ORB-SLAM3 的。
所以它的贡献不在"多加了一个网络"，而在**怎么让追踪不再等网络**。

对照 `include/` 也能看出来：`YOLO.h` 是新增的，`Tracking.h` 是改得最狠的。

---

## 1 · 它要解决的具体痛点

论文 Introduction 把问题说得很直白：已有的动态 SLAM 用深度网络给每帧生成掩码，
**追踪必须等这个掩码**，于是要么掉帧、要么延迟累积；而且为了实时几乎都得上 GPU。

要拆掉这个依赖，只有两条路：**要么让网络跑得更快，要么让追踪不等它**。
它选了第二条。

---

## 2 · 机制一：掩码传播（Mask Propagation）

### 2.1 线程怎么解耦 — `src/System.cc:216-218`

```cpp
mpYOLO   = new YOLO(0.5, 0.4, 320, 320, "./Thirdparty/YOLO/coco.names",
                    "./Thirdparty/YOLO/yolo-fastest-xl.cfg",
                    "./Thirdparty/YOLO/yolo-fastest-xl.weights", "yolo-fastest");
mptYOLO  = new thread(&ORB_SLAM3::YOLO::Run, mpYOLO);
```

- 网络是 **YOLO-fastest-xl**，输入 **320×320**（不是常见的 416/640），置信度 0.5、NMS 0.4。
  小输入 + 小模型是"CPU 也能跑"的前提。
- 它跑在**自己的线程**里，和 Tracking 完全并行（`System.cc:218`）。

### 2.2 生产者/消费者，而且**不阻塞** — `src/YOLO.cc:215-246`

```cpp
void YOLO::Run() {
  while(1) {
    std::unique_lock<std::mutex> inputLock(mInputMutex);
    if(mInputPair.size() == 2) {              // 有新帧才干活
        ... mInputPair.clear(); inputLock.unlock();
        cv::Mat imMask = Detect(imRGB, imDepth, 0);   // YOLO 推理
        cv::cvtColor(imRGB, imGray, cv::COLOR_BGR2GRAY);
        std::unique_lock<std::mutex> outputLock(mOutputMutex);
        mOutputPair.clear();                          // 清空旧的
        mOutputPair.push_back(imGray);                // 输出=灰度图+掩码
        mOutputPair.push_back(imMask);
    } else { inputLock.unlock(); }            // 没新帧就空转，不 sleep
    if(CheckFinish()) break;
  }
}
```

注意 `mOutputPair.clear()`：**输出只有"最新一份"，没有队列**。
追踪侧因此永远拿不到过期结果——拿不到就是拿不到，然后用传播顶上。
这是个刻意的取舍：牺牲一点点语义新鲜度，换掉整条等待链。

`Detect()` 在 `YOLO.cc:167-176`：`blobFromImage` → `net.forward` → `postprocess(imRGB, imDepth, ...)`。
**深度图也进了后处理**（`YOLO.cc:160-161` 还有一道保护：掩码占比 > 80% 就整张清零，
防止网络把整帧判成动态）。

### 2.3 追踪侧：轮询 + 更新"关键掩码" — `src/Tracking.cc:1567-1596`

```cpp
mpYOLO->InsertInput(mImRGB, mImDepth2);        // 把帧丢给网络线程，不等
while(true) {
    std::vector<cv::Mat> outputYOLO = mpYOLO->GetOutput();
    if(outputYOLO.size() == 2 && mFrameNum == 1) { mImMask = outputYOLO[1]; break; }   // 第 1 帧：必须等
    else if(outputYOLO.size() == 2 && mFrameNum > 1) {                                 // 有新的就用新的
        ...
        mImGrayLastKey = outputYOLO[0];      // 记下这一帧的灰度图
        mImMaskLastKey = outputYOLO[1];      // 和它的掩码 —— 作为"关键掩码"
        break;
    }
    else if(mFrameNum > 1) break;            // 没有新的？直接走人
}
if(mFrameNum > 1) PredictCurrentMask();      // 用旧掩码推出当前帧的掩码
```

**`else if(mFrameNum > 1) break;` 这一行就是全文的题眼**：除了第一帧，追踪**从不等待**网络。

### 2.4 传播怎么做 — `src/Tracking.cc:4286-4325`

```cpp
void Tracking::PredictCurrentMask() {
    mImMask = cv::Mat::zeros(mImMaskLastKey.size(), CV_8UC1);   // 静态=0，每帧从零开始
    int erosionSize = 5;                                        // 11x11 矩形核
    cv::Mat erosionElement = cv::getStructuringElement(cv::MORPH_RECT,
                                    cv::Size(2*erosionSize+1, 2*erosionSize+1), ...);
    erode(mImMaskLastKey, mImMaskLastKey, erosionElement);      // ① 先腐蚀

    ExtractDynaPoints(lastDynaPoints, mImGrayLastKey, mImMaskLastKey, 15);  // ② 15 像素栅格采样

    if(!lastDynaPoints.empty()) {
        cv::calcOpticalFlowPyrLK(mImGrayLastKey, mImGray,
                                 lastDynaPoints, currDynaPoints, status, error);  // ③ LK 光流
        for(size_t j = 0; j < status.size(); ++j) {
            if(status[j]) {
                float depth = mImDepth2.at<float>(currDynaPoints[j].y, currDynaPoints[j].x);
                if (depth >= 0.05) trackedDynaPoints.push_back(
                        cv::Point3f(currDynaPoints[j].x, currDynaPoints[j].y, depth)); // ④ 带深度
            }
        }
        ClusterWithDBSCAN(clusters, trackedDynaPoints, 50.0f, 15);   // ⑤ 聚类
        CreateMaskFromClusters(clusters);                            // ⑥ 填回掩码
    }
}
```

六步：**腐蚀 → 栅格采样 → 光流跟踪 → 取深度 → DBSCAN 聚类 → 画回掩码**。

几个值得记的细节：

| 细节 | 为什么这么做 |
| :--- | :--- |
| **① 先 `erode`（`Tracking.cc:4300-4302`）** | 上一帧掩码的**边界**最不可靠（分割边缘常抖动）。腐蚀掉边界，只采样"确定是动态"的内部点，避免把静态点拖进光流。 |
| **② `ExtractDynaPoints(..., cellSize=15)`** | 只在掩码内**每 15×15 像素取一个点**。这是它快的原因——不是跟踪整块区域，而是几百个代表点。 |
| **④ 用 `mImDepth2` 取深度** | 像素坐标 + 深度 = 3D 点，才能做有意义的空间聚类。深度 < 0.05 m 直接丢。 |
| **⑤ `ClusterWithDBSCAN(..., eps=50.0, minPts=15)`**（`Tracking.cc:4413`） | 在 **(x, y, depth)** 三维上聚类。`eps=50`、`minPts=15` 之外，函数内部还写了 `range=0.5, minSize=20, step=0.1`（`Tracking.cc:4416`）。 |
| **⑥ `CreateMaskFromClusters`**（`Tracking.cc:4497`） | 按聚类画**填充矩形/凸包**回掩码，得到当前帧的动态区域。 |

> **一句话总结传播**：动态区域在相邻帧之间是**连续移动**的，
> 所以拿上一帧掩码里的代表点做 LK 光流，就能"免费"得到当前帧的掩码。
> 网络只需要偶尔给一次可靠的真值来重置这个传播。

---

## 3 · 机制二：混合追踪（光流为主、ORB 兜底）

### 3.1 非关键帧**根本不提 ORB** — `src/Tracking.cc:1599-1605`

```cpp
if(mbStartOpticalFlow) {
    mCurrentFrame = Frame(mbStartOpticalFlow);   // ← 空帧构造函数
    mCurrentFrame.mTimeStamp = timestamp;
    TrackWithOpticalFlow();
}
```

`Frame::Frame(bool idPlus)`（`src/Frame.cc:55`）**只建了一个带 id 的空帧**：
不提取 ORB、不算描述子、不建金字塔。这是速度的第二个来源。
`mbStartOpticalFlow` 在前 3 帧为 false（`Tracking.cc:1563-1565`），
因为 RGB-D 初始化那几帧必须走完整的 ORB 流程。

### 3.2 用光流代替特征匹配 — `src/ORBmatcher.cc:2012-2052`

```cpp
int ORBmatcher::SearchByOpticalFlow(Frame &CurrentFrame, const Frame &LastFrame,
                                    const cv::Mat CurrImg, const cv::Mat LastImg,
                                    const cv::Mat imMask) {
    // 只取上一帧里"观测数 >= 3"的地图点（已经比较可靠的点）
    for (int i=0; i < LastFrame.mvpMapPoints.size(); ++i)
        if (LastFrame.mvpMapPoints[i] && LastFrame.mvpMapPoints[i]->Observations()>=3) { ... }

    cv::calcOpticalFlowPyrLK(LastImg, CurrImg, lastKeyPoints, currKeyPoints, status, error);

    for (size_t i = 0; i < currKeyPoints.size(); i++)
        if (status[i] && imMask.at<uchar>(currKeyPoints[i].y, currKeyPoints[i].x) == 0) {
            //                                      ↑ 落进动态掩码的点，直接扔掉
            cv::KeyPoint kp(currKeyPoints[i], 1.0f);
            CurrentFrame.mvKeysUn.push_back(kp);
            CurrentFrame.mvpMapPoints.push_back(lastMapPoints[i]);
            nmatches++;
        }
}
```

两个关键点：

1. **动态点的剔除发生在这里**（`imMask.at<uchar>(...) == 0` 才收），
   不依赖描述子匹配，也就不需要给动态区域算特征。
2. **地图点的身份是继承的**（`lastMapPoints[i]` 直接搬过来），
   所以非关键帧不做数据关联——这正是省下来的那部分计算。

### 3.3 什么时候退回 ORB — `src/Tracking.cc:3381`

```cpp
bool c5 = mbStartOpticalFlow && (mnMatchesInliers<20
        || (mnMatchesInliers<75  && mCurrentFrame.mnId>mnLastKeyFrameId+5)
        || (mnMatchesInliers<300 && mCurrentFrame.mnId>mnLastKeyFrameId+30));
```

这是一条**分级兜底**规则，读法是：

| 内点数量 | 距离上个关键帧 | 处理 |
| :--- | :--- | :--- |
| < 20 | 任意 | 立刻建关键帧，走完整 ORB |
| < 75 | > 5 帧 | 建关键帧 |
| < 300 | > 30 帧 | 建关键帧 |

也就是"**光流够用就一直用，一旦不可靠就切回 ORB**"。
论文说的 *"selectively allocating computational resources to input frames"* 就是这一段。

---

## 4 · 这套设计的效果（论文自报）

| 序列 | ATE (m) | RPE 平移 (m/s) | RPE 旋转 (°/s) |
| :--- | ---: | ---: | ---: |
| **f3/w xyz** | **0.015** | 0.020 | 0.470 |
| f3/w rpy | 0.034 | 0.044 | 0.889 |
| f3/w half | 0.024 | 0.025 | 0.695 |
| f3/w static | 0.007 | 0.009 | 0.262 |

（表 I，p.5；`*` 表示实时或近实时方法。）

**速度**：平均 **16.72 ms/帧 ≈ 60 FPS**，纯 CPU（表 IV + 正文 p.6）。
硬件是 Ryzen 7 4800H + RTX 2060，但正文明确说 GPU 不参与。

---

## 5 · 复现时要注意的三件事

1. **必须跑完整序列，不能抽帧。** 论文写明 "results are obtained by processing all frames in
   the sequence"。而它的机制（掩码传播 + 光流）**依赖帧间连续性**，抽帧会同时破坏两者。
2. **它没有 Pangolin 就编译不过**。`CMakeLists.txt:42` 是 `find_package(Pangolin REQUIRED)`，
   而 Pangolin 只被 `Viewer.cc` / `MapDrawer.cc` / `System.cc` 用到 —— 也就是说**为了一个可视化窗口，
   整个系统被绑上了一个图形栈依赖**。本机无 sudo 且发行版不带 `libpangolin-dev`，
   处理办法见本文件夹 README 的「环境」一节。
3. **`build.sh` 会构建 Sophus 的库和测试，但这个项目只用它的头文件**
   （`CMakeLists.txt:49` 只把 `Thirdparty/Sophus` 加进 include 路径）。
   照抄 `build.sh` 会在这里平白撞上一次编译失败。

---

## 6 · 与任务书的关系

| 任务书 | 对应 |
| :--- | :--- |
| §2 难点 5「算力受限下的稀疏表示 + 语义」（NGD-SLAM 是其中一条） | **正是本文**：它的贡献就是"语义分割在最贵的地方被绕开了" |
| §1 H6「算力受限 + 稀疏表示 与 动态检测 + 语义分割 互相冲突」 | 它的答案是调度：**低频语义 + 高频传播**（H6 给的三条修正方案里的第 1 条） |
| car.md 难点 1「未知动态物体检测（语义先验的盲区）」 | ⚠️ **反面**：它比纯几何方法更依赖语义先验（YOLO 的 COCO 类），未知动态物体仍会漏 |
| 01-05 DUFOMap 对比 | 一个是**几何**路线（光线投射判动态），一个是**语义**路线（YOLO + 传播）；两者互补 |
