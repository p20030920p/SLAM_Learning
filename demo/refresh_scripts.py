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
             "original.ps1", "build-maps.ps1", "stop-presentation.ps1"):
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
(TARGET / "使用说明.md").write_text(r"""# 当前现场脚本

- 00：打开最新视频目录。
- 01 / 02 / 05：静态、动态、新走廊建图 A；二维 slam_toolbox + 独立三维点云采集。
- 08：处理新走廊 A，生成 Raw / DUFOMap / BeautyMap 地图。更改走廊模型后必须重新执行 05 → 08 → 23，禁止混用旧地图。
- 10 / 11：处理最新静态／动态建图 A；再运行对应定位入口。
- 20 / 21 / 22 / 23：对应四种环境，三个独立 RViz、相同 AMCL、不同地图，同时记录现场。
- 24：自动录制四种环境。每次新运行目录，不覆盖已封存证据。
- 31 / 32：NDT / GICP 原库三维固定地图定位；使用 /points 和原生输出 pcl_pose。无 IMU、无逐点去畸变。
- 论文-实时-*：DUFOMap / BeautyMap / IR-MCL 原库计算与 RViz 当前状态。
- 论文-adam-mcl：一次受限数据试验，单位为格，不作为论文精度复现。
- 09：正常结束活动仿真。

一次启动一个场景。键盘在 SLAM-LIVE 终端：i/k 前后，j/l 转向，u/o 横移，空格停止，q 结束。超过 0.4 秒无按键自动停车。31 / 32 与 20–23 均录窗口。

需要本机已配置的 Windows Terminal、FFmpeg、Ubuntu-24.04 ROS Jazzy / Gazebo，以及 Ubuntu-22.04 作者环境。源库 D:\workspace\be2\slam_learning_updated；原始输出在 results\runs\presentation；录像复制到 F:\be2演讲\屏幕实录\20261014-native-ui。

实体机器人尚未测试。本目录的 BAT / PS1 是仿真与原库演示入口。
""", encoding="utf-8")
print(f"Removed {len(LEGACY)} obsolete managed entries; refreshed current scripts: {TARGET}")
