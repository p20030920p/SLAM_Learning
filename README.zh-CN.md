# Personal-Learning-Physical

从空白分支开始的本机实物传感器学习与验证。目录：`D:\workspace\be2\Personal-Learning-Physical`。

**自己操作从这里开始：[一步一步使用本机测试流程](docs/USAGE.zh-CN.md)。** 按“固定设备 → 同时录制 → 核验原始数据 → 导出 → 定位 → 主分支接口测试”执行，文中给出命令、输出文件和正常判据。

**只测试相机、准备手持移动：[从打开 WSL 开始的相机教程](docs/CAMERA_WALKTHROUGH.zh-CN.md)。** 新增 `--session-type motion`，正常走动按轨迹范围统计，不再作为静止漂移打分。

**最新算法实测：** 双目静止基线通过本段目标（0.286 mm／0.093°），尚未验移动。原生 L2 点云上的 RTAB-Map ICP、KISS-ICP 均静止失败；KISS 关闭速度外推的诊断对照降至 13.23 cm／8.23°，仍未通过。主分支 DUFOMap 原适配器已处理 40 次实测观测。BeautyMap 原入口遇到小地图边界错误，局部空白网格扩域对照可处理全部 40 次观测，但还不是主分支修复或质量验收。SA／DA 均无标注依据。[第三轮结果、实际效果与复现命令](docs/DIAGNOSTICS_ROUND3.zh-CN.md)；[第二轮](docs/DIAGNOSTICS_ROUND2.zh-CN.md)；[首轮完整基线](docs/BASELINE_RESULTS.zh-CN.md)。

