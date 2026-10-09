# 相机实物数据接主分支：先验输入，再验语义算法

[English](RGBD_MAIN_INPUT.md) | 中文

2026-10-09 本轮推进到 **ConceptGraphs / HOV-SG 原生 RGB-D 加载与几何接口检查通过**。尚未运行实物 SAM/CLIP、对象合并或文本查询；不能称已完成实物语义建图。本次显卡已有其他 HOV-SG 任务，检查仅使用 CPU，没有中断或改动其他任务。

主分支固定提交 `354b02d69ccc90304174f6d36010d25043d739ca`；从该提交读取配置，按其指定作者提交冻结 Python 源码副本。主分支及作者缓存保持原样。

## 1. 这次确实检查了什么

输入来自用户声明相机固定的原始会话 `data/live-camera-20261009-014327-492/raw.db3`，SHA-256 为 `35cfdca0dc208f65a004b00fc3f8d9e7d142042099753d8a0ec2a8c4c8c9047b`。该完整会话有动态背景，不能用作全场景完全静态验收。

导出其约 3–10 秒的 8 帧，间隔约 1 秒；逐帧联系表中可见饮料瓶、纸巾、盒子和透明容器，未见明显人员，但未人工标注物体或对所有原始帧做运动检测。

- SDK `rs.align(color)` 将真实深度对齐到 RGB；使用 RGB 内参，不套用 IR 内参。原始深度内参、深度到彩色外参另存。
- 深度保留 uint16 原单位，本机每单位约 `0.0010000000475 m`；作者加载器的 `scale` 是它的倒数，约 1000 单位/米。0 保持无效，不填洞。
- 保存无损 RGB PNG；ConceptGraphs 作者加载器固定找 `frame*.jpg`，另存质量 95 的 JPEG 兼容视图，检查时与此 JPEG 比较。原图不被覆盖。
- `replica-layout/` 只是作者要求的文件布局，数据仍是实测 D435，不冒称 Replica 数据集。
- 位姿为 `T_world_color=I`，依据是操作者声明相机固定。世界系取彩色光学系：x 向右、y 向下、z 向前，单位米；不是估计轨迹或独立真值。
- 逐帧记录两路时间、帧号、原始文件及导出文件哈希。RGB/深度时差约 **9.14–9.61 ms**，属于 SDK 配对，未证明硬件同步。

| 原生入口 | 实测结果 | 结果边界 |
| --- | --- | --- |
| ConceptGraphs `ReplicaDataset` | 8/8 帧读取；JPEG 像素一致；米制深度与导出文件差异最大约 `2.34e-7 m` | 只是浮点读入误差，不能当相机测距误差 |
| HOV-SG `ReplicaDataset` / `create__pcd` | 8/8 帧；每帧 180,643–183,392 个有效深度点；三维反投影差异最大约 `2.83e-7 m`，重投影约 `5e-14 px` | 坐标与尺度数值自洽，不能当独立标定精度或语义准确率 |
| 深度覆盖 | RGB 对齐后的全图有效比例约 **58.80–59.70%** | 近距离桌面、透明/反光物和遮挡仍有黑洞；不等于已通过哑光平面 ROI >90% 的目标 |

联系表：`data/rgbd-main-input-20261009-01/input-contact.png`；原生点云：`check-hovsg/native-first-frame.ply`；两份完整检查记录为对应 `check-*/record.json`。[可公开的数字证据](../evidence/rgbd-main-input-and-l2-independent-20261009.json)不包含室内图像或原始数据。

## 2. 在本机复现：先在 Windows 导出

按 Win+X → Windows PowerShell，确认提示符为 `PS ...>`。以下每块只有一条命令，整条粘贴回车。使用已有、确认固定的会话，不必重新打开相机，也不占用硬件。

```powershell
D:\workspace\be2\Personal-Learning-Physical\.venv\Scripts\python.exe D:\workspace\be2\Personal-Learning-Physical\scripts\export_rgbd.py D:\workspace\be2\Personal-Learning-Physical\data\live-camera-20261009-014327-492\raw.db3 --fixed-sensor-session --frames 8 --output D:\workspace\be2\Personal-Learning-Physical\data\manual-rgbd-input-01
```

预期 `status=exported`、`frames=8`，生成 `rgbd.json`、标定、图像和单位位姿文件。目录存在时换新的后缀；脚本拒绝覆盖。失败也保留 `rgbd.json`，不能只看文件夹存在就判通过。

