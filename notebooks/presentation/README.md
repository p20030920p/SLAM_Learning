# 逐步展示 Notebook

中文教师演示：[SLAM_实验逐步展示.ipynb](SLAM_实验逐步展示.ipynb)。作者原库四项、静态／动态／持久变化／走廊退化四种平台测试均按“问题 → 条件 → 启动 → 现场 → 数据复算 → 结论”组织。已保存完整运行输出，现场入口默认关闭。

本机完整便携展示目录：`F:\be2演讲\展示`。

## 本机打开

1. 双击 `一键打开Notebook.bat`，启动已有的独立 Python 3.10 JupyterLab 环境，打开中文 Notebook。
2. 选择内核 **SLAM 展示 (Python 3.10)**，按 Shift+Enter 逐格运行；也可直接讲解已保存输出。Notebook 可全部复算，默认不会启动现场仿真。
3. 视频点击播放，必要时用“单独打开 MP4”；左侧目录可按章节跳转。
4. 只讲解结果时，双击 `一键打开离线展示.bat`。HTML 和视频在本地；将展示目录整体复制可继续播放，不需 Python 内核。

JupyterLab 只监听 `127.0.0.1`，使用默认鉴权。关闭启动终端或 Ctrl+C 可停止服务。若浏览器打开后 HTML 输出没有显示，请通过一键启动的本地可信目录打开，并运行相关输出单元。

## 现场操作

把某个现场单元的 `START_THIS_EXPERIMENT = False` 改为 `True`，只运行这一格。先结束上一场仿真。地图依赖顺序为建图 A → 处理最新地图 → 定位 B；未创建新地图标记时定位入口可使用发布地图。

`launch(..., auto=False)` 打开手动键盘测试。键盘焦点放在专用终端：i/k 前后，j/l 转向，u/o 横移，空格停止，q 正常结束。`auto=True, record=True` 自动驾驶并录制三个真实窗口；走廊默认自动持续运动，95 个仿真秒。

新运行保存在仓库 `results/runs/presentation`；Notebook 的表和曲线始终读取冻结发布包，不会自动换成“最新实验”。需要展示新的实验数值，应完成打包、复验再替换证据。

已有所有 BAT 仍在 `F:\be2演讲\实机脚本`。现场重新实验需要这台 Windows、原库以及 Ubuntu-24.04 ROS/Gazebo、Ubuntu-22.04 作者环境；单纯播放与复算不需要这些环境。

## 文件

- `SLAM_实验逐步展示.ipynb`：逐格演示，已执行输出。
- 同名 HTML：离线讲解；不执行现场单元。
- `evidence/`：11 个发布包和 AdaM 历史评分勘误，视频、CSV、TUM、地图、参数、日志与 SHA-256 记录。
- `experiment_tools.py`：实际误差复算、独立真值核对、绘图和现场启动函数。
- `bundle-manifest.json`：便携证据副本的文件哈希；原始大体积 ROS bag 留在本机，未伪称便携。
- `requirements.txt`：Notebook 专用环境的直接依赖；不会改动作者或 ROS 环境。

库内 Notebook 使用 `../../results/reference`；F 盘版本使用相邻 `evidence`。视频读取本地文件，不把视频 base64 塞入 ipynb；离线 HTML 保留相对链接。

## 重建

从仓库根目录执行：

```powershell
uv venv .cache/presentation-notebook --python src/.venv/Scripts/python.exe
uv pip install --python .cache/presentation-notebook/Scripts/python.exe -r notebooks/presentation/requirements.txt
$env:PYTHONUTF8='1'
& .cache/presentation-notebook/Scripts/python.exe notebooks/presentation/build_notebook.py --destination 'F:\be2演讲\展示'
```

生成器会复制发布证据，执行库内和 F 盘两份 Notebook，并导出 HTML。它会更新同名展示文件，但不会自动运行现场入口或清理其他演讲材料。
