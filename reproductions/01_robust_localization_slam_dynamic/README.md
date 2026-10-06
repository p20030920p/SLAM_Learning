<div align="center">

# D1 · 动态环境下的鲁棒定位与 SLAM

**清理掉的东西，到底让定位变好还是变坏。**

![question](https://img.shields.io/badge/question-%E6%B8%85%E7%90%86%E5%AE%8C%E8%BF%98%E8%83%BD%E4%B8%8D%E8%83%BD%E5%AE%9A%E4%BD%8D-22314E)
![finding](https://img.shields.io/badge/finding-rho%28AA%2C%20%E6%95%88%E7%94%A8%29%200.78-2ea043)
![compute](https://img.shields.io/badge/compute-CPU-6f42c1)

[问题](#问题) &nbsp;•&nbsp; [目录](#目录) &nbsp;•&nbsp; [结论](#结论)

*[复现区索引](../README.md) &nbsp;•&nbsp; [D2](../02_semantic_mapping_visual_anchoring_navigation/README.md) &nbsp;•&nbsp; [背景分析](../NOTES.md)*

</div>

|  |  |
| :--- | :--- |
| 问题 | 环境里有东西在动、有东西被搬走时，地图还能不能用来定位 |
| 做法 | 先用统一指标测清得干不干净，再用下游定位器测还能不能定位，最后看两个排名是否一致 |
| 假设 | 两种排名不一致，且误删集中在可观测性低的区域 |
| 结论 | 排名确实不一致，误删分层在保住点的地图上成立 |

---

## 问题

环境里有东西在动、有东西被搬走，还有白墙暗光这类退化条件时，地图还能不能用来定位。
本方向的链条先测清理质量（点级 SA/DA/AA 或 PR/RR/F1），再用下游定位器测配准失败率与 ATE，
最后比较两个排名。

## 目录

| 编号 | 复现对象 | 角色 | 数据 | 状态 |
| :--- | :--- | :--- | :--- | :--- |
| [01-01](01_dynamicmap_benchmark/) | DynamicMap_Benchmark | 评测地基：点级真值与统一评分 | KITTI | 完成 |
| [01-02](02_kiss_icp/) | KISS-ICP | 下游定位器 | KITTI 00–10 | 完成，0.53 % |
| [01-03](03_erasor/) | ERASOR | 被测方法 | KITTI 00 | 完成，F1 0.950 |
| [01-04](04_removert/) | Removert | 被测方法 | KITTI 00 | 完成，DA 89.25 |
| [01-05](05_dufomap/) | DUFOMap | 被测方法 | KITTI 00 | 完成，精确命中 |
| [01-06](06_beautymap/) | BeautyMap | 被测方法 | KITTI 00 | 完成，命中表 I |
| [01-07](07_dynosam/) | DynoSAM | 备选：物体级动态 SLAM | KITTI tracking / OMD | 阻塞，configure 需 CUDA |
| [01-08](08_ngd_slam/) | NGD-SLAM | 动态 SLAM，相机 | TUM RGB-D | 完成，ATE 0.0157 m |
| [01-09](09_lt_mapper/) | LT-mapper | 长期建图 | KITTI 双会话 | 半完成，仓库缺建图半边 |
| [01-10](10_genz_icp/) | GenZ-ICP | 退化鲁棒的里程计 | KITTI 00–10 | 完成，0.52 % |
| [01-11](11_elite/) | ELite | 多会话地图更新 | ParkingLot | 完成，AC 0.9708 |
| [01-12](12_orb_slam3/) | ORB-SLAM3 | 视觉惯性里程计 | EuRoC | 完成，ATE 0.035–0.045 m |
| [01-13](13_khronos/) | Khronos | 4D 时空语义地图 | tesse_cd | 阻塞，需 13.5 GB 以上内存 |

## 结论

统一量表（01-01）给出四个清理方法的排名，下游配准实验（01-02）给出定位可用性排名，
两者不一致：ρ(归一化 AA, 定位效用) = 0.78，ρ(提交口径 AA) = 0.38，ρ(SA) = 0.23。
按提交口径的指标排名更不预测定位效果。

误删分层：Removert 官方实现在从没被看到的点上误删率是每帧都看得到的点的 51 倍，
而在体素化到 0.2 m 的地图上这条曲线反过来，说明那些误删来自分辨率而不是误分类。

两条方法学上的修正也在这里：官方实现与基准重实现可以差 47.7 个百分点（01-04），
指标本身也会左右结论（01-03 的 SA 在换口径后从 95.62 掉到 66.71）。