本分支为独立工作树中的 **orphan 分支**，没有复制主分支内容。主仓库为 `../SLAM_Learning`，检查时主分支提交为 `354b02d69ccc90304174f6d36010d25043d739ca`。现按用户要求推送到同一仓库的独立分支 [`Personal-Learning-Physical`](https://github.com/p20030920p/SLAM_Learning/tree/Personal-Learning-Physical)，不合并、不改主分支。它与 `notes/personal-study-guide-20261008` 是不同分支。

## 已确认的设备

| 项目 | 2026-10-08 本机实测 | 当前结论 |
| --- | --- | --- |
| 相机 | SDK 名称 **RealSense D435**，USB 3.2，固件 5.17.0.10；RGB／深度／左右 IR | 四路成功收流，30 秒各约 29.98 fps，帧号缺失 0；SDK 未发现 IMU，不能当成 D435i 使用 |
| L2 | **YS-L2**，硬件 2.2.1.1，固件 2.8.8.1；CH343，4,000,000 baud、8N1、无流控 | 成功收到 CRC 合格的点云与 IMU，并读出设备版本 |
| 串口 | 实体 CH343 与 ELTIMA 虚拟串口都叫 COM3 | 本次通过 `\\?\GLOBALROOT\Device\Serial2` 打开实体设备；未删除虚拟串口 |
| L2 30 秒记录 | 6,464 点云线包、7,492 IMU 包、1,743,215 有效点；5 次 CRC 拒绝 | 主机接收约 215.66 线包/s、249.96 IMU 包/s；线包不是完整 360° 扫描 |
| L2 时间 | 主机约 30 秒，原始设备时间约 15 秒；拟合比例约 1.9985 | **尚未通过惯性定位的时间验收**；原始时间未被擅自乘 2 或覆盖 |
| 官方 SDK 对照 | 原生 SDK 能解析保存的 UART；Python 与官方 XYZ 转换最大分量差约 4.53 μm | 接收与几何解码链路成立；不等于定位精度或 IMU 标定通过 |

本轮扩展到 20 包时的 0.1274 mm 差异已通过 float 角度累加对照解释，相同门槛下最大差降至 0.000954 mm；整段官方原生转换的点数与 Python 一致。原失败保留，未把该实现差值当测距误差。L2 厘米级定位漂移仍存在。

**最新 60 秒静止并发复核：** 在用户确认固定后，增大串口接收缓冲并用独立线程收字节。L2 收到 12,932 线包、15,000 IMU 包和 3,525,525 有效点，CRC 错误、序号缺失、时间倒退均为 0；相机四路约 29.98 fps、帧号缺失 0。原先同步帧组回放计数与采集一致；本轮逐路回调进一步确认全部实时帧号都被保留，且覆盖 DB3 所有图像消息，包括额外启动帧。接收链路通过这次检查，时间与场景质量另外验收。

最新相机场景前景过近：中央有效深度约 15.4 cm、全画面有效比例约 20.0%；这段不适合用来验收测距和定位。应让普通有纹理的墙角／家具处于约 1–3 m，避开强反光与近距离遮挡。L2 时间比例仍约 1.99866；静止陀螺仪均值接近零，但逐样本波动较大，单位／电机振动与标定还需核查。[最新审核](evidence/static-audit.json)。

最初相机 30 秒 `.db3` 经 SDK 同步帧组回放：深度 885、左 IR 886、右 IR 886、RGB 887，与采集帧组计数一致；这不是逐条原始图像消息计数。该段画面朝向天花板与强灯，深度有效比例约 94.1%、中央约 2.083 m、中央 ROI 随时间标准差约 8.76 mm。没有卷尺参考，不能称为测距精度。

L2 的序号实测在 1023→0 回绕，不能按 32 位单调序号统计丢包。修正后的离线审核记录在 `evidence/l2-audit.json`；首次错误 CRC 假设、错误 `.bag` 扩展名及原采集记录保留在本地 `data/`，用于追溯。

## 操作入口

当前已创建独立 `.venv`，Python 3.12，依赖见 `requirements.txt`。以后重新配置：

```powershell
Set-Location -LiteralPath D:\workspace\be2\Personal-Learning-Physical
& C:\Users\qzl\AppData\Local\Programs\Python\Python312\python.exe -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
git -c http.proxy= -c https.proxy= clone https://github.com/unitreerobotics/unilidar_sdk2.git .cache/unilidar_sdk2
git -C .cache/unilidar_sdk2 checkout 0e3c51f512e6b8ff60b8c32f160b412cb48445c2
```

`git -c ...proxy=` 仅对该次下载绕开本机失效的 7890 代理，不修改全局 Git 配置。

固定设备朝向有纹理的墙角与家具，避开直射灯。一次同时采集：

```powershell
.\scripts\capture_pair.ps1 -Seconds 60 -Session static
```

脚本根据 CH343 硬件与注册表重新解析实体串口，避免 COM3 名称冲突。两路分别生成新的目录，不覆盖旧数据。该脚本只发 L2 版本查询，不改工作模式、固件或时钟。没有刚性安装和时间标定时，同时采集不代表传感器已经同步。

分别采集与离线检查：

```powershell
.venv\Scripts\python.exe scripts\capture_camera.py --seconds 30 --record-raw --output data\camera-new
.venv\Scripts\python.exe scripts\capture_l2.py --seconds 30 --query-version --output data\l2-new
.venv\Scripts\python.exe scripts\audit_l2.py data\l2-new
.venv\Scripts\python.exe scripts\verify_camera_recording.py data\camera-new\raw.db3
```

`capture_l2.py` 的默认设备路径仅适用于本次枚举。重新插拔后优先用 `capture_pair.ps1` 重新解析，或明确传入新的 `--port`。两次采集不要同时争抢同一设备。

30 秒四路相机原始录制约 0.87 GB，UART 约 7.4 MB。原始数据和包含室内人员的预览只保存在本机 `data/`，已被 Git 忽略；轻量数值证据进入 `evidence/`。

- [初步测试、正常画面与指标门槛](docs/TEST_PLAN.zh-CN.md)
- [接入主分支算法与以后合并的步骤](docs/MAIN_INTEGRATION.zh-CN.md)
- 原相机预览：`data/2026-10-08/camera-02/preview.mp4`
- 原 L2 预览：`data/2026-10-08/l2-02/preview.mp4`
- 最新静止相机预览：`data/static-20261008-221334/camera/preview.mp4`
- 最新静止 L2 预览：`data/static-20261008-221334/l2/preview.mp4`

以上 `camera/preview.mp4`、`l2/preview.mp4` 是原始采集预览。新增算法输出视频和统计另见 [实际基线报告](docs/BASELINE_RESULTS.zh-CN.md)。双设备并发测试另存于 `data/link-*`，结果见 `evidence/concurrent-link.json`。

推送内容包括测试源码、文档和 `evidence/` 中的轻量记录；原始录制、视频、PCD、环境及 SDK 缓存不上传。报告中的 `../data/...` 链接只在本机有对应数据时可用，GitHub 页面不会包含这些媒体。[当前完成与待解决项](docs/HARDWARE_STATUS.zh-CN.md)。
