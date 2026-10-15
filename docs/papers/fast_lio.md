# FAST-LIO / FAST-LIO2

**Original-paper experiments: not reproduced.** See the [homepage](../../README.md#related-fast_lio) for original figures; custom-scene code tests are in Practice.

[FAST-LIO paper](https://arxiv.org/abs/2010.08196) · [FAST-LIO2 paper](https://arxiv.org/abs/2107.06829) · [Official ROS2 branch](https://github.com/hku-mars/FAST_LIO/tree/ROS2)

![FAST-LIO2 Fig. 1, page 4](../assets/related/20261016/fastlio2-fig1.png)

H2 isolates point compensation with synchronized LiDAR/IMU, known extrinsics and point times. The implementation follows FAST-LIO2 direct registration. The instance skipping only backward point correction is a disclosed ablation, not an unmodified paper baseline. Bind the author commit and patch in the run record.