换新录制时，必须确实固定相机，并在同目录 `session-note.json` 中如实记录 `camera_fixed_declared_by_operator: true`；不能给移动录制套单位位姿。此入口暂不支持移动位姿。

## 3. 打开 WSL，执行两套作者加载器

仍在 PowerShell 执行：

```powershell
wsl -d Ubuntu-22.04
```

看到 `qzl@...$` 后，在 Ubuntu 中执行：

```bash
cd /mnt/d/workspace/be2/Personal-Learning-Physical
```

先 ConceptGraphs：

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /home/qzl/projects/SLAM_Learning/.venv-semantic/bin/python scripts/check_main_rgbd.py data/manual-rgbd-input-01 --method conceptgraphs --main-repo /mnt/d/workspace/be2/SLAM_Learning --runtime /home/qzl/projects/SLAM_Learning --output data/manual-rgbd-input-01/check-conceptgraphs
```

再 HOV-SG：

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /home/qzl/projects/SLAM_Learning/.venv-hovsg/bin/python scripts/check_main_rgbd.py data/manual-rgbd-input-01 --method hovsg --main-repo /mnt/d/workspace/be2/SLAM_Learning --runtime /home/qzl/projects/SLAM_Learning --output data/manual-rgbd-input-01/check-hovsg
```

预期都为 `loader_check_passed`、`frames_checked=8`。这里不启动 RViz、不生成语义掩码，也不加载模型权重。实时 RGB/深度、点云、里程计及录像仍按[相机指南](CAMERA_GUIDE.zh-CN.md)启动。上面的 WSL 环境和模型缓存是本机已有依赖；新克隆机器须先按主分支环境文档配置。

## 4. 接下来怎样体现真正的语义算法

下一步是在独立运行副本中给主分支语义入口增加硬件 manifest 选项，替代固定 Replica 数据路径，并保留原入口回归。显卡有可用资源后依次运行两套核心，禁止并发挤占已有任务。

1. **SAM/CLIP 单帧**：保存原图、真实分割掩码及特征。画面预期是区域叠色；纸巾、盒子、瓶子可能被拆分或与背景连在一起。没有人工核对前，颜色块不等于正确识别。
2. **固定 8 帧建图**：保存逐帧掩码、对象/分段点云、对象编号和合并日志。预期同一物体多次观测在相同空间重叠；前后跳动、过多碎片、不同物体错误合并须保留并统计。
3. **文本查询**：使用预先写好的纸巾、盒子、饮料瓶查询，展示前三候选、相似度和三维表面位置；人工按真实可见物体核对 Top-1，不能用物品摆放说明直接写成模型输出。
4. **换摆放/移动物体**：固定相机，尺量位移并记录事件；观察身份碎片、错误合并和旧位置残留。完整移动相机实验须先有可验证的定位前端。

第一阶段目标是 8/8 帧完整执行、无非有限坐标、掩码与 RGB 尺寸一致、三维点使用同一标定和位姿来源。语义质量目标见[测试计划](TEST_PLAN.zh-CN.md)：至少标注目标实例、遮挡、事件和参考位置，再报告查询准确率、身份碎片/误合并、位置误差；现在这些指标留空。

## 5. 同轮 L2 独立检查

新会话 `data/l2-independent-20261009-015239-563` 绕开 ROS/RViz，只打开实体 CH343 的物理路径，采集约 **10.04 秒**，只发送一次读取版本请求。仍只有 **32 字节，0 有效包、0 点**；原始哈希与前次失败的 32 字节完全相同，离线协议审计也是 `incomplete`。

因此当前问题在 ROS 前的接收链路，尚不能定位到电源、TX/RX 接线、共地或设备状态中的某一个；也不能以 USB 适配器枚举成功证明雷达已正常输出。下一步需检查 L2 独立供电及转换器到雷达的实际接线，再录版本响应和点云。不要改波特率/模式来掩盖无包，也不要根据历史成功宣称当前收流正常。雷达可用数据录像仍待恢复后补录。

本轮不改主分支、不合并；脚本、指南及轻量证据推送到个人分支，原始录像、图像、点云和环境留本机。

## 6. 后续无人值守结果

另外使用同一原始录像的 500 帧执行 RTAB-Map RGB-D 的采样/送帧对照，修复 ROS 字节赋值开销，保留严格覆盖未通过记录，并录制了短时实机 RViz 视频。见[无人值守回放与性能](OFFLINE_REPLAY.zh-CN.md)。这是定位前端对照，不改变本页“语义核心尚未运行”的结论。
