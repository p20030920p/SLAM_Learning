"""Current videos: native SRRG 2D, unchanged 3D arms, H2 and H3 controls."""

from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[3]
SUITE = "results/reference/direction-20261016"


def publish():
    lines = [
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        "<title>SLAM · 当前实验录像</title>",
        "<style>body{max-width:1280px;margin:32px auto;padding:0 24px;font:16px/1.65 system-ui;color:#182331;background:#f5f7fa}nav{position:sticky;top:0;background:white;padding:12px}section{margin:36px 0}article{background:white;padding:18px;margin:16px 0;border-radius:12px}video,img{display:block;width:100%;max-width:960px}a{color:#075ca8}h3{margin-top:0}</style>",
        "<h1>当前实验录像 · H1 / H2 / H3</h1>",
        '<nav><a href="#2d">原生2D</a> · <a href="#3d">原三维测试</a> · <a href="#h2">FAST-LIO</a> · <a href="#h3">长廊与缺测</a> · <a href="../docs/HOME.zh-CN.md#direction-experiments-20261016">指标与分析</a></nav>',
        "<p>Gazebo／RViz实录与数据回放分别标注。二维为Raw／SRRG；原三维Raw／DUFOMap／BeautyMap保持不变。单轮探索不等于原文复现。</p>",
    ]

    def clip(path, title):
        assert (ROOT / path).is_file(), path
        lines.append(
            f'<article><h3>{escape(title)}</h3><video controls preload="none" src="../{path}"></video><a href="../{path}">MP4</a></article>'
        )

    lines += ['<section id="2d"><h2>E1 · 原生二维建图与定位</h2>']
    for scene, title in [("static", "静态"), ("dynamic", "动态"), ("corridor", "长廊")]:
        clip(f"{SUITE}/2d-A-{scene}/execution.mp4", title + " · 对应A采集（历史录制）")
        for method in ["raw", "srrg"]:
            case = ("degraded_" if scene == "corridor" else "") + method
            clip(f"{SUITE}/2d-{scene}/executions/{case}.mp4", title + " · 独立B · " + method)
    lines += ['</section><section id="3d"><h2>原三维地图与GICP测试（保持原记录）</h2>']
    for scene, title in [("static", "静态"), ("dynamic", "动态"), ("corridor", "长廊")]:
        for method in ["raw", "dufomap", "beautymap"]:
            clip(
                f"results/reference/robot-3d-{scene}/executions/{method}.mp4",
                title + " · 3D · " + method + " map / GICP",
            )
    lines += [
        '</section><section id="h2"><h2>E2 · FAST-LIO2点补偿</h2><p>绿色：开启点补偿；橙色：关闭点补偿。两组同输入，IMU预测保留。</p>'
    ]
    clip(f"{SUITE}/fastlio-motion/execution.mp4", "A · 原生点补偿开／关")
    for method in ["deskew", "no_deskew"]:
        clip(f"{SUITE}/fastlio-B/executions/{method}.mp4", "独立GICP B · " + method)
    lines += ['</section><section id="h3"><h2>E3 · 长廊几何与缺测边界</h2>']
    clip(f"{SUITE}/corridor-landmark-mapping/execution.mp4", "派生长廊 · 新增非对称几何标志 · A")
    for method in ["degraded_raw", "degraded_srrg"]:
        clip(f"{SUITE}/2d-landmark-corridor/executions/{method}.mp4", "派生长廊 · B · " + method)
    lines += [
        f'<article><h3>E3a · 受控缺测数据回放（不是镜面物理实录）</h3><img src="../{SUITE}/mirror-control/control-replay.gif" alt="受控缺测回放"></article>',
        '</section><p><a href="archive-20261014.html">较早录像页</a></p></html>',
    ]
    (ROOT / "demo/gallery.html").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    publish()
