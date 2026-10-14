# 自恢复场景梯度录制（S1–S4）

> **历史离屏流程**：这里的右侧是自建 `map_view.py`，不是 RViz；S3 未通过、S4 本流程未录制。当前已完成的真实 Gazebo＋RViz＋终端四类现场片段与独立评分见 [本机现场流程](../../../docs/testing/LIVE.zh-CN.md)。当时 llvmpipe 下的故障不代表本机永久硬件限制。

## 这是什么

把 `Sim2Real-AlgoBench` 的四级场景（静态 → 动态 → 大变动 → 退化）各录成一条
1920×1080 的同屏片段：

| 位置 | 内容 |
| --- | --- |
| **左 960×1080** | Gazebo 自己渲染的**第三人称俯瞰实时画面**（仿真输出，不是回放、不是后处理重绘） |
| **右 960×1080** | `slam_toolbox` **在线建图**结果：占用栅格 + 实时激光 + 机器人位姿/轨迹 |

两半来自**同一次** 1920×1080 屏幕抓取，所以是同一时刻。

一键复现：`src/scripts/media/record_live_split.sh <级别> [秒数]`

---

## 先说清楚右半边是什么（重要，别误读）

**右半边不是 RViz 窗口，是本次录制自己写的一个看图程序** `src/scripts/media/map_view.py`。

原因是这条历史流程当时选用 llvmpipe，RViz2 的占用栅格着色器链接失败。它自己的日志：

```
[ERROR] [rviz2]: rviz/glsl120/indexed_8bit_image.vert
               rviz/glsl120/indexed_8bit_image.frag
 GLSL link result :
active samplers with a different type refer to the same texture image unit
```

RViz 的 `Map` display 着色器在当时的 llvmpipe（Mesa 软件渲染）配置下链接失败，栅格不显示；
RViz 其余部分（网格、TF）正常，所以窗口看起来"活着"，但关键证据是空的。

`map_view.py` 订阅**与 RViz 完全相同的主题**：

| 项 | 值 |
| --- | --- |
| 占用栅格 | `/map`（latched，`TRANSIENT_LOCAL` + `RELIABLE`） |
| 激光 | `/scan`（`BEST_EFFORT`） |
| 机器人位姿 | `/omni_drive_controller/odom` + tf2 查 `map → base_footprint` |
| 固定帧 | `map` |

信息与 RViz 一致，只是用本机能工作的 X11 canvas 画出来。画面常驻标签写明它是自建看图程序
与当前栅格尺寸，避免被误当成 RViz 窗口。

切回 RViz：`RIGHT_VIEW=rviz ./record_live_split.sh S1_static`。
这条历史配置未修复着色器时，右半边会缺掉地图。后续本机流程已使用 NVIDIA 4070 SUPER 的 D3D12 加速与独立 RViz 资源覆盖修复，并录下真实 RViz 地图，详见上述现场流程。

---

## 每级的条件（一句话）与实际参数

| 级别 | 一句话条件 | 世界 | 机器人 | 位姿来源 |
| --- | --- | --- | --- | --- |
| **S1_static** | 名义竞技场、无运动障碍、原厂 720 束激光；机器人按 10 点航点巡检，地图从零建起 | `scenario_variants/worlds/S1_static.world` | 原厂 `omni_car_ros2_control.urdf` | 仿真轮式里程计 TF，**非独立真值** |
| **S2_dynamic** | 同竞技场，脚本驱动的运动障碍穿过巡检路线 | `S2_dynamic.world` | 同上 | 仿真轮式里程计 TF，**非独立真值** |
| **S3_large_change** | **先建好的地图 + 被结构性改造的世界**：机器人拿 S1 的地图定位，而通道已被封死，地图与现状矛盾 | `S3_large_change.world` | 同上 | 仿真轮式里程计 TF，**非独立真值** |
| **S4_degradation** | 长直无特征走廊 + 退化激光（72 束 / ±120° / 3.5 m / σ=0.03 m），几何与感知同时退化 | `S4_degradation.world` | `urdf/omni_car_lidar_sparse.urdf` | 仿真轮式里程计 TF，**非独立真值** |

