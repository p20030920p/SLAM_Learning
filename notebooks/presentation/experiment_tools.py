"""Read frozen evidence and drive the local, step-by-step teaching notebook."""
from __future__ import annotations

import hashlib
import html
import json
import math
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

import matplotlib.pyplot as plt
import numpy as np
from IPython.display import HTML, Markdown, display
from PIL import Image

PACKAGES = (
    "robot-supp-static", "robot-supp-dynamic", "robot-supp-large-change", "robot-corridor-v2-mapping",
    "robot-live-static", "robot-live-dynamic", "robot-live-large-change", "robot-corridor-v2",
    "desktop-live-dufomap", "desktop-live-beautymap", "desktop-live-ir-mcl", "desktop-adam-mcl",
    "robot-ndt-static", "robot-gicp-static", "robot-ndt-static-initial",
)
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "evidence"
if not DATA.exists():
    DATA = ROOT.parent.parent / "results" / "reference"
REPO = Path(os.environ.get("SLAM_DEMO_REPO", r"D:\workspace\be2\slam_learning_updated"))
if (ROOT.parent.parent / "demo" / "presentation.ps1").is_file():
    REPO = ROOT.parent.parent
plt.rcParams.update({"font.family": ["Microsoft YaHei", "DejaVu Sans"],
                     "axes.unicode_minus": False, "figure.dpi": 110})


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def package(name: str) -> Path:
    if name not in PACKAGES and name != "adam-mcl":
        raise ValueError(f"Unknown frozen package: {name}")
    return DATA / name


def table(headers, rows):
    head = "".join(f"<th>{html.escape(str(x))}</th>" for x in headers)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(x))}</td>" for x in row) + "</tr>"
                   for row in rows)
    display(HTML('<table class="experiment-table"><thead><tr>' + head
                 + "</tr></thead><tbody>" + body + "</tbody></table>"))


def local_url(path: Path) -> str:
    # JupyterLab's HTML renderer does not resolve every video source against the
    # notebook directory. Use the authenticated file endpoint; the HTML exporter
    # turns it back into a relative offline URL.
    server_root = ROOT if (ROOT / "evidence").is_dir() else ROOT.parent.parent
    return "/files/" + quote(path.relative_to(server_root).as_posix(), safe="/")


def videos(name: str, result: bool = True):
    """Relative local URLs, no base64 videos or network dependency."""
    parts = []
    for kind, title in [("execution", "现场执行 / 墙钟时间"), ("result", "保存结果回放 / 无新推理")]:
        path = package(name) / f"{kind}.mp4"
        if not path.exists() or (kind == "result" and not result):
            continue
        src = local_url(path)
        poster = f' poster="{local_url(package(name) / "frame-mid.png")}"' if kind == "execution" else ""
        parts.append(f'<div><strong>{title}</strong><video controls preload="none"{poster} '
                     f'style="width:100%;max-width:900px;display:block" src="{src}"></video>'
                     f'<a href="{src}" target="_blank">单独打开 MP4</a></div>')
    display(HTML('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));'
                 'gap:18px">' + "".join(parts) + "</div>"))


def verify_files():
    rows, total = [], 0
    for name in PACKAGES:
        record = read_json(package(name) / "record.json")
        count = 0
        for relative, expected in record["artifacts"].items():
            if expected.get("availability") != "portable":
                continue
            path = package(name) / Path(relative.replace("\\", "/"))
            assert path.is_file(), path
            assert path.stat().st_size == expected["bytes"], path
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected["sha256"], path
            count += 1
        total += count
        rows.append([name, record["status"], count, "SHA-256 一致"])
    table(["实验包", "状态", "核对文件", "结果"], rows)
    print(f"共核对 {total} 个记录绑定文件；大体积 ROS bag / 点云源文件仍保留在本机原始运行目录。")
    return total


def samples(name: str, case: str) -> np.ndarray:
    arr = np.genfromtxt(package(name) / f"{case}-samples.csv", delimiter=",", names=True)
    assert len(arr) >= 2 and np.all(np.diff(arr["stamp_s"]) >= 0)
    e = np.hypot(arr["estimate_x"] - arr["truth_x"], arr["estimate_y"] - arr["truth_y"])
    d = arr["estimate_yaw"] - arr["truth_yaw"]
    yaw = np.arctan2(np.sin(d), np.cos(d))
    assert np.allclose(e, arr["position_error_m"], atol=1e-10, rtol=0)
    assert np.allclose(yaw, arr["yaw_error_rad"], atol=1e-10, rtol=0)
    assert np.all((arr["nearest_truth_delta_s"] >= 0) & (arr["nearest_truth_delta_s"] <= .05))
    return arr


