"""Build and execute the repository notebook and a self-contained local presentation bundle.

Run in the dedicated notebook environment, not the ROS or author-model environments.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter
from nbformat.sign import NotebookNotary
from experiment_tools import PACKAGES

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
TITLE = "SLAM_实验逐步展示"
SCENES = (("static", "纯静态"), ("dynamic", "运动障碍物"), ("large-change", "持久结构变化"),
          ("corridor", "原走廊退化"), ("height-corridor", "高处几何·派生对照"))


def make_notebook():
    cells = []
    def md(text):
        cells.append(nbformat.v4.new_markdown_cell(text))
    def code(text):
        metadata = {"tags": ["manual-live-launch"]} if "RUN_LIVE = False" in text else {}
        cells.append(nbformat.v4.new_code_cell(text.strip(), metadata=metadata))
    md("""# 动态鲁棒定位与 SLAM · 代码展示

保存数据复核与视频展示；默认运行全部不启动仿真。二维使用XY RMSE，三维使用XYZ RMSE；单次理想仿真不构成稳定排名。

<a id="notebook-index"></a>

| 原有场景 | 2D · AMCL | 3D · GICP |
| --- | --- | --- |
""" + "\n".join(f"| {title} | [查看](#baseline-2d-{scene}) | [查看](#baseline-3d-{scene}) |" for scene, title in SCENES[:4]) + """

[四篇原库](#authors) · [逐条误差复算](#score-recompute) · [走廊持续恢复](#corridor-recovery) · [NDT／GICP早期静态试验](#early-3d) · [末尾：开放问题、假设与简单实验](#hypotheses)
""")
    code(r"""from pathlib import Path
import json, csv, hashlib, subprocess, os
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display, HTML, Image
from experiment_tools import local_url, videos, package, verify_files, table
from experiment_tools import baseline_scene, probe_scene, refinement_scene
ROOT = Path.cwd()
DATA = ROOT / 'evidence' if (ROOT / 'evidence').exists() else ROOT.parent.parent / 'results/reference'
ANALYSIS = ROOT / 'analysis/hypotheses' if (ROOT / 'evidence').exists() else ROOT.parent.parent / 'results/analysis/hypotheses'
REPO = Path(os.environ.get('SLAM_DEMO_REPO', r'D:\workspace\be2\slam_learning_updated'))
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
verify_files()""")
    md('<a id="authors"></a>\n\n## 1. 原库执行\n\n[↑ 返回目录](#notebook-index)')
    for method, name in [('dufomap','desktop-live-dufomap'),('beautymap','desktop-live-beautymap'),('ir-mcl','desktop-live-ir-mcl'),('adam-mcl','desktop-adam-mcl')]:
        code(f"""# {method}：查看本次执行记录、命令和视频
record = read(DATA / '{name}' / 'record.json')
print(json.dumps({{k:v for k,v in record.items() if k != 'artifacts'}}, ensure_ascii=False, indent=2)[:7000])
videos('{name}', result={method == 'adam-mcl'})""")
        code(f"""# 重新执行原库：需要时改为 True；Run All 默认只核对保存证据
RUN_LIVE = False
command = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
           str(REPO / 'demo' / '{'original.ps1' if method=='adam-mcl' else 'original-live.ps1'}'), '-Method', '{method}']
print(subprocess.list2cmdline(command))
if RUN_LIVE:
    subprocess.Popen(command)""")
    md("## 2. 地图清理计数复算")
    code("""for name in ('desktop-live-dufomap', 'desktop-live-beautymap'):
    metrics = read(DATA / name / 'metrics.json')
    counts = metrics['counts']
    sa = 100 * counts['kept_static'] / (counts['kept_static'] + counts['removed_static'])
    da = 100 * counts['removed_dynamic'] / (counts['kept_dynamic'] + counts['removed_dynamic'])
    print(name, 'SA', sa, 'DA', da, 'HA', 2*sa*da/(sa+da))
    print(counts, 'threshold_m=', metrics['threshold_m'])""")
    md("## 3. IR-MCL 原生轨迹复算")
    code("""folder = DATA / 'desktop-live-ir-mcl'
