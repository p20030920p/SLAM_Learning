"""Build a small navigable gallery from verified hypothesis run records."""
import argparse
import html
import json
import os
from pathlib import Path
from urllib.parse import quote

NAMES = {"static": "纯静态", "dynamic": "运动障碍物", "large-change": "持久结构变化",
         "corridor": "原走廊退化", "height-corridor": "高处标志走廊（派生对照）"}
METHODS = {"plain": "Plain ICP", "guard": "H1 · Guard", "depth": "H2 · Guard + Depth",
           "search": "H3 · LiDAR Search", "recover": "H3 · Depth + Search", "native": "原生定位器"}


def rmse(record, case):
    if record["hypothesis_probes"]["dimension"] == "3d":
        return record["metrics_3d"][case]["xyz_rmse_m"] * 100
    return record["metrics"]["cases"][case]["position_rmse_m"] * 100


def effect(record, case):
    dimension = record["hypothesis_probes"]["dimension"]
    result = f"{'XYZ' if dimension == '3d' else 'XY'} RMSE {rmse(record, case):.2f} cm"
    parent = {"guard": "plain", "depth": "guard", "search": "guard", "recover": "depth"}.get(case)
    if parent:
        difference = rmse(record, case) - rmse(record, parent)
        reference = {"plain": "Plain", "guard": "Guard", "depth": "Depth"}[parent]
        result += f"；接近{reference}" if abs(difference) < .01 else f"；较{reference}{'低' if difference < 0 else '高'}{abs(difference):.2f} cm"
    recovery = record.get("restoration", {}).get(case)
    if recovery:
        if recovery["converged"]:
            result += f"；恢复后{recovery['sustained_convergence_delay_s']:.1f} s持续收敛"
        elif recovery["converged"] is None:
            result += "；恢复后样本不足"
        else:
            result += "；未持续收敛"
    return result