**四级共同的一条**：本录制的位姿一律来自仿真轮式里程计 `/omni_drive_controller/odom`
及其发布的 `odom → base_footprint` TF，**四级都没有使用独立真值**。
`truth:=true` 只用于桥出仿真模型位姿，不参与本录制的画面生成。

四级统一由 `scenario_variants/launch/scenario.launch.py` 启动；
级别定义的唯一来源是 `Sim2Real-AlgoBench/scenario_variants/run_scenario.sh`。
本录制只负责"怎么拍"，不改场景语义。

- S3 与 S1L 基线**只差 `world:=`**，命令其余部分完全相同，这样两个残差数字才可直接对比。
- S4 走廊航点 `9.4,-3.1;5.0,-3.1`，spawn `7.15,-3.10,0.0`。

### 实拍参数

**S1_static**（`S1_static.mp4`，170.0 s，2550 帧，15 fps，1920×1080，1 361 637 B）

| 项 | 实测值 |
| --- | --- |
| 世界 | `scenario_variants/worlds/S1_static.world` |
| 机器人 | 原厂 `omni_car_ros2_control.urdf`（未改任何传感器） |
| 相机 | 烘焙进派生世界 `topcam`，位姿 `3.65 1.0 10.5 0 1.5708 0`，600×675，hfov 1.92，10 Hz |
| 航点 | `8.5,7.6;5.3,7.6;5.3,6.5;8.2,6.5;8.2,5.2;9.7,5.2;9.7,4.2;6.7,4.2;6.7,1.8;9.7,1.8` |
| spawn | `8.0727, 7.5312, -1.5708` |
| `/scan` | 5.26 Hz（配置 10 Hz） |
| `/omni_drive_controller/odom` | 49.2 Hz |
| `/top_view` | 5.42 Hz |
| `/map` | 0.999 Hz |
| 左半边 | mean 188.78 / std 32.74 / 非黑 1.0 |
| 右半边 | mean 57.22 / std 76.82 / 非黑 0.9999 / 14 502 种颜色 |
| 显示器 | Xvfb pid 484，录制前后同一 pid（`display_stable`） |
| 屏上计数器 | `map 204 scan 539`（首帧）→ `map 530 scan 1244`（末帧） |
| 栅格尺寸 | **216×143 → 293×143**（0.05 m/cell，即已分配地图从 4.65 m 宽长到 14.65 m 宽） |
| 已建图占比 | t=34 s **0.8968** → t=136 s **0.9002**（`mapped_growth` **+0.0034**） |
| 机器人轨迹像素 | 1360 → 1625（**+265**，`robot_moved`） |
| 判定 | `left_rendered` ✅ `right_drawn` ✅ `right_map_grew` ✅ `robot_moved` ✅ **`pass` ✅** |

**S2_dynamic**（`S2_dynamic.mp4`，80.0 s，1200 帧，15 fps，1920×1080，1 190 402 B）

| 项 | 实测值 |
| --- | --- |
| 世界 | `scenario_variants/worlds/S2_dynamic.world`（三个运动障碍） |
| 录制窗口 | 启动后约 t≈107–187 s（避开巡检结束后的静止段） |
| `/scan` / `/odom` / `/top_view` / `/map` | 3.97 / 38.1 / 3.24 / 1.000 Hz |
| 左半边 | mean 139.39 / std 44.75 / 非黑 1.0（17k 种颜色，运动障碍在画面内） |
| 右半边 | mean 58.71 / std 78.05 / 非黑 0.9999 |
| 已建图占比 | t=16 s **0.8702** → t=64 s **0.8978**（`mapped_growth` **+0.0277**） |
| 画面差异 | `changed_frac` **0.0648**（S1 为 0.0102，动态场景差异明显更大） |
| 机器人轨迹 | 1096 → 1590 px（**+494**） |
| 判定 | 五项全通过 |

**S3_large_change**（`S3_large_change.mp4`，70.0 s，1050 帧，15 fps，1 227 976 B）——**五项全通过**

