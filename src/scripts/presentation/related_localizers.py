"""Introduce the common frozen-map localizers using attributed source images."""

import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "docs/assets/related/20261016-localizers"
AMCL_REPO = "https://github.com/ros-navigation/navigation2/tree/main/nav2_amcl"
AMCL_FIGURE = "https://github.com/ros-navigation/docs.nav2.org/blob/8f6571b599d6b1e899f11ac58c5c1982d3b0a8b5/docs/getting_started/quickstart/assets/rviz/navstack_ready.png"
GICP_REPO = "https://github.com/avsegal/gicp"
GICP_AUTHOR = "https://www.robots.ox.ac.uk/~avsegal/generalized_icp.html"
GICP_PCL = "https://pointclouds.org/documentation/classpcl_1_1_generalized_iterative_closest_point.html"
GICP_ROS = "https://github.com/rsasaki0109/lidar_localization_ros2"


def related_localizers(text, doc, zh):
    def s(cn, en):
        return cn if zh else en

    def asset(name):
        path = ASSETS / name
        assert path.is_file(), path
        return os.path.relpath(path, doc.parent).replace("\\", "/")

    amcl_image, gicp_image = asset("amcl-nav2-original.png"), asset("gicp-author-original.jpg")
    text = text.replace("原库复现GIF／原文点云图", "原库实录GIF／原始图示").replace(
        "Native GIF / original point-cloud figure", "Native GIF / original-source illustration"
    )
    text = re.sub(r'^\| <a id="related-(?:amcl|gicp)"></a>.*\n', "", text, flags=re.M)
    text = re.sub(r"<!-- LOCALIZERS_RELATED -->.*?<!-- /LOCALIZERS_RELATED -->\s*", "", text, flags=re.S)
    rows = (
        f'| <a id="related-amcl"></a>[AMCL / Nav2]({AMCL_REPO})<br>'
        + s("二维粒子定位", "2D particle localization")
        + f' | <a href="{AMCL_FIGURE}"><img src="{amcl_image}" width="280" loading="lazy" alt="AMCL: original Nav2 repository localization screenshot"></a><br>'
        + s("Nav2官方文档库原图", "Original Nav2 documentation-repository image")
        + " | " + s("二维冻结地图定位器；看XY／偏航RMSE。原库图示，非本项目实录；[方法说明](#related-amcl-details)",
                       "Common 2D frozen-map localizer; XY / yaw RMSE. Source illustration, not our recording; [method](#related-amcl-details)") + " |  |\n"
        + f'| <a id="related-gicp"></a>[GICP]({GICP_REPO})<br>'
        + s("三维几何配准", "3D geometric registration")
        + f' | <a href="{GICP_AUTHOR}"><img src="{gicp_image}" width="280" loading="lazy" alt="GICP: original point-cloud illustration from the algorithm author"></a><br>'
        + s("GICP作者主页原图", "Original GICP author-page image")
        + " | " + s("三维冻结地图定位器；看XYZ／旋转RMSE。原作者图示，非本项目实录；[方法说明](#related-gicp-details)",
                       "Common 3D frozen-map localizer; XYZ / rotation RMSE. Author illustration, not our recording; [method](#related-gicp-details)") + " |  |\n"
    )
    target = '| <a id="related-ir-mcl"></a>'
    assert text.count(target) == 1
    text = text.replace(target, rows + target, 1)
    if zh:
        details = f"""<!-- LOCALIZERS_RELATED -->
<a id="related-amcl-details"></a>

### AMCL · 在已建好的二维地图中定位

**输入 → 处理 → 输出：**固定二维占据栅格地图、激光扫描与里程计 → 粒子运动预测、扫描与地图匹配加权、重采样及自适应粒子数量 → 平面位置、偏航与位姿不确定性。AMCL负责定位，不构建或清理地图。

<img src="{amcl_image}" width="680" alt="Nav2官方文档库原图：地图中的机器人与AMCL粒子分布">

**图源：**[Nav2官方文档库原图]({AMCL_FIGURE})，展示机器人、粒子分布及导航栈图层；非本项目录制。[AMCL官方代码]({AMCL_REPO})。

**与本文的关系：**二维Practice及自写H1／H2均使用AMCL，在冻结A地图后处理独立B；对照共用扫描、里程计、参数及初始化，评价XY定位误差，按需要报告偏航误差。地图残影或静态约束损失会改变扫描匹配权重；DA／SA不用于评价AMCL。自有场景测试见[Practice](#practice-index)与[Hypothesis test](#hypothesis-test-index)，不复现原文基准实验。

<a id="related-gicp-details"></a>

### GICP · 将三维扫描配准到固定点云地图

**输入 → 处理 → 输出：**固定三维点云地图、当前扫描与初始位姿预测 → 建立对应，利用两侧局部表面协方差加权残差，迭代求解刚体变换 → 三维位置与姿态。原始GICP是配准算法；接入定位系统后用于扫描到地图定位，本身不执行动态清理。

<img src="{gicp_image}" width="400" alt="GICP作者主页原始点云示意图">

**图源：**[GICP作者主页原图]({GICP_AUTHOR})；作者参考库未提供图片，采用作者主页点云图，非本项目实录。[原始参考代码]({GICP_REPO}) · [PCL实现说明]({GICP_PCL}) · [本文使用的ROS2定位框架]({GICP_ROS})。

**与本文的关系：**三维Practice将Raw／DUFOMap／BeautyMap的A地图冻结，用相同GICP配置处理新B点云与轮速里程计，评价XYZ及三维旋转RMSE。地图清理由前述方法完成，GICP只检验下游定位。局部配准依赖初值和几何约束；长廊中角度误差小也可能伴随纵向米级漂移。自有场景测试见[三维Practice](#scene-static-3d)；当前安装版ROS2/PCL实现不等同于作者参考库复现，也不复现原文基准实验。
<!-- /LOCALIZERS_RELATED -->

"""
    else:
        details = f"""<!-- LOCALIZERS_RELATED -->
<a id="related-amcl-details"></a>

### AMCL · Localization in a prebuilt 2D map

**Input → process → output:** a fixed occupancy grid, laser scans and odometry → particle motion prediction, scan-to-map weighting, resampling and adaptive particle counts → planar position, yaw and pose uncertainty. AMCL localizes; it does not build or clean the map.

<img src="{amcl_image}" width="680" alt="Original Nav2 repository screenshot: robot and AMCL particles in the map">

**Image source:** [original Nav2 documentation-repository image]({AMCL_FIGURE}), showing the robot, particle distribution and navigation-stack layers; not our recording. [Official AMCL code]({AMCL_REPO}).

**Role here:** 2D Practice and our H1/H2 use AMCL on frozen A maps with independently acquired B. Paired controls share scans, odometry, parameters and initialization; evaluate XY localization RMSE and yaw when relevant. Map remnants and lost static constraints affect observation weights. DA/SA do not evaluate AMCL. Custom-scene tests are in [Practice](#practice-index) and [Hypothesis test](#hypothesis-test-index); original-paper benchmarks are not reproduced.

<a id="related-gicp-details"></a>

### GICP · Register a 3D scan to a fixed point-cloud map

**Input → process → output:** a fixed 3D point-cloud map, a current scan and an initial pose prediction → establish correspondences, weight residuals using local surface covariances on both sides, and iteratively solve a rigid transform → 3D position and orientation. GICP is originally a registration algorithm; a localization system uses it for scan-to-map matching. It does not remove dynamic objects itself.

<img src="{gicp_image}" width="400" alt="Original point-cloud illustration from the GICP author page">

**Image source:** [original GICP author-page image]({GICP_AUTHOR}). The author's reference repository contains no image; this uses the author's own point-cloud illustration, not our recording. [Reference code]({GICP_REPO}) · [PCL implementation]({GICP_PCL}) · [ROS2 localization framework used here]({GICP_ROS}).

**Role here:** 3D Practice freezes Raw/DUFOMap/BeautyMap A maps and applies the same GICP configuration to fresh B clouds and wheel odometry, evaluating XYZ and full-rotation RMSE. The preceding methods clean the maps; GICP evaluates downstream localization. Local registration depends on initialization and geometric constraints; small angular errors can coexist with metre-scale longitudinal drift in corridors. See [3D Practice](#scene-static-3d). Our installed ROS2/PCL implementation is distinct from the author's reference code; original-paper benchmarks are not reproduced.
<!-- /LOCALIZERS_RELATED -->

"""
    closing = "<!-- /HOME_RELATED_DETAILS -->"
    assert text.count(closing) == 1
    return text.replace(closing, details + closing, 1)


def publish():
    for path, zh in [("README.md", False), ("docs/HOME.zh-CN.md", True)]:
        doc = ROOT / path
        text = doc.read_text(encoding="utf-8")
        doc.write_text(related_localizers(text, doc, zh), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    publish()
