"""Refresh the explicitly managed F-drive demonstration entries."""
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
TARGET = Path(r"F:\be2演讲\实机脚本").resolve()
TARGET.mkdir(parents=True, exist_ok=True)
LEGACY = (
    "03-静态定位对照.bat", "04-动态定位与论文地图对照.bat",
    "06-退化定位与观测恢复.bat", "07-持久结构变化定位.bat",
    "论文-dufomap.bat", "论文-beautymap.bat", "论文-ir-mcl.bat",
    "重录-动态.bat", "重录-退化.bat", "重录-四类场景.bat", "entry.ps1",
)
for name in LEGACY:
    path = (TARGET / name).resolve()
    if path.parent != TARGET:
        raise ValueError("Cleanup escaped the named script directory")
    if path.is_file():
        path.unlink()
for name in ("presentation.ps1", "record-methods.ps1", "original-live.ps1",
             "original.ps1", "build-maps.ps1", "stop-presentation.ps1", "record-map-review.ps1",
             "record-probes.ps1", "record-all-probes.ps1", "build-probe-maps.ps1", "refine-probes.ps1", "srrg.ps1"):
    (TARGET / name).write_text((SOURCE / name).read_text(encoding="utf-8-sig"), encoding="utf-8-sig")


def bat(name, command):
    (TARGET / name).write_bytes(("@echo off\nchcp 65001 >nul\n"+command+"\npause\n").replace("\n", "\r\n").encode("utf-8"))


def ps(script, args):
    return f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0{script}" {args}'


bat("00-查看本轮视频.bat", r'start "" "F:\be2演讲\本轮成片\native-ui\index.html"')
for name, flow in (
    ("01-静态建图与三维点云.bat", "mapping-static"),
    ("02-动态建图与三维点云.bat", "mapping-dynamic"),
    ("05-走廊点云建图.bat", "mapping-corridor"),
):
    bat(name, ps("presentation.ps1", f"-Flow {flow} -Duration 0"))
bat("08-处理最新走廊地图.bat", ps("build-maps.ps1", "-Scene corridor"))
bat("10-处理最新静态地图.bat", ps("build-maps.ps1", "-Scene static"))
bat("11-处理最新动态地图.bat", ps("build-maps.ps1", "-Scene dynamic"))
bat("09-正常停止仿真.bat", ps("stop-presentation.ps1", ""))
for name, scene in (
    ("20-静态_三方法独立RViz实时.bat", "static"),
    ("21-动态_三方法独立RViz实时.bat", "dynamic"),
    ("22-持久变化_三方法独立RViz实时.bat", "large-change"),
    ("23-走廊退化_三方法独立RViz实时.bat", "degradation"),
):
    bat(name, ps("record-methods.ps1", f"-Scene {scene} -Keyboard -Duration 86400"))
commands = []
for scene in ("static", "dynamic", "large-change", "degradation"):
    duration = 100 if scene == "degradation" else 85
    commands += [ps("record-methods.ps1", f"-Scene {scene} -Duration {duration}"), "if errorlevel 1 exit /b 1"]
bat("24-自动重录四场景_逐方法实时.bat", "\n".join(commands))
for method in ("dufomap", "beautymap", "ir-mcl"):
    bat(f"论文-实时-{method}.bat", ps("original-live.ps1", f"-Method {method}"))
bat("论文-adam-mcl.bat", ps("original.ps1", "-Method adam-mcl -Trials 1 -Record"))
for number, method in ((31, "ndt"), (32, "gicp")):
    bat(f"{number}-{method.upper()}三维定位_静态.bat", ps("presentation.ps1", f"-Flow localization-{method}-static -Duration 0 -Record"))
for number, scene, label in ((33, "static", "静态"), (34, "dynamic", "动态"),
                             (35, "large-change", "持久变化"), (36, "degradation", "走廊退化")):
    duration = 120 if scene == "degradation" else 90
    bat(f"{number}-三维{label}_三图GICP对照.bat", ps("record-methods.ps1", f"-Scene {scene} -Dimension 3D -Duration {duration}"))
bat("37-三维地图清理结果展示.bat", ps("record-map-review.ps1", "-Duration 30"))
bat("38-采集假设实验地图A.bat", ps("build-probe-maps.ps1", ""))
bat("39-查看假设实验视频.bat", r'start "" "F:\be2演讲\本轮成片\hypotheses\index.html"')
for dimension, start in (("2D", 40), ("3D", 45)):
    for offset, (scene, label) in enumerate((("static", "静态"), ("dynamic", "动态"),
                                             ("large-change", "持久变化"), ("degradation", "原走廊退化"),
                                             ("height-corridor", "高处标志_派生对照"))):
        bat(f"{start + offset}-{dimension}_{label}_假设实验.bat", ps("record-probes.ps1", f"-Scene {scene} -Dimension {dimension}"))
bat("50-自动重录假设实验_二维三维十组.bat", ps("record-all-probes.ps1", ""))
for number, dimension, scene, label in ((51, "2D", "corridor", "原走廊"), (52, "2D", "height-corridor", "高处对照"),
                                        (53, "3D", "corridor", "原走廊"), (54, "3D", "height-corridor", "高处对照")):
    bat(f"{number}-{dimension}_{label}_封存输入细化.bat", ps("refine-probes.ps1", f"-Dimension {dimension} -Scene {scene}"))
