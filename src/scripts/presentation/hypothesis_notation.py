"""Shared mathematical definitions for the homepage and presentation notebook."""

from pathlib import Path
import re


def raw_baselines(zh):
    if zh:
        return """**Raw的含义。** Raw是本库对“未做地图动态清理的累积基线”的标签，不是一个独立SLAM或定位算法，也不表示完全未经预处理的数据。

| 使用位置 | Raw如何生成 | 后续定位 |
| --- | --- | --- |
| 自写H1 | 用已知起点、轮速里程计和传感器外参，把有效二维回波变到同一坐标系；5 cm栅格至少命中一次就保留，只累计、不回撤，不用H1时序过滤。 | 冻结后用AMCL |
| Practice：SRRG二维对照 | 用SRRG每帧当时估计的传感器位姿直接累计回波；历史累计点不按最终图优化结果重新投影。SRRG输出另含地图维护与图优化。 | 冻结后用AMCL |
| Practice：Raw／DUFOMap／BeautyMap三维对照 | 用受控建图A提供的传感器位姿变换并拼接三维扫描，不调用DUFOMap或BeautyMap清理。该A使用提供的仿真位姿。 | 冻结后用GICP；B不输入真值 |

因此，不同实验的Raw不是同一张图，位姿来源也不相同；只能在各自匹配的对照内比较。SRRG这一组是包含位姿优化与地图维护的端到端对照，不是只改变删除规则的消融。当前H1干预还包含自写位姿对齐，Raw不含该对齐；仅清理／仅对齐消融区分两者贡献。H2基线另称Off，只关闭逐点运动补偿；FAST-LIO实践的Off仍保留LiDAR–IMU估计。
"""
    return """**Meaning of Raw.** Raw labels this repository's accumulated baseline without dynamic-map cleaning. It is not a standalone SLAM/localization algorithm or completely unprocessed sensor data.

| Context | How Raw is built | Downstream localization |
| --- | --- | --- |
| Own H1 | Transform valid 2D returns using the known start, wheel odometry and sensor extrinsic; retain each 5 cm cell hit at least once, without retracting earlier occupied cells or applying H1 temporal filtering. | Frozen-map AMCL |
| Practice: SRRG 2D comparison | Accumulate returns using SRRG's online sensor-pose estimate at each frame; do not reproject accumulated historical points with the final optimized graph. SRRG output additionally includes map maintenance and graph optimization. | Frozen-map AMCL |
| Practice: Raw / DUFOMap / BeautyMap 3D comparison | Transform and concatenate 3D scans using provided sensor poses from controlled mapping A, without DUFOMap/BeautyMap cleaning. A uses supplied simulation poses. | Frozen-map GICP; no truth input in B |

These Raw maps and pose sources differ between experiments; compare within the matched experiment. The SRRG comparison includes pose optimization and map maintenance, not just a deletion-rule ablation. Current H1 also adds own pose alignment, which Raw does not use; filter-only / alignment-only ablations distinguish their contributions. H2 calls its baseline Off: only point-time compensation is disabled. FAST-LIO Practice Off still retains LiDAR–IMU estimation.
"""


def _explanation_parts(zh):
    language = "zh-CN" if zh else "en"
    name = "explanation.zh-CN.md" if zh else "explanation.md"
    source = Path(__file__).resolve().parents[3] / "docs/hypothesis" / name
    text = source.read_text(encoding="utf-8")
    pattern = r"<!-- HYPOTHESIS_PART:([a-z0-9_]+) -->(.*?)<!-- /HYPOTHESIS_PART:\1 -->"
    parts = {key: body.strip() for key, body in re.findall(pattern, text, re.S)}
    assert set(parts) == {"common", "h1", "h2", "comparison"}, language
    return parts


def math_sections(zh):
    """Shared formula explanations; native math for notebooks, GFM via github_math."""
    parts = _explanation_parts(zh)
    return {key: parts[key] for key in ("common", "h1", "h2")}


def srrg_comparison(zh):
    return _explanation_parts(zh)["comparison"]


def pseudocode():
    return """for test, scene in [(H1, static), (H1, dynamic), (H2, motion)]:
    A = acquire_scans_and_wheel_odometry(scene)
    if test == H1:
        M0 = integrate_A_with_wheel_poses(A)
        h, s, f = initialize_grid_evidence()
        M1 = empty_map()
        previous_wheel, previous_corrected = None, None
        for scan in A.in_time_order():
            wheel = sensor_pose_from_wheel_odometry(scan)
            predicted = wheel if previous_wheel is None else previous_corrected @ inverse(previous_wheel) @ wheel
            reference = previous_retained_cells_with_support(M1, s, min_bins=3)
            corrected = own_robust_SE2_alignment_or_wheel_fallback(scan, predicted, reference)
            points = transform_scan(scan, corrected)
            bin = floor(scan.time / 0.5)
            add_hits_once_per_cell_and_bin(h, points, bin)
            add_neighborhood_support_once_per_bin(s, points, bin, radius=0.10)
            add_free_crossings_once_per_bin(f, points, corrected, bin, stop_before_return=0.15)
            M1 = cell_centers_where((h > 0) & ((f < 3) | (f < 1.5 * s)))
            previous_wheel, previous_corrected = wheel, corrected
    else:
        M0 = integrate_A(A, point_compensation=False)
        M1 = integrate_A(A, point_compensation=True)  # no H1 filtering
    freeze(M0, M1)
    B = acquire_independent_scans_and_wheel_odometry(scene)
    positions = {}
    for m, map in [(0, M0), (1, M1)]:
        positions[m] = same_AMCL(B.scans, B.odometry, grid_of(map), same_initial_config)
    # Truth enters only here; references are shared across controls
    S, D = scoring_references_from_A_truth(A)
    if test == H1:
        score_SA(M0, M1, S)
        if scene == dynamic: score_DA(M0, M1, D)
    if test == H2: score_map_RMSE(M0, M1, S)
    score_position_RMSE(positions, B_truth, common_valid_times)
"""


def github_math(text):
    fence = chr(96) * 3
    text = re.sub(r"\$\$(.*?)\$\$", lambda m: fence + "math\n" + m[1].strip() + "\n" + fence, text, flags=re.S)
    return re.sub(r"(?<!\$)\$([^$\n]+?)\$(?!\$)", lambda m: "$" + chr(96) + m[1] + chr(96) + "$", text)
