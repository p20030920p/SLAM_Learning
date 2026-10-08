# 分支整理记录（2026-10-09）

这次清理针对重复入口、过期状态与分散的操作说明。原始录制和失败证据仍有复现价值，未按“没用”删除。

| 处理 | 具体内容 |
| --- | --- |
| 压缩首页 | README 改为当前状态、两条实时启动命令和指南索引；去掉首页重复的长诊断过程 |
| 归档 7 份旧文档 | HARDWARE_STATUS、BASELINE_RESULTS、DIAGNOSTICS_ROUND2/3、旧 USAGE、旧 CAMERA_WALKTHROUGH、旧 TEST_PLAN 移入 docs/archive，补历史标识并修复相对链接 |
| 保留旧书签 | USAGE 和 CAMERA_WALKTHROUGH 原路径变成短入口，指向当前指南及归档 |
| 统一操作 | 新增 start_live.ps1，Windows 一行启动采集、WSL、算法、RViz；避免 Shell 混用和手填变量 |
| 明确配置 | configs/rviz 只放当前相机 raw/odom/map、雷达 raw/odom 五种配置 |
| 保留可复现工具 | 原始审核、原生 SDK 对照、离线基线和主分支适配脚本继续保留，见下表 |
| 保留本地实验资产 | data、.venv、.cache、作者缓存和主分支工作树未做批量删除；旧失败和原始数据哈希仍可查 |

## 脚本分工

| 任务 | 入口 |
| --- | --- |
| 平时实时测试 | start_live.ps1；live_windows.py（Windows 设备）、live_ros.py（WSL ROS/算法）、live_transport.py（传输）、live_kiss_worker.py（隔离 KISS） |
| 快速静态图片/固定离线视频 | preview_camera.ps1、test_camera_stationary.ps1 |
| 独立原始采集 | capture_camera.py、capture_l2.py、capture_pair.ps1 |
| 原始审核与导出 | verify_camera_recording.py、audit_l2.py、analyze_static.py、export_stereo.py、export_rgbd.py、export_l2_clouds.py |
| 离线定位与视频 | run_odometry_baseline.py、run_kiss_baseline.py、render_odometry_video.py |
| 主分支固定输入适配 | run_main_dufomap.py、run_main_beautymap.py、render_dufomap_smoke.py；check_main_rgbd.py 仅原生加载/几何检查，不运行语义模型 |
| SDK/几何/IMU/边界诊断 | probe_sdk_replay.py/.cpp、verify_sdk.cpp、decode_sdk_lines.cpp、crosscheck_l2_geometry.py、diagnose_l2_motor.py、audit_l2_registration.py、audit_imu_frequency.py、verify_beautymap_padding.py |

诊断脚本不是日常第一步，保留是为了能解释和复查失败。没有清掉未通过记录，没有把未安装算法写成可运行。分支继续独立推送，当前不合并 main。