gt = np.loadtxt(folder / 'seq_1_gt_pose.txt')
est = np.loadtxt(folder / 'IRMCL.txt')
assert gt.shape == est.shape and np.allclose(gt[:, 0], est[:, 0])
window = gt[:, 0] >= gt[0, 0] + 20
gt, est = gt[window], est[window]
error_cm = np.linalg.norm(est[:, 1:3] - gt[:, 1:3], axis=1) * 100
def yaw(tum):
    x,y,z,w = tum[:,4:8].T
    return np.arctan2(2*(w*z+x*y), 1-2*(y*y+z*z))
delta = yaw(est) - yaw(gt)
error_deg = np.rad2deg(np.arctan2(np.sin(delta), np.cos(delta)))
print('N=', len(gt), 'RMSE cm=', np.sqrt(np.mean(error_cm**2)), 'yaw deg=', np.sqrt(np.mean(error_deg**2)))
print(read(folder / 'metrics.json'))
plt.figure(figsize=(10,3)); plt.plot(gt[:,0], error_cm); plt.ylabel('error cm'); plt.xlabel('sequence seconds'); plt.show()""")
    md("## 4. 机器人现场：建图 A → 固定地图 → 独立定位 B")
    code(r"""# 双击入口只启动本机实时场景；评分读取下方封存数据
SCRIPTS = Path(r'F:\be2演讲\实机脚本')
for path in sorted(SCRIPTS.glob('*.bat')):
    print(path.name)
RUN_LIVE = False
SCRIPT = SCRIPTS / '20-静态_三方法独立RViz实时.bat'
if RUN_LIVE:
    subprocess.Popen(['cmd.exe', '/c', str(SCRIPT)])""")
    for name in ('robot-supp-static','robot-supp-dynamic','robot-corridor-v2-mapping'):
        code(f"""# {name}：真实 Gazebo + RViz + 终端，及采集信息
videos('{name}', result=False)
print(read(DATA / '{name}' / 'runtime.json'))
print(read(DATA / '{name}' / 'metrics.json'))""")
    md("## 5. 二维：每种地图的现场执行与保存结果")
    for scene, title in SCENES[:4]:
        name = "robot-corridor-v2" if scene == "corridor" else "robot-live-" + scene
        md(f'<a id="baseline-2d-{scene}"></a>\n\n### {title} · 2D\n\n[↑ 返回目录](#notebook-index)')
        code(f"# 三列表格先于视频；从CSV复算XY，走廊使用受限观测组。\nbaseline_scene('{name}', '2d', prefix={'degraded_' if scene == 'corridor' else ''!r})")
    md('<a id="score-recompute"></a>\n\n## 6. 实测误差：逐条时间关联与 RMSE\n\n[↑ 返回目录](#notebook-index)')
    code("""# e_i = hypot(estimate_x-truth_x, estimate_y-truth_y)
# RMSE = sqrt(mean(e_i**2)); yaw = atan2(sin(delta),cos(delta))
# 包含初始化；不拟合坐标；匹配上限 0.05 仿真秒。
for name in ('robot-live-static','robot-live-dynamic','robot-live-large-change','robot-corridor-v2'):
    folder = DATA / name
    truth = [json.loads(line) for line in (folder/'truth.jsonl').read_text().splitlines()]
    stamps = np.array([row['stamp_s'] for row in truth])
    for path in sorted(folder.glob('*-samples.csv')):
        rows = list(csv.DictReader(path.open(encoding='utf-8')))
        arr = {key:np.array([float(row[key]) for row in rows]) for key in rows[0]}
        xy = np.hypot(arr['estimate_x']-arr['truth_x'], arr['estimate_y']-arr['truth_y'])
        angle = arr['estimate_yaw']-arr['truth_yaw']
        angle = np.arctan2(np.sin(angle), np.cos(angle))
        assert np.allclose(xy,arr['position_error_m'])
        assert np.allclose(angle,arr['yaw_error_rad'])
        for i,stamp in enumerate(arr['stamp_s']):
            near = int(np.argmin(abs(stamps-stamp)))
            assert abs(stamps[near]-stamp) <= .05 + 1e-9
            assert np.allclose(truth[near]['xyz'][:2], [arr['truth_x'][i],arr['truth_y'][i]])
        print(name, path.stem, 'N=',len(rows), 'RMSE cm=', np.sqrt(np.mean(xy**2))*100,
              'yaw deg=', np.rad2deg(np.sqrt(np.mean(angle**2))))""")
    md('<a id="corridor-recovery"></a>\n\n## 7. 新走廊：受限 → 恢复 → 持续确认\n\n[↑ 返回目录](#notebook-index)')
    code("""folder = DATA / 'robot-corridor-v2'