def check_truth(name: str, arr: np.ndarray):
    truth = [json.loads(x) for x in (package(name) / "truth.jsonl").read_text().splitlines()]
    stamps = np.array([x["stamp_s"] for x in truth])
    assert np.all(np.diff(stamps) >= 0)
    for row in arr:
        idx = int(np.argmin(abs(stamps - row["stamp_s"])))
        t = truth[idx]
        qx, qy, qz, qw = t["xyzw"]
        yaw = math.atan2(2*(qw*qz + qx*qy), 1 - 2*(qy*qy + qz*qz))
        assert t["model"] == "omni_car"
        assert np.allclose([row["truth_x"], row["truth_y"], row["truth_yaw"]],
                           [*t["xyz"][:2], yaw], atol=1e-10, rtol=0)
        assert math.isclose(abs(stamps[idx] - row["stamp_s"]), row["nearest_truth_delta_s"], abs_tol=1e-10)


def score(arr: np.ndarray) -> dict:
    warm = arr[arr["stamp_s"] >= arr["stamp_s"][0] + 5]
    return {"samples": len(arr),
            "position_rmse_m": float(np.sqrt(np.mean(arr["position_error_m"]**2))),
            "yaw_rmse_deg": float(np.rad2deg(np.sqrt(np.mean(arr["yaw_error_rad"]**2)))),
            "position_p95_m": float(np.percentile(arr["position_error_m"], 95)),
            "post_warmup_5s_samples": len(warm),
            "post_warmup_5s_position_rmse_m": float(np.sqrt(np.mean(warm["position_error_m"]**2)))}


def score_table(name: str):
    rows = []
    expected = read_json(package(name) / "metrics.json")["cases"]
    for case, saved in expected.items():
        arr = samples(name, case)
        check_truth(name, arr)
        actual = score(arr)
        for key, value in actual.items():
            assert math.isclose(value, saved[key], rel_tol=0, abs_tol=1e-10), (name, case, key)
        rows.append([case, actual["samples"], f'{actual["position_rmse_m"]*100:.3f}',
                     f'{actual["post_warmup_5s_position_rmse_m"]*100:.3f}',
                     f'{actual["yaw_rmse_deg"]:.3f}', f'{actual["position_p95_m"]*100:.3f}'])
    table(["地图 / 输入组", "更新数", "全窗 RMSE (cm)", "首条后 5s RMSE (cm)",
           "偏航 RMSE (°)", "位置 P95 (cm)"], rows)
    print("由原生更新的估计与真值重新计算；最近真值时间差 ≤0.05 仿真秒；没有轨迹对齐。")


def trajectory_plot(name: str, cases=("raw", "dufomap", "beautymap")):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.4))
    first = samples(name, cases[0])
    axes[0].plot(first["truth_x"], first["truth_y"], "k--", label="独立 Gazebo 真值", linewidth=2)
    for case in cases:
        arr = samples(name, case)
        axes[0].plot(arr["estimate_x"], arr["estimate_y"], label=case, alpha=.8)
        axes[1].plot(arr["stamp_s"], arr["position_error_m"]*100, label=case, alpha=.8)
    axes[0].set(xlabel="世界 X (m)", ylabel="世界 Y (m)", title="原生定位轨迹，无空间对齐")
    axes[0].set_aspect("equal", adjustable="datalim")
    axes[1].set(xlabel="仿真时间 (s)", ylabel="位置误差 (cm)", title="每次原生 AMCL 更新")
    for ax in axes:
        ax.grid(alpha=.25)
        ax.legend()
    fig.tight_layout()
    display(fig)
    plt.close(fig)


