"""Publish original paper figures, explicitly separating custom-scene tests."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]


def publish():
    for zh, path in [(True, ROOT / "docs/HOME.zh-CN.md"), (False, ROOT / "README.md")]:
        text = path.read_text(encoding="utf-8")
        base = "assets/related/20261016/" if zh else "docs/assets/related/20261016/"
        fast = "papers/fast_lio.zh-CN.md" if zh else "docs/papers/fast_lio.md"
        srrg = "papers/srrg_mapper2d.zh-CN.md" if zh else "docs/papers/srrg_mapper2d.md"
        text = re.sub(r'^\| <a id="related-(?:srrg_mapper2d|fast_lio)"></a>.*\n', "", text, flags=re.M)
        rows = (
            f'| <a id="related-fast_lio"></a>[FAST-LIO / FAST-LIO2]({fast}) | <img src="{base}fastlio2-fig1.png" width="230" alt="FAST-LIO2 original Fig. 1"> | '
            + (
                "原文实验：**不复现**；原图与方法介绍，自有场景测试见Practice"
                if zh
                else "Original-paper experiments: **not reproduced**; original figure and method summary; custom-scene tests in Practice"
            )
            + " |  |\n"
            f'| <a id="related-srrg_mapper2d"></a>[SRRG / srrg_mapper2d]({srrg}) | <img src="{base}srrg-fig1.png" width="230" alt="SRRG original Fig. 1"> | '
            + (
                "原文实验：**不复现**；原图与方法介绍，自有场景测试见Practice"
                if zh
                else "Original-paper experiments: **not reproduced**; original figure and method summary; custom-scene tests in Practice"
            )
            + " |  |\n"
        )
        # Insert into the existing overview table without altering other papers.
        at = text.index('| <a id="related-dufomap"></a>')
        text = text[:at] + rows + text[at:]
        if zh:
            details = f"""<!-- SRRG_RELATED -->
### SRRG · 原生二维动态环境建图

**原文实验：不复现。** 使用论文原图介绍方法；自有Gazebo场景中的作者代码测试独立列在[Practice](#srrg-2d)，不等于复现LCAS／MIT Stata长期多会话实验。

![SRRG 原文图1：系统流程]({base}srrg-fig1.png)

来源：Lázaro等，*Efficient Long-term Mapping in Dynamic Environments*，IROS 2018，图1，第2页。[原文](https://iris.uniroma1.it/handle/11573/1340118) · [作者代码](https://gitlab.com/srrg-software/srrg_mapper2d)。二维点云和里程计经过配准、局部图维护与位姿图优化；对应H1的动态地图维护，也需要检查H3中的几何约束。
<!-- /SRRG_RELATED -->

<!-- FASTLIO_RELATED -->
### FAST-LIO / FAST-LIO2 · LiDAR–IMU运动估计与点补偿

**原文实验：不复现。** 下面是FAST-LIO2论文的原图。本文的FAST-LIO实现测试使用官方ROS2分支、FAST-LIO2直接配准路径；同名软件包与初版论文需要区分。自有场景消融见[新假设实验](#direction-experiments-20261016)。

![FAST-LIO2 原文图1：系统流程]({base}fastlio2-fig1.png)

来源：Xu等，*FAST-LIO2: Fast Direct LiDAR-inertial Odometry*，图1，第4页。[FAST-LIO论文](https://arxiv.org/abs/2010.08196) · [FAST-LIO2论文](https://arxiv.org/abs/2107.06829) · [官方ROS2代码](https://github.com/hku-mars/FAST_LIO/tree/ROS2)。IMU传播与逐点反向补偿对应H2；ikd-Tree维护的是增量空间数据结构，不能直接当成动态物体去除或镜面检测器。
<!-- /FASTLIO_RELATED -->"""
        else:
            details = f"""<!-- SRRG_RELATED -->
### SRRG · Native 2D dynamic-environment mapping

**Original-paper experiments: not reproduced.** The original figure introduces the method. Custom Gazebo runs of the author code appear separately in [Practice](#srrg-2d); these do not reproduce the LCAS/MIT Stata long-term multi-session benchmark.

![SRRG original Fig. 1: system overview]({base}srrg-fig1.png)

Source: Lázaro et al., *Efficient Long-term Mapping in Dynamic Environments*, IROS 2018, Fig. 1, page 2. [Paper](https://iris.uniroma1.it/handle/11573/1340118) · [Author code](https://gitlab.com/srrg-software/srrg_mapper2d). Registration, local maintenance and graph optimization connect H1 to geometric conditions in H3.
<!-- /SRRG_RELATED -->

<!-- FASTLIO_RELATED -->
### FAST-LIO / FAST-LIO2 · LiDAR–IMU estimation and point compensation

**Original-paper experiments: not reproduced.** This is the original FAST-LIO2 paper figure. Our custom-scene ablation uses the official ROS2 branch and FAST-LIO2 direct registration, distinct from reproducing the first FAST-LIO paper. [New hypothesis tests](#direction-experiments-20261016).

![FAST-LIO2 original Fig. 1: system overview]({base}fastlio2-fig1.png)

Source: Xu et al., *FAST-LIO2: Fast Direct LiDAR-inertial Odometry*, Fig. 1, page 4. [FAST-LIO](https://arxiv.org/abs/2010.08196) · [FAST-LIO2](https://arxiv.org/abs/2107.06829) · [Official ROS2 code](https://github.com/hku-mars/FAST_LIO/tree/ROS2). IMU propagation and backward point compensation address H2. The incremental spatial index is not a dynamic-object removal or mirror detector.
<!-- /FASTLIO_RELATED -->"""
        text = re.sub(r"<!-- FASTLIO_RELATED -->.*?<!-- /FASTLIO_RELATED -->\s*", "", text, flags=re.S)
        text = re.sub(r"<!-- SRRG_RELATED -->.*?<!-- /SRRG_RELATED -->", lambda _: details, text, flags=re.S)
        path.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    publish()
