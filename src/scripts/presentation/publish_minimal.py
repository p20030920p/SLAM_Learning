"""Render table-only bilingual indexes of every tracked GIF/MP4 and experiment settings."""

import json
import re
import subprocess
from pathlib import Path

from publish_map_quality import legacy_minimal
from publish_mapping_focus import SETUP_EN, SETUP_ZH

ROOT = Path(__file__).resolve().parents[3]

TRANSLATIONS = {
    "静态A旧图": "static A old map",
    "动态格删除": "Dynamic cell removal",
    "静态格保留": "Static cell retention",
    "动态残影删除": "Dynamic ghost removal",
    "动态点删除": "Dynamic point removal",
    "静态覆盖保留": "Static coverage retained",
    "静态点保留": "Static point retention",
    "动态删除": "Dynamic removal",
    "静态保留": "Static retention",
    "动态删／静态留：": "Dynamic removal / static retention: ",
    "实机传感器录制；清理指标不适用": "Hardware sensor capture; cleaning metrics N/A",
    "早期场景演示；未绑定地图清理评分，保留原片": "Early scene demo; no bound cleaning score; retained",
    "传感器／建图过程演示；未评分": "Sensor/mapping demonstration; unscored",
    "失败诊断：图合并数值崩溃，最后成功仿真66.0s／录制55.4s": "Failure: numerical graph-merge crash; last native sim 66.0s / recording offset 55.4s",
    "联调失败诊断；已修复，保留原片": "Integration failure diagnostic; fixed; retained",
    "定位原型；地图清理指标不适用；": "Pose prototype; map-cleaning metrics N/A; ",
    "旧z=0诊断（保留，不参与排名）；": "Earlier z=0 diagnostic (retained; not ranked); ",
    "定位RMSE（清理指标不适用／未标注）：": "Pose RMSE (cleaning N/A or unlabelled): ",
    "历史10轮定位RMSE均值": "Historical mean pose RMSE over 10 trials: ",
    "格（已勘误）；清理指标不适用": " cells (corrected); cleaning N/A",
    "定位RMSE": "Pose RMSE",
    "格；清理指标不适用": " cells; cleaning N/A",
    "；清理指标不适用": "; cleaning N/A",
    "旧图A静态": "Old-map A static",
    "；B未更新": "; B not updated",
    "未测试": "untested",
    "（": " (",
    "）": ")",
    "；": "; ",
    "／": " / ",
    "：": ": ",
    "、": ", ",
    "，": ", ",
}


def english(text):
    for source, target in TRANSLATIONS.items():
        text = text.replace(source, target)
    return text