def map_comparison(name: str):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    rows = []
    for case, ax in zip(("raw", "dufomap", "beautymap"), axes):
        path = package(name) / "maps" / case
        image = np.asarray(Image.open(path / "map.pgm"))
        processing = read_json(path / "processing.json")
        method = processing["methods"][case]
        ax.imshow(image, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
        ax.set_title(f'{case}: {method["points"]:,} 点')
        ax.axis("off")
        rows.append([case, method["points"], method["resolution_m"],
                     hashlib.sha256((path / "map.pgm").read_bytes()).hexdigest()[:16]])
    fig.suptitle("同次建图 A 的三维点云输出 → 同一投影规则 → 二维固定定位地图")
    fig.tight_layout()
    display(fig)
    plt.close(fig)
    table(["地图", "输出点数", "栅格 (m)", "PGM SHA-256 前16位"], rows)
    print("点数只是处理输出规模；没有逐点静动态真值，不能换算静态误删率。")


def mapping_info(name: str):
    m = read_json(package(name) / "metrics.json")
    table(["项目", "本轮记录"], [
        ["三维点云消息", m["points_received"]], ["保存建图帧", m["mapping_frames"]],
        ["在线二维地图", f'{m["observed_map"]["width"]} × {m["observed_map"]["height"]}'],
        ["已知栅格数", m["observed_map"]["known_cells"]],
        ["三维建图位姿", "给定的 Gazebo 传感器位姿；不是三维 SLAM 产出"],
    ])


def recovery_window(arr: np.ndarray, restore: float):
    after = arr[arr["stamp_s"] >= restore]
    if len(after) < 8 or after["stamp_s"][-1] - after["stamp_s"][0] < 5:
        return None
    for i, row in enumerate(after):
        end = int(np.searchsorted(after["stamp_s"], row["stamp_s"] + 5, side="left"))
        if end >= len(after):
            continue
        window = after[i:end+1]
        if len(window) >= 8 and window["stamp_s"][-1] - row["stamp_s"] >= 5 - 1e-9:
            if np.all((window["position_error_m"] < .1) & (abs(window["yaw_error_rad"]) < np.deg2rad(5))):
                return (float(row["stamp_s"]), float(window["stamp_s"][-1]), len(window))
    return None


def degradation_analysis():
    name = "robot-degradation"
    events = [json.loads(x) for x in (package(name) / "scan-stress.jsonl").read_text().splitlines()]
    restore = min(x["stamp_s"] for x in events if x["phase"] == "restored")
    record = read_json(package(name) / "record.json")
    rows = []
    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(12, 7))
    for case, label in [("raw", "完整观测"), ("degraded_raw", "受限 → 恢复")]:
        arr = samples(name, case)
        before, after = arr[arr["stamp_s"] < restore], arr[arr["stamp_s"] >= restore]
        window = recovery_window(arr, restore)
        assert window is not None, "缺少满足持续判据的记录，不可称为恢复成功"
        delay = window[0] - restore
        assert math.isclose(delay, record["restoration"][case]["sustained_convergence_delay_s"], abs_tol=1e-10)
        rows.append([label, len(before), len(after), f'{score(before)["position_rmse_m"]:.4f}',
                     f'{score(after)["position_rmse_m"]:.4f}',
                     f'{arr["position_error_m"][-1]*100:.2f}', f"{delay:.1f}",
                     f"{window[1]-restore:.1f}", window[2]])
        axes[0].plot(arr["stamp_s"], arr["position_error_m"], label=label)
        axes[1].plot(arr["stamp_s"], np.rad2deg(abs(arr["yaw_error_rad"])), label=label)
        if case == "degraded_raw":
            for ax in axes:
                ax.axvspan(window[0], window[1], color="#22c55e", alpha=.14, label="首次满足持续判据的窗口")
    for ax in axes:
        ax.axvline(restore, color="#dc2626", linestyle="--", label=f"恢复原始扫描 t={restore:.1f}s")
        ax.grid(alpha=.25)
        ax.legend(loc="upper right")
    axes[0].axhline(.1, color="gray", linestyle=":")
    axes[1].axhline(5, color="gray", linestyle=":")
    axes[0].set(ylabel="位置误差 (m)", title="走廊：初值 X 偏差 1m，机器人持续运动")
    axes[1].set(xlabel="仿真时间 (s)", ylabel="绝对偏航误差 (°)")
    fig.tight_layout()
    display(fig)
    plt.close(fig)
    table(["组", "恢复前更新", "恢复后更新", "前 RMSE(m)", "后 RMSE(m)", "末误差(cm)",
           "稳定窗口起点延迟(s)", "可确认延迟(s)", "确认窗口更新数"], rows)
    geometry = read_json(package(name) / "geometry-audit.json")
    table(["实际扫描", "扫描帧", "法向小/大特征值比中位数"],
          [[k, geometry[k]["scan_frames"], f'{geometry[k]["median_normal_ratio"]:.6f}']
           for k in ["full_before", "limited", "restored"]])
    print("11.3s 指首次稳定窗口的起点；必须观察到窗口末端才可确认。法向比仅为局部诊断。")