record = read(folder/'record.json')
print(json.dumps(record['restoration'], indent=2))
events = [json.loads(line) for line in (folder/'scan-stress.jsonl').read_text().splitlines()]
restore = min(row['stamp_s'] for row in events if row['phase']=='restored')
for path in sorted(folder.glob('degraded_*-samples.csv')):
    rows = list(csv.DictReader(path.open()))
    t=np.array([float(row['stamp_s']) for row in rows])
    e=np.array([float(row['position_error_m']) for row in rows])
    plt.plot(t,e*100,label=path.stem)
plt.axvline(restore,color='black',linestyle='--',label='full scan restored')
plt.xlabel('simulation seconds'); plt.ylabel('error cm'); plt.legend(); plt.show()""")
    md('<a id="early-3d"></a>\n\n## 8. 早期三维固定地图定位：NDT / GICP\n\n[↑ 返回目录](#notebook-index)')
    code('''for name in ("robot-ndt-static", "robot-gicp-static"):
    videos(name)
    folder = DATA / name
    print(read(folder / "cases.json"))
    print(read(folder / "metrics.json")["cases"])
    for path in folder.glob("*-samples.csv"):
        rows = list(csv.DictReader(path.open()))
        error = np.array([np.hypot(float(r["estimate_x"])-float(r["truth_x"]),
                                    float(r["estimate_y"])-float(r["truth_y"])) for r in rows])
        print(name, len(error), np.sqrt(np.mean(error**2))*100, "cm")
# 同参数两轮都保留；差异原因待查，不挑选好看的结果。
print("NDT initial trial:", read(DATA / "robot-ndt-static-initial" / "metrics.json")["cases"])
print("NDT latest trial:", read(DATA / "robot-ndt-static" / "metrics.json")["cases"])''')
    md("## 9. 三维：Raw／DUFOMap／BeautyMap共用GICP\n\n三维输入不是完整三维SLAM：地图A使用给定位姿，定位B使用独立观测。")
    for scene, title in SCENES[:4]:
        md(f'<a id="baseline-3d-{scene}"></a>\n\n### {title} · 3D\n\n[↑ 返回目录](#notebook-index)')
        code(f"# 同一三维GICP，只改变地图；从完整位姿CSV复算XYZ。\nbaseline_scene('robot-3d-{scene}', '3d')")
    append_hypotheses(md, code)
    nb=nbformat.v4.new_notebook(cells=cells)
    nb.metadata['kernelspec']={'display_name':'SLAM 展示 (Python 3.10)','language':'python','name':'slam-presentation'}
    return nb


def append_hypotheses(md, code):
    md("""<a id="hypotheses"></a>

## 10. 从开放问题提出假设，再做简单实验