def render():
    legacy_minimal()
    old = (ROOT / "docs/MINIMAL.zh-CN.md").read_text(encoding="utf-8").splitlines()[2:]
    source_rows = []
    for line in old:
        parts = [p.strip() for p in line.split("|")[1:-1]]
        match = re.search(r"\]\(\.\./([^)]*)\)", parts[1])
        source_rows.append((match.group(1), parts[0], parts[2]))
    tracked = subprocess.check_output(["git", "ls-files", "*.mp4"], cwd=ROOT, text=True).splitlines()
    videos = set(tracked)
    slots = json.loads((ROOT / "docs/figures/slots.json").read_text())["slots"]
    labels = {s["path"]: s["caption"].get("en", s["id"]) for s in slots if s.get("status") == "published"}
    for chinese in (False, True):
        rows = [
            "| 导航 | 入口 |" if chinese else "| Navigation | Link |",
            "| --- | --- |",
            "| 语言 | [English](MINIMAL.md) / [中文](MINIMAL.zh-CN.md) |"
            if chinese
            else "| Language | [English](MINIMAL.md) / [中文](MINIMAL.zh-CN.md) |",
            "| 主文 | [English](../README.md) / [中文](HOME.zh-CN.md) |"
            if chinese
            else "| Main article | [English](../README.md) / [中文](HOME.zh-CN.md) |",
            "| 查看方式 | 点击GIF／MP4；保留成功、无效和失败记录；单轮不排名 |"
            if chinese
            else "| Viewing | Open GIF/MP4; positive, null and failed runs retained; single trials do not establish a ranking |",
            "",
            "| 实验／设置 | 输入和地图 | 指标／范围 |"
            if chinese
            else "| Experiment / setup | Inputs and map | Metrics / scope |",
            "| --- | --- | --- |",
        ]
        zh = [
            "| 原库清理 | KITTI等作者数据；原库参数见主文 | DUFO／Beauty点级DA／SA；不与仿真排名 |",
            "| 原生二维SRRG | 四场景；二维雷达＋里程计，无三维雷达；已知起点 | 残影删除／静态覆盖；动态42.31%／99.51%；独立定位B待测 |",
            "| 旧二维投影＋AMCL | 四场景；三维清理图投影，定位使用二维扫描 | 动态格DA／静态格SA；另报XY RMSE，含初始化 |",
            "| 三维清理＋GICP | 四场景；三维扫描，给定位姿建图A；独立定位B无真值输入 | 源点DA／SA；另报XYZ RMSE，含初始化；走廊覆盖不同不排名 |",
            "| 历史定位假设 | 五场景×2D／3D＋深度；五原型同帧；地图冻结 | 只测定位／恢复，不是动态建图；细化回放无新仿真 |",
            "| 时长／重复 | 逐记录为准；假设普通场景90s、走廊120s；前50s限制雷达后恢复 | 仿真秒；主要场景每条件一轮，不能推出稳定排名 |",
            "| 地图与定位区分 | DA=动态删除，SA=静态保留；无动态样本N/A | 清理率不是几何误差；更干净不保证定位更准 |",
            "| SRRG退化检查 | 11.1s跟踪重置；11.5s持续偏差>20cm；57.6s恢复扫描 | 仿真时刻；MP4首告警约4.6s；非独立测得地图坍塌时刻 |",
        ]
        en = [
            "| Author cleaning | KITTI / author data; native parameters in main article | DUFO/Beauty point DA/SA; no ranking against simulator |",
            "| Native 2D SRRG | Four scenes; 2D lidar + odometry, no 3D lidar; known start | Ghost removal / static coverage; dynamic 42.31% / 99.51%; held-out localization B pending |",
            "| Legacy projection + AMCL | Four scenes; projected 3D-cleaned maps, 2D localization scans | Dynamic/static cell DA/SA; separate XY RMSE, initialization included |",
            "| 3D cleaning + GICP | Four scenes; supplied-pose mapping A, independent localization B with no truth input | Point DA/SA; separate XYZ RMSE, initialization included; unequal corridor coverage prevents ranking |",
            "| Earlier localization hypotheses | Five scenes × 2D/3D + depth; five prototypes share frames; frozen maps | Pose/recovery only, not dynamic mapping; refinement replay has no new simulation |",
            "| Duration / repeats | Per-record settings; hypothesis scenes 90s, corridors 120s; constrained lidar first 50s then restored | Simulation seconds; primary conditions have one run, insufficient for stable ranking |",
            "| Map vs pose | DA=dynamic removal, SA=static retention; no dynamic samples=N/A | Cleaning scores are not geometric error; cleaning need not improve localization |",
            "| SRRG corridor inspection | Tracking reset 11.1s; sustained >20cm error 11.5s; scan restoration 57.6s | Simulation timestamps; first warning around MP4 4.6s; no independently measured map-collapse time |",
        ]
        rows.extend(zh if chinese else en)
        rows += [
            "",
            ("| 器材参数 | 实际设置 |" if chinese else "| Equipment | Actual setting |"),
            "| --- | --- |",
        ]
        setup = SETUP_ZH if chinese else SETUP_EN
        rows.extend(
            line
            for line in setup.splitlines()
            if line.startswith("|") and not line.startswith(("| ---", "| 项目", "| Item"))
        )
        rows += [
            "",
            "| 地图／算法参数 | 设置 |" if chinese else "| Map / algorithm parameter | Setting |",
            "| --- | --- |",
        ]
        rows += [
            "| DUFOMap | voxel=0.10m; d_s=0.20m; d_p=1; threads=2 |",
            "| BeautyMap (Gazebo) | XY=0.50m; Z=0.20m; range=8m; offline |",
            "| SRRG | native local projective merge ON; graph merge OFF in four main runs; 10cm support / 15cm coverage tolerance |",
            "| AMCL / GICP | frozen-map B; nearest truth ≤0.05 simulation seconds; no trajectory fitting |",
            "| Native source | [URDF](../config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf) / [map processing](../src/scripts/presentation/build_maps.py) / [SRRG](papers/srrg_mapper2d.zh-CN.md) |",
            "",
            "| 实验／地图 | GIF / MP4 | 指标效果 |"
            if chinese
            else "| Experiment / map | GIF / MP4 | Metric / effect |",
            "| --- | --- | --- |",
        ]
        used = set()
        for path, label, effect in source_rows:
            gif = Path(path)
            choices = [gif.with_suffix(".mp4").as_posix()]
            if gif.stem == "preview":
                choices += [(gif.parent / name).as_posix() for name in ("replay.mp4", "execution.mp4")]
            video = next((p for p in choices if p in videos), None)
            links = f"[GIF](../{path})"
            if video:
                links += f" / [MP4](../{video})"
                used.add(video)
            if not chinese:
                label = labels.get(path, gif.with_suffix("").as_posix().replace("results/reference/", ""))
                effect = english(effect)
                if re.search(r"[\u4e00-\u9fff]", effect):
                    raise ValueError(f"Untranslated effect: {effect}")
            rows.append(f"| {label} | {links} | {effect} |")
        for path in sorted(videos - used):
            package = path.split("/")[2] if path.startswith("results/reference/") else path
            effect = (
                "补充实录／回放；对应指标见同实验GIF行，不新增评分"
                if chinese
                else "Additional capture/replay; use the same experiment's GIF score; no additional measurement"
            )
            rows.append(f"| {package} / {Path(path).name} | [MP4](../{path}) | {effect} |")
        output = ROOT / "docs" / ("MINIMAL.zh-CN.md" if chinese else "MINIMAL.md")
        output.write_text("\n".join(rows) + "\n", encoding="utf-8")
        print(output.name, len(source_rows), "GIFs;", len(videos), "MP4s")


if __name__ == "__main__":
    render()
