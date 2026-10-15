"""Two independent galleries: related-method practice and own hypothesis tests."""

from html import escape

from own_research_home import ROOT, SUITE
from simple_research_home import SUITE as PAPER_SUITE


def page(title, groups, out):
    content = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        f"<title>{title}</title>",
        '<style>body{max-width:1200px;margin:24px auto;padding:0 20px;font:16px/1.7 system-ui;background:#f4f6f8}nav{position:sticky;top:0;padding:12px;background:white}section{margin:24px 0}article{background:white;padding:16px;margin:16px 0}video{width:100%;max-width:960px}a{color:#075ca8}</style>',
        f"<h1>{title}</h1>", '<nav><a href="gallery.html">Practice · 论文方法实践</a> · <a href="hypotheses.html">Hypothesis test · 自写方法</a> · <a href="../docs/HOME.zh-CN.md">中文首页</a></nav>',
        '<p>A按任务看清图比例或地图几何；B看冻结地图后的定位误差。DA/SA不表示定位精度；完整导航到达效果尚未测试。<a href="../docs/HOME.zh-CN.md#指标">指标与数值</a> · <a href="../docs/HOME.zh-CN.md#raw-baseline-definitions">Raw基线定义</a></p>']
    for anchor, label, clips in groups:
        content.append(f'<section id="{anchor}"><h2>{escape(label)}</h2>')
        for path, caption in clips:
            assert (ROOT / path).is_file(), path
            content.append(f'<article><h3>{escape(caption)}</h3><video controls preload="none" src="../{path}"></video><a href="../{path}">MP4</a></article>')
        content.append('</section>')
    content.append('</html>')
    (ROOT / out).write_text("\n".join(content) + "\n", encoding="utf-8", newline="\n")


def publish():
    own = []
    for scene, title in [("static", "H1 静态"), ("dynamic", "H1 动态"), ("motion", "H2 里程计去畸变")]:
        clips = [(f"{SUITE}/{scene}-A/execution.mp4", title + " · A · 自写方法对照")]
        folder = ROOT / SUITE / (scene + "-B/executions")
        clips += [(p.relative_to(ROOT).as_posix(), title + " · B · " + p.stem + " map / AMCL") for p in sorted(folder.glob("*.mp4"))]
        own.append((scene, title, clips))
    page("Hypothesis test · 自写方法实验", own, "demo/hypotheses.html")
    paper = []
    clips = []
    for scene in ("static", "dynamic", "corridor"):
        clips.append((f"{PAPER_SUITE}/2d-A-{scene}/execution.mp4", "SRRG · " + scene + " · A"))
        clips += [(p.relative_to(ROOT).as_posix(), "SRRG · " + scene + " · B · " + p.stem) for p in sorted((ROOT / PAPER_SUITE / ("2d-" + scene) / "executions").glob("*.mp4"))]
    paper.append(("srrg", "P1 · SRRG", clips))
    paper.append(("fastlio", "P2 · FAST-LIO", [(f"{PAPER_SUITE}/fastlio-motion/execution.mp4", "FAST-LIO · A · 运动阶段"), *[(p.relative_to(ROOT).as_posix(), "FAST-LIO · B · " + p.stem) for p in sorted((ROOT / PAPER_SUITE / "fastlio-B/executions").glob("*.mp4"))]]))
    clips = [(f"results/reference/desktop-live-{method}/execution.mp4", "KITTI-00 · " + method) for method in ("dufomap", "beautymap")]
    clips += [(f"results/reference/robot-3d-{scene}/executions/{method}.mp4", scene + " · " + method + " / GICP") for scene in ("static", "dynamic", "corridor", "large-change") for method in ("raw", "dufomap", "beautymap")]
    paper.append(("3d", "P3 · DUFOMap / BeautyMap · 3D", clips))
    paper.append(("irmcl", "P4 · IR-MCL", [("results/reference/desktop-live-ir-mcl/execution.mp4", "Bonn · 原生执行")]))
    paper.append(("adam", "P5 · AdaM-MCL", [("results/reference/desktop-adam-mcl/result.mp4", "保存结果回放")]))
    page("Practice · Related works方法实践", paper, "demo/gallery.html")


if __name__ == "__main__":
    publish()
