# 代码展示 Notebook

[SLAM_实验逐步展示.ipynb](SLAM_实验逐步展示.ipynb)：19 个已执行代码单元，四篇原库、四种机器人条件、新走廊和 NDT/GICP 部署。文字只保留章节标题；代码包含启动命令、视频读取、时间关联与误差复算。

1. 双击 F:\be2演讲\展示\一键打开Notebook.bat。
2. 内核选择 SLAM 展示 (Python 3.10)，Shift+Enter 逐格运行。
3. 现场启动单元默认 RUN_LIVE=False；只在需要时改为 True，先结束上一场。
4. 离线观看使用一键打开离线展示.bat。

视频与评分读取相邻 evidence，库内版本读取 results/reference。默认 Run All 不启动仿真。Live execution 为真实窗口计算；Measured result replay 为该次保存输出，无新推理。

- 建图与处理顺序：A → 地图处理 → 独立定位 B。新走廊对应 05 → 08 → 23。
- 键盘在 SLAM-LIVE 终端：i/k 前后、j/l 转向、u/o 横移、空格停止、q 结束。
- 15 个当前证据包保留 CSV、TUM、参数、视频与绑定哈希；原始大 bag 留在本机运行目录。
- NDT 两轮分数都保留，差异原因待查。二维与三维输入不直接排名，实体机器人待测。

本机 JupyterLab 只监听 127.0.0.1，保留默认鉴权。复制展示目录可离线播放，但现场执行仍依赖这台电脑的 ROS / Gazebo / 作者环境。

重新生成并执行使用 build_notebook.py；依赖在独立 Notebook 环境中。生成器会更新同名文件，不会自动执行现场启动单元。