def author_lidar(name: str):
    m = read_json(package(name) / "metrics.json")
    c = m["counts"]
    sa = 100*c["kept_static"]/(c["kept_static"] + c["removed_static"])
    da = 100*c["removed_dynamic"]/(c["kept_dynamic"] + c["removed_dynamic"])
    ha = 2*sa*da/(sa+da)
    for key, value in [("SA", sa), ("DA", da), ("HA", ha)]:
        assert math.isclose(value, m[key], abs_tol=1e-10)
    table(["量", "独立评分器的已保存计数"], list(c.items()))
    table(["SA (%)", "DA (%)", "HA (%)", "近邻距离阈值(m)"],
          [[f"{sa:.4f}", f"{da:.4f}", f"{ha:.4f}", m["threshold_m"]]])
    print("这里重算计数的比率；不重载大体积 PCD 做近邻搜索，不声称本轮 PCL 交叉核验。")


def ir_analysis():
    truth = np.loadtxt(package("desktop-ir-mcl") / "seq_1_gt_pose.txt")
    estimate = np.loadtxt(package("desktop-ir-mcl") / "IRMCL.txt")
    assert truth.shape == estimate.shape and np.allclose(truth[:, 0], estimate[:, 0])
    keep = truth[:, 0] >= truth[0, 0] + 20
    truth, estimate = truth[keep], estimate[keep]
    assert len(truth) == 1354
    position = np.linalg.norm(estimate[:, 1:3] - truth[:, 1:3], axis=1)*100
    def yaw(tum):
        qx, qy, qz, qw = tum[:, 4:8].T
        return np.arctan2(2*(qw*qz+qx*qy), 1-2*(qy*qy+qz*qz))
    angle = yaw(estimate) - yaw(truth)
    angle = np.rad2deg(abs(np.arctan2(np.sin(angle), np.cos(angle))))
    measured = {"location_rmse_cm": round(float(np.sqrt(np.mean(position**2))), 2),
                "yaw_rmse_deg": round(float(np.sqrt(np.mean(angle**2))), 2)}
    measured.update({f"location_lt{n}_pct": round(float(np.mean(position < n)*100), 2) for n in (5, 10, 20)})
    measured.update({k: round(float(np.mean(angle < n)*100), 2) for k, n in
                     [("yaw_lt0_5_pct", .5), ("yaw_lt1_pct", 1), ("yaw_lt2_pct", 2)]})
    assert measured == read_json(package("desktop-ir-mcl") / "metrics.json")["measured"]
    table(["指标", "本次原生轨迹复算"], list(measured.items()))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(truth[:, 1], truth[:, 2], "k--", label="发布真值")
    axes[0].plot(estimate[:, 1], estimate[:, 2], label="IR-MCL 本次估计")
    axes[0].set_aspect("equal", adjustable="datalim")
    axes[0].set(xlabel="X(m)", ylabel="Y(m)", title="1354 帧评分窗口，无对齐")
    axes[1].plot(truth[:, 0], position)
    axes[1].set(xlabel="序列时间(s)", ylabel="位置误差(cm)", title="首20秒按原协议排除")
    axes[0].legend()
    fig.tight_layout()
    display(fig)
    plt.close(fig)