| 项 | 实测值 |
| --- | --- |
| 世界 | `scenario_variants/worlds/S3_large_change.world`（通道已封死） |
| 模式 | **`localize:=true map:=race_map.yaml`——用旧地图定位，不是建图** |
| 航点 | 主路线**重复 4 遍（40 段）**，理由见下 |
| `/scan` / `/odom` / `/top_view` | 6.07 / 54.0 / 4.71 Hz |
| 左半边 | mean 188.57 / std 32.97 / 非黑 1.0 |
| 右半边 | mean 74.82 / std 88.66 / 非黑 0.9999 / 18 497 种颜色 |
| **定位证据** | `map → base_footprint` 采样两次：`[6.765, 6.510]` → `[9.557, 4.438]`，**位姿在地图系里确实在变** |
| `/map` 发布端 QoS | `Durability: TRANSIENT_LOCAL`（`map_server` 与 `amcl` 各一个发布者） |
| 机器人轨迹 | 1988 → 2566 px（**+578**） |
| 已建图占比 | 0.8713 → 0.8700（**旧地图本就不该增长**） |

**S3 的判据与 S1/S2 不同，这一点必须说清楚**：S3 是**定位**级，手里的地图是建好的成品，
**本就不应该增长**，所以对 S3 而言"地图在长"是**错误的判据**——它曾两次把本来正常的定位
录制判成失败。S3 正确的判据是：机器人真的在动（`robot_moved`），且它**在地图坐标系里的位姿
随时间变化**（上面那条采样，原文记进 `check.json` 的 `localization_evidence` 字段）。
`right_map_grew` 对 S3 只作信息记录（`growth_criterion = map_static_ok`）。

**为什么航点要重复 4 遍**：巡检只走一圈，走完就打 `ROUTE_COMPLETE` 并停死；一圈约 155 s，
而录制前的准备（等话题、渲染门禁、摆窗口、布局门禁、测频率，加上 S3 额外的定位采样）约 150 s。
两者几乎相等，于是无论用固定延时还是"等某个航点"，抓到的都是机器人已经停在最后一段的画面
——我在这上面耗了四次尝试。把航点列表重复，就永远还有路可走，录制在流水线就绪时直接开始即可。
这是整条管线里最贵的一个坑。

**S4_degradation**（`S4_degradation.mp4`，70.0 s，1050 帧，15 fps，582 297 B）

| 项 | 实测值 |
| --- | --- |
| 世界 | `scenario_variants/worlds/S4_degradation.world`（长直走廊） |
| 机器人 | `urdf/omni_car_lidar_sparse.urdf`（72 束 / ±120° / 3.5 m） |
| 模式 | `slam:=true` 建图；航点 `9.4,-3.1;5.0,-3.1` **重复 12 遍（24 段）** |
| 视野框 | `0,16,-8,6`（走廊在 y=−3.1，默认竞技场框看不到它） |
| `/scan` / `/odom` / `/top_view` | 5.79 / 58.0 / 4.14 Hz |
| 左半边 | mean 187.94 / std 33.92 / 非黑 1.0 |
| 右半边 | mean 27.85 / std 37.71 / 非黑 0.9999 / 13 636 种颜色 |
| 机器人轨迹 | 903 → 1132 px（**+229**，`robot_moved`） |
| 已建图占比 | 0.9781 → 0.9781（**未增长**），自由格 0.0277 → 0.0276 |

**关于 S4 的判定，必须说清一件事**：这一级 `pass=true`，但它是靠"画面随时间有变化"
（`changed_frac` **0.0017**）这一条通过的，而**地图本身没有增长**
（`free_growth` **−0.0001**、`mapped_growth` **0.0**）。也就是说：
**S4 的"建图在长"并没有被证明**。诚实的原因是——走廊无特征、机器人来回走同一段地面，
地图在上一次经过时就建完了，之后不再有新信息。这其实**正是"退化"这一级要展示的东西**，
但我不能把它说成"地图在长"。若要求 S4 也必须有可测的建图增长，需要换一条更长或有分岔的
走廊，或让机器人走一遍没走过的路线。