bat("55-自动重算四组细化_封存输入.bat", ps("refine-probes.ps1", "-All"))
bat("56-查看SRRG二维视频与指标.bat", r'start "" "F:\be2演讲\本轮成片\mapping-2d\index.html"')
for number,scene,label in ((57,'static','静态'),(58,'dynamic','运动障碍物'),(59,'large-change','持久变化_加载旧图'),(60,'corridor','走廊退化')):
    bat(f'{number}-SRRG二维_{label}.bat',ps('srrg.ps1',f'-Scene {scene}'))
bat('61-自动录制SRRG二维四场景.bat',ps('srrg.ps1','-All'))
(TARGET / "使用说明.md").write_text(r"""# 当前现场脚本

- 00：打开最新视频目录。
- 01 / 02 / 05：静态、动态、新走廊建图 A；二维 slam_toolbox + 独立三维点云采集。
- 08：处理新走廊 A，生成 Raw / DUFOMap / BeautyMap 地图。更改走廊模型后必须重新执行 05 → 08 → 23，禁止混用旧地图。
- 10 / 11：处理最新静态／动态建图 A；再运行对应定位入口。
- 20 / 21 / 22 / 23：对应四种环境，三个独立 RViz、相同 AMCL、不同地图，同时记录现场。
- 24：自动录制四种环境。每次新运行目录，不覆盖已封存证据。
- 31 / 32：NDT / GICP 原库三维固定地图定位；使用 /points 和原生输出 pcl_pose。无 IMU、无逐点去畸变。
- 33 / 34 / 35 / 36：四种场景的 Raw／DUFOMap／BeautyMap 三维地图，共用GICP，三个独立窗口与录像；三维走廊也施加观测限制。
- 37：已经计算好的三维地图结果展示，红色为残留动态点；不执行新的算法推理。
- 38：重新采集假设实验的静态、动态、原走廊、高处标志对照地图A，保留真实二维／三维雷达和深度相机输入；给定位姿建图。
- 39：打开假设实验视频与指标目录。
- 40–44：二维雷达＋深度相机，依次为静态、动态、持久变化、原走廊、高处标志派生对照；二维B机器人没有三维雷达。
- 45–49：三维雷达＋同一深度相机，对应相同五个场景。
- 50：自动录制并验证全部十组。缺少地图A时先采集；已有地图时复用。每组包含Plain、H1 Guard、H2 Depth、H3 LiDAR Search、H3 Depth + Search，以及原生AMCL／GICP参照，真实窗口共同录制。
- 51–54：分别对二维／三维原走廊和高处对照的封存输入重新计算粗到细候选；55自动重算四组。输出视频是保存位姿的结果回放，没有新增Gazebo实录。
- 56：SRRG二维视频、地图指标和失败诊断；57–60：相同四类环境的作者原生二维建图，61顺序录制全部四组。静态组导出作者旧图后，持久变化组加载旧图开启多会话更新。需要 Ubuntu-20.04 / Noetic 作者库，首次构建用源库 src/scripts/presentation/srrg/build.py。
- SRRG主对照保持作者默认关闭图合并；局部动态点融合开启。开启图合并的数值失败单独保留。旧20–24入口仍为三维清理图的二维投影参照。
- 57–61每轮自动写出srrg-quality.json评分与maps/raw、maps/srrg占据图，便于手动测试定位B；不会覆盖已经发表的参考视频。
- 论文-实时-*：DUFOMap / BeautyMap / IR-MCL 原库计算与 RViz 当前状态。
- 论文-adam-mcl：一次受限数据试验，单位为格，不作为论文精度复现。
- 09：正常结束活动仿真。

一次启动一个场景。键盘在 SLAM-LIVE 终端：i/k 前后，j/l 转向，u/o 横移，空格停止，q 结束。超过 0.4 秒无按键自动停车。31 / 32 与 20–23 均录窗口。33–36自动巡航并录制；2D与3D录像分目录存放，单次误差不作方法排名。

需要本机已配置的 Windows Terminal、FFmpeg、Ubuntu-24.04 ROS Jazzy / Gazebo，以及 Ubuntu-22.04 作者环境。源库 D:\workspace\be2\slam_learning_updated；原始输出在 results\runs\presentation；录像复制到 F:\be2演讲\屏幕实录\20261014-native-ui。

实体机器人尚未测试。本目录的 BAT / PS1 是仿真与原库演示入口。

假设实验结果自动封存到 F:\be2演讲\本轮成片\hypotheses\2D 或 3D，目录页同步更新；校准版原始会话在 F:\be2演讲\原始会话\hypotheses-calibrated，较早原型仍在源库 results\runs\presentation。每次新目录，不覆盖封存数据。深度为80°水平视场、0.25–4m的真实渲染；车体高度由建图A位姿与真实URDF外参标定，定位B不读真值。原型约束平坦地面机器人的x/y/yaw，固定A标定高度和roll/pitch，不是完整六自由度SLAM。高处标志场景是另加几何的可行性对照，不能冒充原走廊结果。原型参数与日志在每组record中；讲义见源库 docs\testing\HYPOTHESES.zh-CN.md。
""", encoding="utf-8")
print(f"Removed {len(LEGACY)} obsolete managed entries; refreshed current scripts: {TARGET}")
