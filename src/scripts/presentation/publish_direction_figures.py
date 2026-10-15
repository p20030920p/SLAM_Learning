"""Publish the editable workflow and factor figures in both homepages."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]

DIRECTION_ZH = """**1. SLAM 的整体流程：位姿与地图共同估计。** 传感器观测经过同步、标定和去畸变，前端建立匹配约束，后端优化位姿等状态，再用估计位姿融合地图；地图又为后续定位提供约束。回环需要检索和几何验证，错误回环也会破坏地图。不能把 SLAM 简化为“先有好地图，才有好定位”。

![SLAM 整体流程：观测、预处理、前端、后端、地图更新与地图反馈，含回环和位姿／地图输出](assets/direction/v3/slam-workflow.zh-CN.png)

**2. 影响鲁棒定位与 SLAM 的因素和实例。** 按“因素→典型实例→影响机制”阅读；图中八类问题覆盖观测、运动、标定、环境变化和算法系统。镜面属于观测可靠性问题，即使静止也可能产生错误几何；动态物体去除、持久变化更新和退化检测需要分别检验。图中的例子是分析线索，配图框等待插入实测图。

![八类影响因素及典型实例：采样、运动、标定、动态变化、镜面玻璃、退化、漂移回环、地图表示与预算；每项有独立配图位](assets/direction/v3/slam-robustness-factors.zh-CN.png)

当前研究主线是**动态残影删除→静态约束保留→独立定位检验**。本轮控制建图位姿与定位器，把干预放在地图层；地图更干净是否降低定位误差，仍由独立测试回答。IR-MCL／AdaM-MCL 属于定位参照。

[可编辑 PowerPoint 源文件（第1–2页中文，第3–4页英文）](assets/direction/v3/direction-analysis.editable.pptx) · [设计与配图位编号](assets/direction/v3/design.json) · [依据与适用边界](assets/direction/v3/sources.json) · [制图检查](assets/direction/v3/audit.json)

<details>
<summary>怎样把自己的图片放进去</summary>

打开源文件第2页，选择 F01–F08 对应的虚线框，删除框内提示文字，用“形状格式→形状填充→图片”填入自己的照片或点云截图。配图框比例约为 **1.61:1**，可先裁剪图片；标题、实例和机制文字均可单独编辑。也可删除框后插入普通图片，对齐原来的位置。

每格放一个清楚的现象，例如 F05 放镜面导致的异常点云、F07 放地图错层。需要做前后对比时，可复制页面放大比较，并注明相同视角、帧号和条件。保存 PPTX 后导出 PNG 替换同名预览图；也可运行[导出脚本](../src/scripts/presentation/draw_direction_figures.ps1)的 `-ExportOnly`，仅更新四张预览，不重建图中对象。

</details>"""

DIRECTION_EN = """**1. The SLAM workflow: estimate pose and map together.** Observations pass through synchronization, calibration and deskewing; the front end forms matching constraints, the back end optimizes poses and other states, and mapping fuses observations at estimated poses. The map constrains later tracking. Loop retrieval needs geometric validation; a false loop can damage the map. A good prior map is not a prerequisite for starting SLAM.

![Full SLAM workflow: observations, preprocessing, front end, back end, map integration and feedback, with loop validation and pose/map outputs](docs/assets/direction/v3/slam-workflow.en.png)

**2. Factors and examples affecting robust localization and SLAM.** Read each entry as factor→example→mechanism. The eight families cover observations, motion, calibration, changing scenes and the algorithm/system. A stationary mirror can still create unreliable geometry. Dynamic removal, lasting-change updates and degeneracy detection require separate tests. Examples are analysis prompts; image slots await measured evidence.

![Eight factor families and examples: sampling, motion, calibration, dynamics, reflective materials, degeneracy, drift and loops, representation and compute; independent image slots](docs/assets/direction/v3/slam-robustness-factors.en.png)

The current research chain is **dynamic trace removal → static constraint retention → held-out localization test**. Mapping poses and the localizer are controlled while intervening at the map layer. Independent testing determines whether cleaner maps lower pose error. IR-MCL/AdaM-MCL remain localization references.

[Editable PowerPoint source (slides 1–2 Chinese, 3–4 English)](docs/assets/direction/v3/direction-analysis.editable.pptx) · [Design and slot IDs](docs/assets/direction/v3/design.json) · [Sources and scope](docs/assets/direction/v3/sources.json) · [Figure checks](docs/assets/direction/v3/audit.json)

<details>
<summary>Insert your own images</summary>

Open slide 4, select the appropriate dashed F01–F08 box, delete its hint text and choose **Shape Format → Shape Fill → Picture**. Slots have an approximately **1.61:1** aspect ratio; crop the image first if needed. Titles, examples and mechanisms remain independently editable. Alternatively, delete a slot and align an ordinary inserted picture to its former bounds.

Use one clear phenomenon per field. For larger before/after comparisons, duplicate a slide and record matching viewpoints, frame IDs and conditions. Save the PPTX and export PNGs to replace the corresponding previews, or run the [export script](src/scripts/presentation/draw_direction_figures.ps1) with `-ExportOnly` to refresh all four previews without reconstructing objects.

</details>"""


def refresh_direction(text: str, chinese: bool) -> str:
    """Preserve the deliverables table and every section outside the figure intro."""
    heading = "方向分析" if chinese else "Direction analysis"
    pattern = rf"(?<=## {heading}\n\n).*?(?=\n\n\| (?:成果|Deliverable) \|)"
    replacement = DIRECTION_ZH if chinese else DIRECTION_EN
    updated, count = re.subn(pattern, lambda _: replacement, text, count=1, flags=re.S)
    if count != 1:
        raise ValueError(f"Direction intro / deliverables boundary missing: {heading}")
    return updated


def publish() -> None:
    for path, chinese in [(ROOT / "README.md", False), (ROOT / "docs/HOME.zh-CN.md", True)]:
        text = path.read_text(encoding="utf-8")
        updated = refresh_direction(text, chinese)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    publish()
