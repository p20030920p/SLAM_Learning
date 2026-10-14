# 本机实时演示

这些入口连接公开 [SLAM-Physical](https://github.com/p20030920p/SLAM-Physical) 仓库。实验代码位于本库同级的 `SLAM-Physical` 文件夹；首次缺失时自动克隆。当前本机算法环境已准备，先双击 `00_check.cmd`。

| 双击文件 | 功能 |
|---|---|
| 00_check.cmd | 检查本机环境 |
| 00_setup.cmd | 安装专用仿真环境和固定版本资产 |
| 01_reproduce.cmd | 菜单选择四个算法，重新计算并显示 RViz |
| 02_experiment.cmd | 静态 BeautyMap C1/C2/C4 实验 |
| 04_departure_experiment.cmd | 首个物体离场实验 |
| 03_stop.cmd | 停止本次运行 |
| 90_update.cmd | 更新 SLAM-Physical main，保留本地结果 |
| 10_amcl_keyboard.cmd | Windows 键盘驾驶、AMCL 实时偏移与自动录制 |
| 11_build_localization_maps.cmd | 用一次驾驶生成论文方法的定位地图 |
| 12_amcl_choose_map.cmd | 选算法地图后键盘驾驶与观看偏移 |
| 13_compare_localization.cmd | 用另一录制，在各地图上回放同一输入进行定位对照 |

窗口内显示实际命令及进度；完成后按 Enter 关闭。结果写入 `SLAM-Physical/runs/`。源代码、实验协议与已实跑结果见实验仓库 README。

入口面向当前 Windows / WSL2 / CUDA 机器，依赖已准备的 Ubuntu-22.04 作者环境；`00_setup.cmd` 只安装 Ubuntu-24.04 仿真侧，不能替代全部算法、数据与权重安装。现有私有库不需要公开或复制到这里。
