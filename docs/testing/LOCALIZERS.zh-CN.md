# 定位算法与部署范围

AMCL 不是必须的。此前固定同一个定位器，是为了只检验 Raw / DUFOMap / BeautyMap 地图的影响。更换定位算法时，还要控制地图、传感器、初始偏移、路线和评分窗口。

- [slam_toolbox](https://docs.ros.org/en/jazzy/p/slam_toolbox/)：二维扫描匹配定位；需要序列化位姿图，现有 PGM 栅格地图不能直接替代它。
- [IR-MCL](https://github.com/PRBonn/ir-mcl)：神经场渲染预测扫描，更新粒子权重；Bonn 作者序列已复现，接入 Gazebo 需要为新地图训练神经场。
- [AdaM-MCL](https://github.com/Runjian-Chen/AdaM_MCL)：学习式位姿候选与粒子跟踪混合；已有受限原库执行，当前地图还需要训练与在线输入适配。
- [NDT / GICP](https://github.com/rsasaki0109/lidar_localization_ros2)：直接将实时三维扫描与固定三维点云地图配准，输出位姿；本次优先部署。
- [Beluga](https://github.com/Ekumen-OS/beluga)：可扩展 MCL 实现，已经安装；仍属于粒子滤波族。

NDT 将地图邻域表示成概率分布；GICP 用局部几何协方差做配准。二者都需要足够约束和可用初值，成功跟踪不等于成功全局重定位。KISS-ICP 等纯里程计估计相邻扫描间运动，不能直接当成固定地图定位的替代品。

## 本次三维接入

作者库固定提交 ba9f7f06dbe80aeabff602c37d712dfaa948241d，ndt_omp_ros2 与定位包在独立 Jazzy 工作区 /root/slam-alternative-ws/build_ws 编译。[接入脚本](../../src/scripts/presentation/registration.launch.py)不改作者估计器。

输入为实时 /points、真实传感器外参、冻结建图 A 的 Raw 三维地图与轮速里程计。输出为作者原生 /<method>/pcl_pose 与 map→odom TF。Gazebo 真值只交给评分器。当前机器人没有 IMU 和逐点时间字段，因此关闭 IMU 和连续时间去畸变；二维栅格只用于显示，估计器实际匹配三维地图。

初始偏移 X=0.25 m、Y=0.15 m、yaw=0.12 rad；NDT 分辨率 0.5 m，输入体素 0.15 m，距离 0.3–12 m，最大 35 次迭代、两个 NDT 线程。这里是小室内平台部署，不能当作者基准复现，也不能用不同的二维／三维输入直接给 AMCL 排名。

当前入口在 F:\be2演讲\实机脚本：31-NDT三维定位_静态.bat / 32-GICP三维定位_静态.bat。启动真实 Gazebo、RViz 和终端，保存原生定位输出与现场录像。

## 已执行的静态试验

- [NDT 最新原生记录](../../results/reference/robot-ndt-static/record.json)：402 条匹配更新，XY RMSE 0.93 cm，偏航 0.17°。
- [GICP 原生记录](../../results/reference/robot-gicp-static/record.json)：397 条匹配更新，XY RMSE 1.09 cm，偏航 0.16°。
- [NDT 首次预检](../../results/reference/robot-ndt-static-initial/record.json)：399 条更新，XY RMSE 34.43 cm。之后修正视口并新录一轮，估计器参数没有变；两轮都保留；差异原因尚未定位，不能只用最新精度宣称稳定。

这是 35 个仿真秒的短静态驾驶，输入为三维点云，评分仅为 XY／yaw；不能与更长的二维 AMCL 对照直接排名，也不是完整三维位姿误差基准。此处尚未验证 NDT/GICP 的动态、退化与绑架恢复能力。

两个源包编译完成，上游 focused suite 342 项通过。依赖 ndt_omp_ros2 固定提交 63bf15b965b71d3a53db1757abe8e31b6114372a。[固定版本重建脚本](../../demo/build-registration.sh)使用独立工作区，发现已有 checkout 版本不同会停止，不覆盖它。
