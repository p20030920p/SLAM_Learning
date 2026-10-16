"""Update only H1 and shared pseudocode; preserve the user's H2 cells."""
import base64
import hashlib
import json
from pathlib import Path
import shutil
import sys

import nbformat
from nbclient import NotebookClient
from nbformat.sign import NotebookNotary

from hypothesis_notation import math_sections, pseudocode, raw_baselines
ROOT = Path(__file__).resolve().parents[3]
SUITE = ROOT / "results/reference/h1-refined-20261016"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

NAME = "新假设_H1-H2_数学原理与可视化.ipynb"
destination = Path("F:/be2演讲/ipynb") / NAME
notebook = nbformat.read(destination, as_version=4)
assert len(notebook.cells) == 9
preserved_h2 = {i: notebook.cells[i].copy() for i in (5, 6, 7)}
backup = ROOT / ".cache/h1-notebook-before"
backup.mkdir(exist_ok=True)
if not (backup / NAME).exists():
    shutil.copyfile(destination, backup / NAME)
notebook.cells[0].source = "# 新的 Hypothesis：数学原理与可视化\n\n[H1 自写对齐与清理](#h1) · [H2 运动补偿](#h2)\n\n代码默认折叠，图已执行保存；两张图是构造的原理示意，H1动态B结果汇总三次新采集。\n\n" + math_sections(True)["common"] + "\n\n### Raw基线说明\n\n" + raw_baselines(True)
notebook.cells[2].source = '<a id="h1"></a>\n## H1｜自写对齐与动态清理\n\n' + math_sections(True)["h1"]
notebook.cells[3].source = r'''# 构造示意：用纯平移特例展示加权对齐，完整实现还估计旋转
wall = np.column_stack([np.full(90, 5.), np.linspace(-1.8, 1.8, 90)])
ghost = np.array([[2.2, -.18], [2.2, .18], [2.4, -.18], [2.4, .18]])
rare = np.array([[4., 1.3], [4., 1.5]])
offset = np.array([.08, 0.])
raw_wall = wall + offset
# 对应只取静态历史支持，动态点不参与本示意的位姿增量
residual = np.linalg.norm(raw_wall-wall, axis=1)
weights = np.minimum(1., .05/np.maximum(residual, 1e-9))
ids = np.argsort(residual)[:int(.7*len(residual))]
delta = ((wall[ids]-raw_wall[ids])*weights[ids,None]).sum(axis=0)/weights[ids].sum()
np.testing.assert_allclose(delta, -offset, atol=1e-12)
support = np.array([8, 3, 1])
free = np.array([2, 8, 0])
keep = (free < 3) | (free < 1.5*support)
assert keep.tolist() == [True, False, True]
groups, names, colors = [wall, ghost, rare], ['墙面', '动态残影', '稀疏静态'], [BLUE, ORANGE, PURPLE]
fig, axes = plt.subplots(1, 3, figsize=(14.8, 4.5), layout='constrained')
for stage, ax in enumerate(axes):
    for points, name, color, retained in zip(groups,names,colors,keep):
        if stage == 2 and not retained: continue
        values = points+offset if stage == 0 else points+offset+delta
        ax.scatter(*values.T, color=color, s=24, label=name, zorder=3)
    ax.plot(wall[:,0],wall[:,1],'--',color=GREY,lw=1.5,label='前序支持')
    ax.set(xlim=(1.6,5.65),ylim=(-2.15,2.15),xlabel='x / m',ylabel='y / m',
           title=['① 轮速累积：存在位姿偏差','② 加权对齐：校正 8 cm 平移','③ 时序清理：保墙面与稀疏静态'][stage])
    tidy(ax)
axes[0].legend(loc='upper left',fontsize=9)
axes[2].text(1.75,-1.85,'近邻支持 s / 空闲 f\n墙面 8/2：保留\n残影 3/8：删除\n稀疏静态 1/0：保留',fontsize=10)
fig.suptitle('H1 数学原理示意：先控制对齐偏差，再依据时序证据清理',fontsize=15)
plt.show(); plt.close(fig)
'''
quality = read(SUITE / "dynamic-A/record.json")["methods"]
score = read(SUITE / "confirmation-score.json")
def table(headers, rows):
    return "\n".join(["| "+" | ".join(headers)+" |", "| "+" | ".join(["---"]*len(headers))+" |",
                       *["| "+" | ".join(row)+" |" for row in rows]])
controls = [("raw", "M₀ · Raw：轮速位姿累积"), ("temporal", "M₁ · 自写对齐＋时序清理")]
a_rows = [[name, f"{quality[key]['dynamic_removal']*100:.2f}%", f"{quality[key]['static_retention']*100:.2f}%"] for key,name in controls]
b_rows = [[name, f"{score['methods'][key]['common']['rmse_m']*100:.2f}"] for key,name in controls]
conclusion = "本批次满足清图条件，且三次新B汇总定位误差下降；不能外推为所有场景的保证。" if score["H1_conditions_met_this_batch"] else "清图条件已满足，但三次新B未确认定位改善；H1的定位预测仍不成立。"
notebook.cells[4].source = "**实际验证：同一原始A重建，另采动态B三次。**\n\n**A · 清图比例**\n\n" + table(["方法","DA ↑","SA ↑"],a_rows) + "\n\n**B · 冻结地图后定位：合并三轮共同有效样本。**\n\n" + table(["地图／相同AMCL","XY RMSE / cm ↓"],b_rows) + "\n\n" + conclusion + "\n\n旧逐格过滤5.72→6.11 cm的负结果保留。开发消融区分只清理、只对齐与联合方法；最终B未用于调参。\n\n[逐轮数值与录像](https://github.com/p20030920p/SLAM_Learning/blob/main/docs/HOME.zh-CN.md#own-dynamic-b)"
notebook.cells[8].source = "### 实验伪代码\n\n```text\n" + pseudocode() + "```"
notebook.metadata["H1_algorithm_sources"] = read(SUITE / "confirmation-protocol.json")["algorithm_sources"]
notebook.metadata["H1_metric_sources_sha256"] = {p.relative_to(ROOT).as_posix(): sha(p) for p in (SUITE/"dynamic-A/record.json", SUITE/"confirmation-score.json")}
client = NotebookClient(notebook, timeout=90, kernel_name="python3", resources={"metadata":{"path":str(destination.parent)}})
with client.setup_kernel():
    client.execute_cell(notebook.cells[1], 1, execution_count=1)
    client.execute_cell(notebook.cells[3], 3, execution_count=2)
for index, before in preserved_h2.items():
    assert notebook.cells[index] == before
nbformat.validate(notebook)
assert not any(output.output_type == "error" for cell in notebook.cells if cell.cell_type == "code" for output in cell.outputs)
review = ROOT / ".cache/h1-refined-notebook-review"
review.mkdir(exist_ok=True)
for output in notebook.cells[3].outputs:
    if "image/png" in output.get("data", {}):
        (review / "H1.png").write_bytes(base64.b64decode(output.data["image/png"]))
nbformat.write(notebook, destination)
destination.write_bytes(destination.read_bytes().replace(b"\r\n", b"\n"))
NotebookNotary().sign(notebook)
shutil.copyfile(destination, ROOT / "notebooks/presentation" / NAME)
print(json.dumps({"notebook":str(destination),"H1_updated":True,"H2_cells_and_outputs_preserved":True},ensure_ascii=False))