**第一版 S4 完全无效的原因**：我漏了 `slam`，既没建图也没定位，因此**根本没有 `map` 坐标系**，
右半边只有背景。日志里能看到控制器正常激活、机器人来回走了 8 段航点，但右半边什么都没画。
修正为 `slam:=true` 并在 `verify_split.py` 里把增长判据从"已建图占比"换成**自由空间占比**
（因为"已建图"会把看图程序的深色背景算成占据：背景 18,22,28 而"占据"阈值是 <45，
栅格小的时候整个右半边会读成 99% 已建图，数字几乎不动）。

> 实拍参数按每级 `logs/params.txt` 与 `*_check.json` 的实测值填写。

**引用他人测量时的说明**：S2/S3/S4 的"未解释观测占比""条件数""真值位移"等数字由
平台代理测得，本 README 一律标注为"引用"，与本录制的实测值分表列出，不混在一起。

---

## 数据来源

- **世界 / 机器人 / 控制器 / SLAM 参数**：`Sim2Real-AlgoBench`（commit 见仓库）。
- **左半边画面**：上游 `tools/topcam.sdf` 的运行时相机模型。本录制只把分辨率从 480×480
  改为 600×675、水平视场角从 80° 改为 110°，以便在覆盖整个 30×30 竞技场的同时填满 960×1080。
  相机位姿沿用上游原值 `3.65 1.0 10.5 0 1.5708 0`。
- **左半边旋转**：上游 `docs/RECORDING.md` 用标记物实测得出"世界 +X 对应图像向上、+Y 对应图像向左"，
  而地图/RViz 是 +X 向右、+Y 向上，所以左半边**顺时针转 90°** 才与右半边同向；旋转在显示时施加一次。
- **建图**：`slam_toolbox` 的 `sync_slam_toolbox_node`，由 `nav2_lifecycle_manager` 驱动。
  slam_toolbox 是**生命周期节点**，裸启动会停在 `unconfigured` 且**不创建任何订阅**，
  必须由 lifecycle manager 带起来。
- **真值**：本录制**不使用独立真值**。右半边用的是仿真里程计
  `/omni_drive_controller/odom` 及其发布的 `odom → base_footprint` TF，
  **它是仿真里程计，不是独立真值**。
  注意 `/odom` 在这个栈里**不存在**（`slam_launch.py` 的 remap 叫这个名字，但没有节点发布到那里）。

### S3 残差判据（引用平台侧工具，注明版本）

`map_residual.py` 的数值使用**修正后**的判据，两条修正都必须带上，否则数字无意义：

1. 三值 PGM 里的**灰色 205 表示"未建图"**，必须按 yaml 阈值转成 ROS 的 0/100/−1；
   否则每条射线都"撞到未知"，S1 世界会被误算成 100% 未解释。
2. 只有"**沿自由且已建图的空间射到量程上限、却仍有回波**"才算"地图上没有的障碍"；
   射进未建图区的回波不构成证据。

S1 世界基线（修正后）：未解释观测 **0.2%**、mean|Δ| **3.9 cm**、p90 **8.3 cm**，
720 束中 708 条可判定。S3 的对应数字见 `S3_large_change_check.json`。

---

## 已知限制

1. **右半边不是 RViz 窗口**，理由见上。这条历史软件渲染配置的故障后来已在原生现场流程中修复。
2. **左半边帧率偏低**：原厂 URDF 同时开着机器人自带相机与俯瞰相机时，`/top_view` 实测约
   **1.4–2.7 Hz**。早期版本为提帧率裁掉机器人相机，但那次"只能有一个 RGB 相机"的结论**是错的**
   （成因见第 3 条），现在按上游原样使用 URDF，代价就是这个帧率，如实记录不掩饰。
3. **`GZ_PARTITION` 不要设**：设了之后 Gazebo server 与 `ros_gz_bridge` 可能落在不同 transport，
   表现是话题在 ROS 图里存在、却**永远没有数据**。这个静默失败一度被误判成"渲染坏了"。
   准确表述是"两端分区不一致时会静默失败"，最省事的做法是别设。