def adam_analysis():
    path = package("desktop-adam-mcl")
    distance = np.loadtxt(path / "error_position.txt")
    times = np.loadtxt(path / "time_consumption.txt")
    actual = float(np.sqrt(np.mean(distance**2)))
    m = read_json(path / "metrics.json")
    assert len(distance) == m["updates"] == 123
    assert math.isclose(actual, m["position_rmse_cells"], abs_tol=1e-10)
    assert math.isclose(float(distance[-1]), m["final_error_cells"], abs_tol=1e-10)
    assert math.isclose(float(np.mean(times)), m["mean_update_seconds"], abs_tol=1e-10)
    native_log = (path / "native-output.log").read_text(encoding="utf-8")
    truth = np.array([[float(v) for v in line.split()] for line in
                      re.findall(r"^Ground truth: (.+)$", native_log, flags=re.M)])
    assert len(truth) == len(distance)
    jump_index = int(np.argmax(np.linalg.norm(np.diff(truth[:, :2], axis=0), axis=1))) + 1
    print(f"原生日志最大真值跳变：索引 {jump_index}（从0计），即第 {jump_index+1} 次更新（从1计）。")
    table(["项", "本轮复算"], [["RMSE (cells)", f"{actual:.6f}"],
                               ["末次误差 (cells)", f"{distance[-1]:.6f}"],
                               ["更新数", len(distance)], ["平均更新耗时(s)", f"{np.mean(times):.6f}"]])
    fig, ax = plt.subplots(figsize=(11, 3.4))
    ax.plot(np.arange(1, len(distance)+1), distance)
    ax.axvline(jump_index+1, color="#dc2626", linestyle="--", label=f"原生第{jump_index+1}次更新的真值跳变")
    ax.set(xlabel="原生滤波更新编号（从1计）", ylabel="位置误差 (cells)", title="自建128格地图，仅一次新的原库推理")
    ax.legend()
    ax.grid(alpha=.25)
    fig.tight_layout()
    display(fig)
    plt.close(fig)
    erratum = read_json(package("adam-mcl") / "score-erratum.json")
    table(["历史10次结果更正", "正确统计"], [
        ["平均逐次 RMSE (cells)", f'{erratum["position_rmse_cells_mean"]:.6f}'],
        ["平均末次误差 (cells)", f'{erratum["final_error_cells_mean"]:.6f}'],
        ["满足持续全局/绑架收敛", f'{erratum["global_converged_trials"]}/10；{erratum["kidnap_converged_trials"]}/10'],
    ])


def launch(flow: str, *, enabled=False, record=False, auto=False, duration=90, trials=1):
    """Only an explicit per-cell enabled=True starts a fresh external experiment."""
    authors = {"dufomap", "beautymap", "ir-mcl", "adam-mcl"}
    scenes = {"mapping-static", "mapping-dynamic", "mapping-corridor", "localization-static",
              "localization-dynamic", "localization-large-change", "localization-degradation"}
    builds = {"build-static": "static", "build-dynamic": "dynamic", "build-corridor": "corridor"}
    if flow in authors:
        command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                   str(REPO / "demo" / "original.ps1"), "-Method", flow, "-RepoRoot", str(REPO),
                   "-Trials", str(trials)]
    elif flow in scenes:
        command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                   str(REPO / "demo" / "presentation.ps1"), "-Flow", flow, "-RepoRoot", str(REPO),
                   "-Duration", str(duration if auto else 0)]
        if auto:
            command.append("-Auto")
    elif flow in builds:
        command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                   str(REPO / "demo" / "build-maps.ps1"), "-Scene", builds[flow], "-RepoRoot", str(REPO)]
    elif flow == "stop":
        command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                   str(REPO / "demo" / "stop-presentation.ps1"), "-RepoRoot", str(REPO)]
    else:
        raise ValueError(flow)
    if record and flow not in builds and flow != "stop":
        command.append("-Record")
    print(subprocess.list2cmdline(command))
    if not enabled:
        display(Markdown("**现场启动单元尚未启用。** 需要现场演示时，把本单元 `START_THIS_EXPERIMENT` 改为 `True`，再单独运行；先结束上一场仿真。"))
        return
    if os.name != "nt" or not Path(command[5]).is_file():
        raise RuntimeError("现场入口需要本机 Windows 和原仓库；视频与复算可以离线使用。")
    log_dir = ROOT / "live-launch-logs"
    log_dir.mkdir(exist_ok=True)
    log = log_dir / f"{flow}.log"
    with log.open("ab") as stream:
        proc = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT,
                                creationflags=subprocess.CREATE_NO_WINDOW)
    print(f"启动进程 PID={proc.pid}；独立 Gazebo/RViz/终端会打开。启动日志：{log}")
    print("键盘焦点在专用终端：i/k 前后、j/l 转向、u/o 横移、空格停、q 正常结束。")