def collect(root):
    selected = {}
    for path in root.rglob("record.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if not record.get("hypothesis_probes"):
            continue
        runtime = json.loads((path.parent / "runtime.json").read_text(encoding="utf-8"))
        key = (record["hypothesis_probes"]["dimension"], runtime["scene"])
        run_id = record["source_run"].replace("\\", "/").rsplit("/", 1)[-1]
        previous_id = selected[key][1]["source_run"].replace("\\", "/").rsplit("/", 1)[-1] if key in selected else ""
        if key not in selected or run_id > previous_id:
            selected[key] = (path, record)
    calibrated = {key: value for key, value in selected.items() if "ground_z_m" in value[1]["hypothesis_probes"]}
    return calibrated or selected


def render(records, output, supplements=None, mappings=None):
    def url(path):
        return quote(os.path.relpath(path, output.parent).replace("\\", "/"), safe="/.-_")
    nav = []
    for scene, title in NAMES.items():
        columns = [f'<a href="#{dimension}-{scene}">查看实验</a>' if (dimension, scene) in records else "待录制" for dimension in ("2d", "3d")]
        nav.append(f"<tr><td>{title}</td><td>{columns[0]}</td><td>{columns[1]}</td></tr>")
    if supplements:
        for scene in ("corridor", "height-corridor"):
            columns = [f'<a href="#refinement-{dimension}-{scene}">查看重算</a>' for dimension in ("2d", "3d")]
            nav.append(f"<tr><td>{NAMES[scene]} · 搜索细化</td><td>{columns[0]}</td><td>{columns[1]}</td></tr>")
    chunks = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>开放问题：假设与简单实验</title><style>body{max-width:1100px;margin:30px auto;padding:0 20px;font-family:system-ui;color:#223d59;background:#f6f9fc}a{color:#1b63aa}h1,h2,h3{color:#234966}section{background:white;padding:20px;margin:24px 0;border:1px solid #cadbea;border-radius:14px}table{border-collapse:collapse;width:100%;margin:16px 0}th,td{border:1px solid #cadbea;padding:9px;text-align:left;line-height:1.6}th{background:#eaf2fa}p{line-height:1.7}video{width:100%;max-height:700px}.scroll{overflow-x:auto}</style><h1>开放问题：假设与简单实验</h1><p>H1：异常残差剔除与弱约束方向的里程计保底。H2：深度相机补充雷达切片以外的几何。H3：在初始信念附近搜索多个位置，匹配充分且连续两次一致后重定位。</p><p>2D定位B没有三维雷达，使用二维雷达＋真实渲染的4m深度相机；3D组使用16线雷达＋同一深度相机。五个自写原型共用完全相同的已配对扫描及轮式里程计；原生AMCL／GICP独立消费同源输入。三维原型估计地面机器人的x/y/yaw，z/roll/pitch固定，不是完整六自由度SLAM。建图A给定位姿，并采集三维雷达参照用于高度审计；定位B不读取真值，地图冻结。尚未测试仅廉价传感器的自主建图。理想仿真单轮结果，无硬件效果或稳定排名结论。</p><nav id="index"><h2>实验目录</h2><div class="scroll"><table><tr><th>场景</th><th>2D＋深度</th><th>3D＋深度</th></tr>' + "".join(nav) + '</table></div></nav>']
    if supplements:
        chunks.append('<p><a href="#refinement">同输入搜索细化</a></p>')
    if mappings:
        chunks.append('<p><a href="#mapping-a">建图A输入检查</a></p>')
    diagnostic_page = output.parent / "hypotheses-diagnostics.html"
    if diagnostic_page.is_file() and output != diagnostic_page:
        chunks.append('<p><a href="hypotheses-diagnostics.html">首轮原型与失败排查档案（已知高度设置错误）</a></p>')
    for dimension in ("2d", "3d"):
        chunks.append(f"<h2>{dimension.upper()} 雷达实验</h2>")
        for scene, title in NAMES.items():
            if (dimension, scene) not in records:
                continue
            path, record = records[dimension, scene]
            chunks.append(f'<section id="{dimension}-{scene}"><h3>{title}</h3><p><a href="#index">↑ 返回目录</a></p><div class="scroll"><table><tr><th>方法</th><th>地图／观测</th><th>指标效果</th></tr>')
            for case, label in METHODS.items():
                if case == "native":
                    label = "原生 " + ("AMCL" if dimension == "2d" else "GICP")
                base_map = "二维雷达点图" if dimension == "2d" else "三维雷达点图"
                map_type = base_map + "＋深度点图" if case in ("depth", "recover") else base_map
                if case == "native" and dimension == "2d":
                    map_type = "同源二维栅格投影图"
                chunks.append(f"<tr><td>{label}</td><td>{map_type}</td><td>{html.escape(effect(record, case))}</td></tr>")
            frames = json.loads((path.parent / "probe-B-inputs.json").read_text())["frames"]
            used = sum(frame["depth_points"] >= 12 for frame in frames)
            samples = record["metrics"]["cases"]["native"]["samples"]
            chunks.append(f'</table></div><p>五原型各{len(frames)}帧；有效深度{used}/{len(frames)}帧；原生定位器{samples}次输出。高处标志场景加入了两块高处几何，只用于检验额外高度结构的可行性。</p>' if scene == "height-corridor" else f'</table></div><p>五原型各{len(frames)}帧；有效深度{used}/{len(frames)}帧；原生定位器{samples}次输出。</p>')
            chunks.append(f'<video controls preload="none" poster="{url(path.parent / "frame-mid.png")}" src="{url(path.parent / "execution.mp4")}"></video><p><a href="{url(path)}">可重算记录</a> · <a href="{url(path.parent / "probe-config.json")}">冻结参数</a></p></section>')
    if supplements:
        chunks.append('<h2 id="refinement">补充：同输入粗到细搜索</h2><p>从同一已录B包重新计算，比较0.4m粗网格与0.1m细化及更完整的候选检查。以下视频是保存输出的结果回放，不是新增Gazebo实录。</p>')
        for path, record in sorted(supplements, key=lambda item: (item[1]["dimension"], item[1]["scene"])):
            dimension, scene = record["dimension"], record["scene"]
            chunks.append(f'<section id="refinement-{dimension}-{scene}"><h3>{dimension.upper()} · {NAMES[scene]}</h3><p><a href="#index">↑ 返回目录</a></p><table><tr><th>方法</th><th>地图／观测</th><th>指标效果</th></tr>')
            for name, label in (("coarse_lidar", "粗搜索·雷达"), ("coarse_depth", "粗搜索·雷达＋深度"), ("fine_lidar", "细化·雷达"), ("fine_depth", "细化·雷达＋深度")):
                value = record["metrics_3d"][name]["xyz_rmse_m"] if dimension == "3d" else record["metrics"][name]["position_rmse_m"]
                delay = record["initial_sustained_delay_s"][name]
                timing = f"首次输出后{delay:.1f}s持续收敛" if delay is not None else "未持续收敛"
                chunks.append(f'<tr><td>{label}</td><td>{"雷达＋深度点图" if "depth" in name else "雷达点图"}</td><td>{"XYZ" if dimension == "3d" else "XY"} RMSE {value*100:.2f} cm；{timing}</td></tr>')
            chunks.append(f'</table><video controls preload="none" poster="{url(path.parent / "frame-mid.png")}" src="{url(path.parent / "result.mp4")}"></video><p><a href="{url(path)}">同输入记录</a></p></section>')
    if mappings:
        chunks.append('<h2 id="mapping-a">独立建图A：传感器输入与位姿检查</h2><ul>')
        for path, record in mappings:
            runtime = json.loads((path.parent / "runtime.json").read_text())
            chunks.append(f'<li>{NAMES[runtime["scene"]]}：<a href="{url(path.parent / "execution.mp4")}">输入录像</a> · <a href="{url(path)}">输入档案与给定位姿审计</a></li>')
        chunks.append('</ul>')
    chunks.append("</html>")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(chunks), encoding="utf-8")


def render_diagnostics(root, output, primary):
    records, refinements = {}, []
    for path in root.rglob("record.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("hypothesis_probes") and "ground_z_m" not in record["hypothesis_probes"]:
            scene = json.loads((path.parent / "runtime.json").read_text())["scene"]
            records[record["hypothesis_probes"]["dimension"], scene] = path, record
        elif record.get("kind") == "offline_hypothesis_refinement" and "calibrated-" not in record.get("protocol_repository_path", ""):
            refinements.append((path, record))
    render(records, output, refinements)
    text = output.read_text(encoding="utf-8")
    text = text.replace('<h1>开放问题：假设与简单实验</h1>',
                        '<h1>诊断档案：首轮原型与细化负结果</h1><p><strong>本页首轮原型固定z=0，存在已知约9.4cm参考高度错误，不能与校准版拼成XYZ排名。完整重测使用独立建图A标定高度；首轮数据和无效结果保留于此。</strong></p>'
                        f'<p><a href="{html.escape(primary)}">返回校准后的主实验</a></p>')
    output.write_text(text, encoding="utf-8")


def extras(root):
    refinements, mappings = {}, []
    for path in root.rglob("record.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("kind") == "offline_hypothesis_refinement" and "calibrated-refinement-protocol.json" in record.get("protocol_repository_path", ""):
            key = record["dimension"], record["scene"]
            if key not in refinements or path.parent.name > refinements[key][0].parent.name:
                refinements[key] = path, record
        elif record.get("probe_mapping_A"):
            mappings.append((path, record))
    return list(refinements.values()), mappings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    records = collect(args.root)
    refinements, mappings = extras(args.root)
    render(records, args.output, refinements, mappings)
    print(f"Gallery: {args.output}; {len(records)} completed scene/dimension pairs")


if __name__ == "__main__":
    main()
