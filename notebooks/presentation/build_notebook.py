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

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
TITLE = "SLAM_实验逐步展示"
PACKAGES = (
    "robot-supp-static", "robot-supp-dynamic", "robot-supp-large-change", "robot-corridor-v2-mapping",
    "robot-live-static", "robot-live-dynamic", "robot-live-large-change", "robot-corridor-v2",
    "desktop-live-dufomap", "desktop-live-beautymap", "desktop-live-ir-mcl", "desktop-adam-mcl",
    "robot-ndt-static", "robot-gicp-static", "robot-ndt-static-initial",
)


def make_notebook():
    cells = []
    def md(text):
        cells.append(nbformat.v4.new_markdown_cell(text))
    def code(text):
        cells.append(nbformat.v4.new_code_cell(text.strip()))
    md("# 动态鲁棒定位与 SLAM · 代码展示")
    code(r"""from pathlib import Path
import json, csv, hashlib, subprocess, os
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display, HTML, Image
from experiment_tools import local_url, videos, package, verify_files
ROOT = Path.cwd()
DATA = ROOT / 'evidence' if (ROOT / 'evidence').exists() else ROOT.parent.parent / 'results/reference'
REPO = Path(os.environ.get('SLAM_DEMO_REPO', r'D:\workspace\be2\slam_learning_updated'))
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
verify_files()""")
    md("## 1. 原库执行")
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
    md("## 5. 每种地图的现场执行与保存结果")
    code("""def show_video(path, title):
    display(HTML(f'<b>{title}</b><video controls preload="none" width="900" src="{local_url(path)}"></video>'))
for name in ('robot-live-static','robot-live-dynamic','robot-live-large-change','robot-corridor-v2'):
    folder = DATA / name
    record = read(folder / 'record.json')
    print(name, record['source_run'])
    for view in record['native_views']:
        case = view['case']
        show_video(folder / view['video'], f'{name} / {case} / Live execution')
        show_video(folder / 'methods' / case / 'result.mp4', f'{name} / {case} / Measured result replay')""")
    md("## 6. 实测误差：逐条时间关联与 RMSE")
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
    md("## 7. 新走廊：受限 → 恢复 → 持续确认")
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
    md("## 8. 三维固定地图定位：NDT / GICP")
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
    nb=nbformat.v4.new_notebook(cells=cells)
    nb.metadata['kernelspec']={'display_name':'SLAM 展示 (Python 3.10)','language':'python','name':'slam-presentation'}
    return nb


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
    for filename in ["experiment_tools.py", "requirements.txt", "README.md"]:
        shutil.copy2(HERE / filename, destination / ("使用说明.md" if filename == "README.md" else filename))
    for name in PACKAGES:
        shutil.copytree(REPO / "results" / "reference" / name, destination / "evidence" / name,
                        dirs_exist_ok=True)
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
    for path in sorted((args.destination / "evidence").rglob("*")):
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