4. **Gazebo 图像行有 4 字节填充**，`ros_gz_bridge` 原样转发：600×675 rgb8 每行 1800 B 补到
   1804 B，直接 `Image.frombytes` 会抛 `unknown raw mode for given image mode`，画面全黑。
   见 `image_utils.py`。
5. **`xdotool search --name RViz` 会匹配到 Qt 的 3×3 辅助窗口**（`Qt Selection Owner for rviz2`），
   不是真正的 RViz 窗口；必须同时要求尺寸 ≥200×200。
6. **录制需要独占机器**：两台 llvmpipe 仿真并存会拖慢实时因子，屏幕抓取会中途
   `No data available` 而失败（此时显示器本身还活着）。脚本开录前会等待负载下降，
   并用一次与正式录制同时长的试抓做门禁。`WAIT_FOR_QUIET` 只统计 **PGID 与本轮不同**的
   Gazebo server，否则会把自己刚起的那个也算成竞争进程而无谓等满超时。
7. **QoS durability 不匹配会静默收不到任何消息**。这一次真实踩到：`/map` 用
   `RELIABLE + TRANSIENT_LOCAL` 订阅，而发布端若不提供 `TRANSIENT_LOCAL`，该订阅
   **一条消息都收不到，且不报任何错**——表现是画面上 `map 0`、栅格空白、右半边全黑，
   而 `/scan` 同时正常收到上千条。`map_view.py` 因此对 `/map` **同时建两个订阅**
   （`TRANSIENT_LOCAL` 与 `VOLATILE`），哪个真的来数据就用哪个，并把生效的那个
   显示在画面上、写进日志。
   教训：**话题存在、频率正常、订阅却匹配不上**，是这个栈第四种"看起来活着但是空的"形态。
   （本机 rclcpp 其实会在 stdout 打印
   `New subscription discovered on topic '/map', requesting incompatible QoS. No messages
   will be sent to it. Last incompatible policy: DURABILITY`，所以它是可查的，
   前提是去看进程的 stdout 而不是画面。）
8. **右半边必须用"固定世界坐标框"画，不能把栅格缩放去填满面板**。
   `slam_toolbox` 一开始就分配好整个 `max_size` 栅格（本机是固定的 293×143），
   之后只是往里填格子；如果看图程序把这张栅格缩放到铺满面板，那么从第 3 秒到最后一秒
   画面都是同一个矩形，"地图在长"这件事**会被渲染方式本身抹掉**。
   实测：这种画法下 t=3/15/40/80/130/165 s 的已建图占比恒为 **0.901**，自由格恒为 0.1441。
   改成固定世界框（`--view-bounds`，单位是米）后，已建图区域才会随机器人探索真实扩张。

---

## 文件与判定口径

| 文件 | 说明 |
| --- | --- |
| `S1_static.mp4` / `.gif` | 该级成片（其余级别同规律命名） |
| `S*_frame-{first,mid,last}.png` | 首/中/末三帧（整幅） |
| `S*_frame-{first,mid,last}_{L,R}.png` | 同上三帧的左右半边，便于单独核对 |
| `S*_check.json` | 由 `verify_split.py` 生成的判据与统计 |

**判定口径**：`right_drawn`（右半边非黑）**且** `right_map_grew`（右半边两时刻差异 > 0）。
左半边 `left_rendered` 是必要条件，但它单独成立**不算通过**。

注意布局门禁与终审是两次不同的测量：门禁采样**实时屏幕**，终审采样**编码后的 mp4**，
所以"门禁通过、终审失败"是**真问题**而非记账错误。

录制管线源码在 `src/scripts/media/`：
`record_live_split.sh`（主脚本）、`map_view.py`（右侧看图）、`sdk_image_view.py`（左侧看图）、
`rec_tools.py`（生成相机模型）、`image_utils.py`（解码，处理行填充）、
`verify_split.py`（复验）、`grab_overview.py`（渲染探针）、`make_rviz_config.py`（备用 RViz 配置）。

> S1 之前的失败尝试保留在 `results/localization/self-recovery-diagnostics/`，仅作诊断，不作为素材。
