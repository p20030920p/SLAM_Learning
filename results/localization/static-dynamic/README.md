# Static/dynamic localization media · 静态／动态定位媒体

Recorded benchmark: `static-dynamic-20261014-033854-8e3b79`, 2026-10-14.

| Category / 类别 | GIF | Full MP4 / 完整 MP4 |
| --- | --- | --- |
| Pure static / 纯静态，六种地图 | [static.gif](static.gif) | [static.mp4](static.mp4) |
| Dynamic LiDAR / 动态 LiDAR，原始＋BeautyMap＋DUFOMap | [dynamic-lidar.gif](dynamic-lidar.gif) | [dynamic-lidar.mp4](dynamic-lidar.mp4) |
| Dynamic RGB-D geometry / 动态 RGB-D 几何，原始＋ConceptGraphs＋HOV-SG | [dynamic-rgbd.gif](dynamic-rgbd.gif) | [dynamic-rgbd.mp4](dynamic-rgbd.mp4) |
| Clean-map control / 干净地图＋相同动态测试，六种地图 | [clean-map-dynamic-test.gif](clean-map-dynamic-test.gif) | [clean-map-dynamic-test.mp4](clean-map-dynamic-test.mp4) |

These are recorded-data reconstructions: each MP4 renders the common recorded trace interval at 8 fps, using the latest recorded sample at each frame. Each GIF converts every MP4 frame without cuts or speed changes. GIF's 10 ms time units approximate 125 ms frames with alternating 120/130 ms delays. Frame counts, duration differences (at most 0.01 s), full decoding, source hashes and output hashes are checked in [timing.json](timing.json). GIFs loop; the tables score each recorded test once per repeat.

画面为录制数据重绘：每个 MP4 以 8 fps 展示各方法录制轨迹的共同时间区间，每帧使用当时最近的记录样本。GIF 转换全部 MP4 帧，无剪辑、无加速；受 GIF 的 10 ms 时间粒度限制，125 ms 帧间隔用 120/130 ms 交替近似。[timing.json](timing.json) 保存逐片段帧数、时长校验（差异不超过 0.01 秒）、完整解码检查、来源与输出哈希。GIF 循环播放，评分按每次测试录制统计。

Green: truth. Blue: AMCL + odometry estimate. Orange: measured moving boxes. Gray image cells: unobserved space. Curves show the live prediction error; the scored RMSE in panel titles and [summary.csv](summary.csv) uses AMCL pose updates after the initial 5 seconds. Frozen live traces are in `evidence/<condition>/<method>.csv`; the moving-box measurements are in [actor_observations.csv](evidence/actor_observations.csv).

绿色为真值，蓝色为 AMCL＋轮速里程计估计，橙色为实际记录的运动箱体，灰色地图格为未观测空间。曲线显示实时预测误差；图标题及 [summary.csv](summary.csv) 中的 RMSE 对 AMCL 位姿更新评分，并排除最初 5 秒。冻结轨迹位于 `evidence/<condition>/<method>.csv`，运动箱体位置见 [actor_observations.csv](evidence/actor_observations.csv)。

Mapping A and test B were independently acquired. Mapping A uses simulator-provided sensor poses; test B gives AMCL scans, wheel odometry and the map, with truth reserved for scoring/display. Static/dynamic main comparisons each have three fresh replays of the same input; identical position outputs check reproducibility. The clean-map control has one replay and uses exactly the same dynamic B. Clips show repeat 1. ConceptGraphs/HOV-SG contribute offline geometry projections; their semantic features and hierarchy are outside this localization test.

建图 A 与测试 B 分开采集。建图 A 使用仿真提供的传感器位姿；测试 B 的 AMCL 接收扫描、轮速与地图，真值用于评分／显示。静态、动态主对照各重新回放三次相同输入，位置输出相同，用于检查可复现性；干净地图控制组仅一次，使用完全相同的动态 B。片段展示第 1 次回放。ConceptGraphs/HOV-SG 提供离线几何投影，本次定位测试不使用语义特征或层级关系。

[Maps, full protocol and scored comparison evidence / 地图、完整协议与评分证据](https://github.com/p20030920p/SLAM-Physical/tree/main/docs/results/static-dynamic) · [Original six-method dynamic video / 原始六方法动态视频](https://github.com/p20030920p/SLAM-Physical/blob/main/docs/results/static-dynamic/dynamic-localization-replay.mp4).

To regenerate from the retained local benchmark, use the prepared LiDAR Python environment in WSL and [render_localization_gallery.py](https://github.com/p20030920p/SLAM-Physical/blob/main/scripts/render_localization_gallery.py):

```bash
cd /mnt/d/workspace/be2/SLAM-Physical
/home/qzl/projects/SLAM_Author_Originals/envs/lidar/bin/python \
  scripts/render_localization_gallery.py \
  --benchmark runs/static-dynamic-20261014-033854-8e3b79 \
  --output ../SLAM_Learning/results/localization/static-dynamic
```

Full raw bags and native algorithm artifacts remain in the local benchmark folder. This gallery retains lightweight traces, summaries, media and hashes.

完整原始 bag 与原生算法产物保留在本机 benchmark 文件夹；此栏目保存轻量轨迹、统计、媒体与哈希。
