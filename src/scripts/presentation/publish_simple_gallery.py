"""Show only the current three-hypothesis recordings and unchanged 3D baselines."""

from html import escape

from simple_research_home import ROOT, SUITE


def publish():
    lines = [
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        "<title>SLAM · H1/H2/H3 新实验录像</title>",
        "<style>body{max-width:1200px;margin:32px auto;padding:0 24px;font:16px/1.65 system-ui;background:#f5f7fa;color:#182331}nav{position:sticky;top:0;background:white;padding:12px}article{background:white;padding:18px;margin:16px 0;border-radius:12px}video{display:block;width:100%;max-width:960px}a{color:#075ca8}</style>",
        "<h1>H1 / H2 / H3 · 新实验录像</h1>",
        '<nav><a href="#h1">动态清图</a> · <a href="#h2">运动畸变</a> · <a href="#h3">长廊参照</a> · <a href="#baseline">三维原测试</a> · <a href="../docs/HOME.zh-CN.md#practice-index">指标与分析</a></nav>',
        "<p>A为建图，B为另一次独立定位采集；此页显示原生Gazebo／RViz实录。</p>",
    ]

    def clip(path, title):
        assert (ROOT / path).is_file(), path
        lines.append(
            f'<article><h3>{escape(title)}</h3><video controls preload="none" src="../{path}"></video><a href="../{path}">MP4</a></article>'
        )

    lines += ['<section id="h1"><h2>H1 · 动态清图</h2>']
    for scene, title in [("static", "静态对照"), ("dynamic", "运动障碍物")]:
        clip(f"{SUITE}/2d-A-{scene}/execution.mp4", title + " · 新A · Raw / SRRG")
        for method in ["raw", "srrg"]:
            clip(f"{SUITE}/2d-{scene}/executions/{method}.mp4", title + " · 新B · " + method + " map / AMCL")
    lines += [
        '</section><section id="h2"><h2>H2 · FAST-LIO点补偿</h2><p>绿色为开启补偿，橙色为关闭补偿；保留两组的IMU状态预测。</p>'
    ]
    clip(f"{SUITE}/fastlio-motion/execution.mp4", "新A · 静止、慢转、快转、平移")
    for method, title in [("no_deskew", "关闭点补偿"), ("deskew", "开启点补偿")]:
        clip(f"{SUITE}/fastlio-B/executions/{method}.mp4", "新B · " + title + "的冻结地图 / GICP")
    lines += ['</section><section id="h3"><h2>H3 · 长廊静态参照</h2>']
    for scene, title in [("corridor", "原长廊"), ("landmark-corridor", "加非对称参照长廊")]:
        clip(f"{SUITE}/2d-A-{scene}/execution.mp4", title + " · 新A · Raw / SRRG")
        for method in ["degraded_raw", "degraded_srrg"]:
            clip(f"{SUITE}/2d-{scene}/executions/{method}.mp4", title + " · 新B · " + method + " map / AMCL")
    lines += ['</section><section id="baseline"><h2>三维原测试</h2>']
    for scene, title in [
        ("static", "静态"),
        ("dynamic", "动态"),
        ("corridor", "长廊"),
        ("large-change", "结构变化"),
    ]:
        for method in ["raw", "dufomap", "beautymap"]:
            clip(
                f"results/reference/robot-3d-{scene}/executions/{method}.mp4",
                title + " · " + method + " map / GICP · 原记录",
            )
    lines += ["</section></html>"]
    (ROOT / "demo/gallery.html").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    publish()
