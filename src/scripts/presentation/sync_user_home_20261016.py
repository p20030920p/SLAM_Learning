"""Synchronize the user's Chinese analysis, with portable evidence images."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).parent))
from publish_home_experiments import sections, apply_home_layout  # noqa: E402

DIRECTION = """## Direction analysis

### 1. What does the research title ask?

**Direction: robust localization and SLAM in dynamic environments.**

Mapping and localization support each other. Our evaluation changes the map, then uses the same localization method to test whether error decreases.

My understanding of localization:

- Given a motion prior, use current observations to score consistency with the map and infer pose and confidence.
- AMCL represents possible poses with particles and weights them using an observation model; GICP estimates pose through geometric consistency.
- The map supplies the references against which sensor observations can be matched.

Our goal is therefore **to improve mapping and test the resulting improvement in localization**.

- **Moving objects leave traces that contaminate the map. This is our main focus.** Detect and remove motion while preserving static structures.
  - 2D LiDAR: SRRG.
  - 3D LiDAR: DUFOMap and BeautyMap.

    ![DUFOMap detection and cleaning example](docs/media/direction/20261016-user/image-20261015222612651.png)

  - Depth/RGB camera: DynaSLAM.

    ![DynaSLAM example](docs/media/direction/20261016-user/image-20261015222431746.png)

- **Sensor motion within a scan causes motion distortion**, which can affect registration, trajectory drift and map alignment. High speed or rotation makes timing errors more visible; drift can also have other causes.

  ![Motion-distortion example](docs/media/direction/20261016-user/image-20261015230734740.png)

  FAST-LIO estimates motion using LiDAR and IMU and compensates points before registration. This is a candidate for fast-motion tests, rather than a guarantee against all failures. [Official implementation](https://github.com/hku-mars/FAST_LIO/tree/ROS2).

  ![FAST-LIO example supplied with the Chinese analysis](docs/media/direction/20261016-user/image-20261015231926970.png)

  My interpretation: combining vision, LiDAR and odometry can provide complementary evidence, but synchronization, calibration and fusion themselves need validation.

- **Special materials and geometrically weak environments can damage mapping and localization.**
  - Mirrors:

    ![Mirror-related map issue](docs/media/direction/20261016-user/image-20261015230454037.png)

  - Corridors:

    ![Corridor example](docs/media/direction/20261016-user/image-20261015234829998.png)

    Repeated or parallel structures can leave the along-corridor position weakly constrained. A possible intervention is an identifiable landmark, such as a mapped visual marker. A QR marker requires a camera and detector; a LiDAR-only test must use visible geometry.

- **Maps need maintenance after construction** to remain useful for localization. Relocated furniture motivates updates, for example Khronos.

  ![Persistent-change example](docs/media/direction/20261016-user/image-20261016000012003.png)

  Temporal evidence helps distinguish persistent structures, occasional relocation and rapid motion. Recognition and segmentation can support these decisions and object-level navigation or manipulation; a semantic class alone does not establish whether something is moving now.

The core question is:

**In a dynamic environment, how can we build a geometrically trustworthy map that retains useful static constraints, and test whether it improves localization accuracy and continuity?**

"""

QUESTIONS = """## Open question

**Broad direction: which strategies enable reliable mapping in changing environments, and thereby reliable localization?**

**Question 1:** Given multiple scans and mapping poses, how can dynamic traces be removed while preserving static structures, and under which contamination and geometric conditions does this improve independent localization?

**Question 2:** With other conditions controlled, how can motion distortion caused by fast translation or rotation of the sensor be reduced?

**Question 3:** How can special obstacles be identified and weak environments such as corridors handled, limiting their effect on mapping and subsequent localization?

"""


def main():
    zh = (ROOT / "docs/HOME.zh-CN.md").read_text(encoding="utf-8")
    en_path = ROOT / "README.md"
    en = en_path.read_text(encoding="utf-8")
    _, zblocks = sections(zh)
    _, eblocks = sections(en)
    physical = zblocks["Problem getting from Physical test"]
    # Translate the author's observations without replacing their analysis slots.
    physical = physical.replace('href="media/', 'href="docs/media/').replace(
        'src="media/', 'src="docs/media/'
    )
    translations = {
        "### 镜面与建图不全": "### Mirror and incomplete mapping",
        "图1：镜面": "Figure 1: mirror",
        "图2：镜面导致的建图不全": "Figure 2: incomplete mapping associated with the mirror",
        "从图2中可以看出，当出现镜面的情况下，建图会难以继续，这是建图中的一个问题之一，在定位时候也是如此，没法扫描出边界": "Observation from Figure 2: the mirror region lacks a usable mapped boundary, which also removes a reference for localization.",
        "实物现场": "Physical scene",
        "RViz 静态视频": "RViz static video",
        "RViz 动态视频": "RViz dynamic video",
        "**分析：**从视频中，其一，可以看出，由于运动速度过快，导致建图过程中建图的畸变；其次，从动态视频中可以看出，由于动态人的出现，导致建图中间出现了污染点。": "**Analysis:** The video suggests distortion during fast motion, and the moving person leaves unwanted points in the map. These are the author's observations motivating separate controlled tests.",
        "**分析：**": "**Analysis:**",
    }
    for a, b in translations.items():
        physical = physical.replace(a, b)
    for name, body in [
        ("Problem getting from Physical test", physical),
        ("Direction analysis", DIRECTION),
        ("Open question", QUESTIONS),
    ]:
        en = en.replace(eblocks[name], body, 1)
    en_path.write_text(apply_home_layout(en, False), encoding="utf-8", newline="\n")
    (ROOT / "docs/HOME.zh-CN.md").write_text(apply_home_layout(zh, True), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