[↑ 返回总目录](#notebook-index)

- **H1 Guard**：稳健残差、较小对应门槛、弱方向抑制和里程计正则，检验能否减轻错误匹配。组合实验不能分辨单个组件的贡献。
- **H2 Depth**：真实4m深度相机提供二维切片以外的高度线索；若仍是平行墙，更多点不保证更多定位信息。
- **H3 Search**：有界多位置候选搜索，分数差和连续两次运动一致后接受；接受候选不等于已恢复。

二维定位B移除三维雷达，使用二维雷达＋320×240、水平80°、0.25–4m深度相机；三维组使用16线雷达＋同一相机。五原型同帧同数组；原生AMCL／GICP是同源参照。A给定位姿建图且保留三维雷达参照，B不读取真值，地图冻结。原型估计x/y/yaw，使用A标定高度，roll/pitch固定；不是完整六自由度SLAM，也未验证仅廉价传感器自主建图。

前三场景90仿真秒，走廊120秒；准备期及录屏起始后50仿真秒限制雷达，随后恢复。恢复标准为XY<0.1m、|yaw|<5°连续5s且至少8次更新。没有真实搬动机器人，不是任意全局绑架恢复。

<a id="hypothesis-index"></a>

| 场景 | 2D＋深度 | 3D＋深度 |
| --- | --- | --- |
""" + "\n".join(f"| {title} | [查看](#hypothesis-2d-{scene}) | [查看](#hypothesis-3d-{scene}) |" for scene, title in SCENES) + """

[同输入粗到细补充实验](#refinement-index) · [输入与高度复核](#input-audit) · [有效／无效与原因](#hypothesis-findings)
""")
    code("""# 正式重测前冻结协议；首轮z=0错误不再作为主结果。
protocol = read(ANALYSIS / 'calibrated-protocol.json')
print('协议冻结UTC:', protocol['frozen_at_utc'])
print('搜索:', protocol['parameters']['search_translation_radius_m'], 'm /',
      protocol['parameters']['search_yaw_radius_deg'], 'deg')
table(['地图A', '车体高度(m)', '定位B真值用于标定'],
      [[scene, f"{prior['ground_z_m']:.8f}", prior['localization_B_truth_used']]
       for scene, prior in protocol['mapping_A_height_priors'].items()])
print('给定位姿的A用于高度基准，B真值只用于评分；不是实机精度或稳定排名结论。')""")
    for dimension in ("2d", "3d"):
        md(f"### {dimension.upper()} · 假设实验实录")
        for scene, title in SCENES:
            note = "\n\n此场景额外加入两块高处几何，是单独的结构互补可行性对照，不能冒充原走廊结果。" if scene == "height-corridor" else ""
            md(f'<a id="hypothesis-{dimension}-{scene}"></a>\n\n#### {title} · {dimension.upper()}\n\n[↑ 返回假设实验目录](#hypothesis-index)' + note)
            code(f"# 从保存CSV复算{'XY' if dimension == '2d' else 'XYZ'}；三列表格先于真实窗口视频。\nprobe_scene('{dimension}', '{scene}')")
    md("""<a id="refinement-index"></a>

### 补充假设：候选细化与恢复确认

首轮高处对照出现约20cm平台偏差，假设0.4m粗网格在弱方向不能继续修正。补充试验使用0.1m局部网格，并将更多已检查的不同位置纳入分数差检验。H1／H2、分数≥0.65、分数差≥0.025与连续两次确认规则保持一致。这是“网格细化＋候选检查”的组合，不是单因素消融。

以下四组使用上方各自封存B的相同雷达／深度／里程计数组重新推理，视频是结果回放。当前Notebook单元仅复核已有结果，不重新推理。

| 场景 | 2D重算 | 3D重算 |
| --- | --- | --- |
| 原走廊 | [查看](#refinement-2d-corridor) | [查看](#refinement-3d-corridor) |
| 高处对照 | [查看](#refinement-2d-height-corridor) | [查看](#refinement-3d-height-corridor) |
""")
    for dimension in ("2d", "3d"):
        for scene, title in SCENES[3:]:
            md(f'<a id="refinement-{dimension}-{scene}"></a>\n\n#### {dimension.upper()} · {title} · 同输入细化\n\n[↑ 返回补充目录](#refinement-index)')
            code(f"refinement_scene('{dimension}', '{scene}')")
    md('<a id="input-audit"></a>\n\n### 同输入、A高度与误差来源复核\n\n[↑ 返回假设实验目录](#hypothesis-index)')
    code("""# 此处是事后证据审计，不向定位器提供真值。
audit_rows = []
for dimension in ('2d', '3d'):
    for scene in ('static', 'dynamic', 'large-change', 'corridor', 'height-corridor'):
        folder = DATA / f'probe-calibrated-{dimension}-{scene}'
        config = read(folder / 'probe-config.json')
        frames = read(folder / 'probe-B-inputs.json')['frames']
        updates = [json.loads(line) for line in (folder / 'probe-updates.jsonl').read_text(encoding='utf-8').splitlines()]
        grouped = {}
        for row in updates:
            grouped.setdefault(row['frame'], []).append(row)
        with np.load(folder / 'probe-B-inputs.npz', allow_pickle=False) as arrays:
            for frame in frames:
                key = f"frame_{frame['frame']:05d}"
                fingerprint = hashlib.sha256(b''.join(arrays[key + suffix].tobytes()
                            for suffix in ('_lidar', '_depth', '_odom'))).hexdigest()
                group = grouped[frame['frame']]
                assert len(group) == 5
                assert {r['case'] for r in group} == {'plain','guard','depth','search','recover'}
                assert all(r['input_sha256'] == fingerprint for r in group)
        with np.load(folder / 'height-prior-inputs.npz', allow_pickle=False) as calibration:
            world_body = calibration['provided_sensor_poses'] @ calibration['body_from_sensor']
            height = float(np.median(world_body[:, 2, 3]))
        assert np.isclose(height, config['ground_z_m'], atol=1e-10, rtol=0)
        assert config['truth_input_to_localizers'] is False
        audit_rows.append([f'{dimension}/{scene}', len(frames), f'{height:.8f}'])
table(['组', '五原型完全同帧数', 'A重建车体高度(m)'], audit_rows)
print('三维约9.4cm旧固定偏差来自原型z=0设置，不能归因于此前论文清理器。')""")
    md("""<a id="hypothesis-findings"></a>

### 本轮支持什么，哪些仍然无效

- **H1**：持久变化的二维Plain→Guard为7.98→0.49cm，三维为3.69→0.24cm；静态没有收益。三维高处走廊Guard为100.36cm，反而差于Plain的46.60cm：保护跟踪不能代替重定位。
- **H2＋细化**：二维高处对照持续收敛从首次输出后55.9s提前到3.3s，完整XY RMSE由21.15降到16.20cm，仍包含起始约1m偏差。没有高处线索的原走廊未改善。
- **H3**：原走廊完整视野恢复后，雷达搜索的二维／三维持续收敛延迟为5.8／6.2s。高分与连续一致仍可能有偏：二维粗搜索曾确认20.2cm偏差，同一时刻细化候选误差0.43cm。
- **三维负结果**：高处组细化没有提前恢复；深度细化XYZ为50.79→47.71cm，恢复后延迟12.8→8.7s。受限段19次细化搜索仅2次通过几何门槛，其后一次均无有效深度，连续确认重置。

原走廊受限时深度仍主要看见平行墙；高度、局部可观测性与全局位置唯一是不同问题。三维高处组受限期仅45个处理帧，二维为157帧，搜索处理也更慢，不能把跨维度差异全部解释为传感器优劣。两个三维走廊的原生GICP分别在75.6／75.1s后停止有效输出，RMSE只覆盖已有输出。

下一步尚未实验的方向：按弱方向分配传感器权重、跨帧累积多候选证据、慢搜索与持续跟踪解耦、主动观察端墙或拐角。地图分层更新、真实噪声、实机、多次独立重复仍需分别测试。[完整原因与首轮诊断档案](https://github.com/p20030920p/slam_learning_updated/blob/main/docs/testing/HYPOTHESES.zh-CN.md#hypothesis-findings)。
""")
    code("""# 误差曲线由保存输出与独立真值计算；没有对缺失输出补点。
summary = read(ANALYSIS / 'calibrated-summary.json')
for dimension in ('2d', '3d'):
    plot = ANALYSIS / f'calibrated-{dimension}-height-corridor-errors.png'
    row = next(r for r in summary['conditions'] if r['dimension'] == dimension and r['scene'] == 'height-corridor')
    assert hashlib.sha256(plot.read_bytes()).hexdigest() == row['plot_sha256']
    display(Image(filename=str(plot)))""")
    code("""# 现场入口：仅手动启用本格才启动新场景；39查看，50十组，51–55同输入细化。
RUN_LIVE = False
RUN_REFINEMENT = False
live_command = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                str(REPO / 'demo/record-probes.ps1'), '-Dimension', '2D', '-Scene', 'height-corridor']
refine_command = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                  str(REPO / 'demo/refine-probes.ps1'), '-All']
print('新计算和实录:', subprocess.list2cmdline(live_command))
print('封存输入重新推理，结果回放:', subprocess.list2cmdline(refine_command))
if RUN_LIVE:
    subprocess.Popen(live_command)
if RUN_REFINEMENT:
    subprocess.Popen(refine_command)""")


def execute_at(directory: Path):
    nb = make_notebook()
    client = NotebookClient(nb, timeout=180, kernel_name="slam-presentation",
                            resources={"metadata": {"path": str(directory)}})
    client.execute()
    path = directory / f"{TITLE}.ipynb"
    nbformat.write(nb, path)
    NotebookNotary().sign(nb)
    body, _ = HTMLExporter(template_name="lab").from_notebook_node(nb)
    offline_prefix = "" if (directory / "evidence").is_dir() else "../../"
    body = body.replace('src="/files/', f'src="{offline_prefix}').replace(
        'href="/files/', f'href="{offline_prefix}')
    # nbconvert's static HTML may use this relative URL for CDN MathJax; the notebook
    # supplies plain-text formulas too. Videos and plots never need a network URL.
    (directory / f"{TITLE}.html").write_text(body, encoding="utf-8")
    code_cells = [c for c in nb.cells if c.cell_type == "code"]
    assert all(c.execution_count is not None for c in code_cells)
    assert not any(o.output_type == "error" for c in code_cells for o in c.outputs)
    print(f"Executed {len(code_cells)} code cells / {len(nb.cells)} total: {path}", flush=True)
    return path


def prepare_bundle(destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    for filename in ["experiment_tools.py", "verify_bundle.py", "requirements.txt", "README.md"]:
        shutil.copy2(HERE / filename, destination / ("使用说明.md" if filename == "README.md" else filename))
    for name in PACKAGES:
        shutil.copytree(REPO / "results" / "reference" / name, destination / "evidence" / name,
                        dirs_exist_ok=True)
    shutil.copytree(REPO / "results/analysis/hypotheses", destination / "analysis/hypotheses", dirs_exist_ok=True)
    erratum_dir = destination / "evidence" / "adam-mcl"
    erratum_dir.mkdir(exist_ok=True)
    for filename in ["ERRATUM.md", "score-erratum.json"]:
        shutil.copy2(REPO / "results" / "reference" / "adam-mcl" / filename, erratum_dir / filename)
    python = str(Path(sys.executable).resolve())
    ps = f'''$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$python='{python.replace(chr(39), chr(39)*2)}'
if (-not (Test-Path -LiteralPath $python)) {{throw 'Prepared Notebook Python environment is missing.'}}
Set-Location -LiteralPath $root
$env:PYTHONUTF8='1'
$env:SLAM_DEMO_REPO='{str(REPO).replace(chr(39), chr(39)*2)}'
& $python -m jupyterlab --ip=127.0.0.1 --notebook-dir="$root" --ServerApp.default_url='/lab/tree/{TITLE}.ipynb'
exit $LASTEXITCODE
'''
    (destination / "打开Notebook.ps1").write_text(ps, encoding="utf-8-sig")
    bat = '@echo off\nchcp 65001 >nul\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0打开Notebook.ps1"\npause\n'
    (destination / "一键打开Notebook.bat").write_bytes(bat.replace("\n", "\r\n").encode("utf-8"))
    preview = f'@echo off\nchcp 65001 >nul\nstart "" "%~dp0{TITLE}.html"\n'
    (destination / "一键打开离线展示.bat").write_bytes(preview.replace("\n", "\r\n").encode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=Path(r"F:\be2演讲\展示"))
    args = parser.parse_args()
    kernel_prefix = REPO / ".cache" / "presentation-notebook"
    subprocess.run([sys.executable, "-m", "ipykernel", "install", "--prefix", str(kernel_prefix),
                    "--name", "slam-presentation", "--display-name", "SLAM 展示 (Python 3.10)"], check=True)
    prepare_bundle(args.destination)
    execute_at(HERE)
    execute_at(args.destination)
    portable = {}
    for folder in ("evidence", "analysis"):
        for path in sorted((args.destination / folder).rglob("*")):
            if path.is_file():
                portable[path.relative_to(args.destination).as_posix()] = {
                    "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    (args.destination / "bundle-manifest.json").write_text(
        json.dumps({"source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO,
                                                            text=True).strip(),
                    "source_working_tree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip()),
                    "notebook_generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    "scope": "frozen evidence copies; not live-run raw bags", "files": portable},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Bundle ready: {len(portable)} evidence files", flush=True)


if __name__ == "__main__":
    main()
