# AdaM-MCL

English | [中文](adam-mcl.zh-CN.md)

**Authored 128-cell indoor plan, one held-out scene, 200 particles.** A CNN turns a map and a 2-D scan into a samplable pose distribution, so global-localization particles are drawn from the whole map instead of a uniform prior.

![AdaM-MCL recorded evaluation session](../../results/reference/adam-mcl/media/preview.gif)

[MP4](../../results/reference/adam-mcl/media/replay/replay.mp4) · [Run](../../results/reference/adam-mcl/runs/adam-mcl-wsl/record.json) · [Timing](../../results/reference/adam-mcl/media/timing.json)

## Results

The released pipeline runs end to end: the authors' data generator, path planner, training entry point and `test_MCL` evaluation all execute unmodified apart from the disclosed patch. Ten repeats of one 123-update sequence give a position RMSE of 5.49 cells (median 5.58, worst final error 7.61) at 0.43 s per filter update. Under the paper's convergence rule rescaled to this plan, 0 of 10 repeats hold the band for five consecutive updates, in either the global-localization or the kidnapping phase.

## Usage

[Reproduction harness](../../results/reference/adam-mcl/harness/README.md) · [Setup and commands](../guides/REPRODUCE.md) · [Sources](../guides/ATTRIBUTION.md)

## Scope

The pinned commit ships `Dataset/` and `Trained_models/` empty; the authors' 20 simulation maps, six evaluation sequences and checkpoints are Google Drive downloads that are unreachable here, and the UPO and Bicocca datasets were not obtained. This run authors its own 128-cell plans, feeds them to the authors' own generator and path planner, and trains DSOM for 2 432 optimizer steps against the authors' 2 880 000-step default. Cells are not the paper's metres, so **no Table I or Table II value is compared**. Only global localization and kidnapping are exercised; the real-dataset experiments, the PFRNN and PF-Net baselines, full SLAM, navigation and hardware accuracy remain unverified.
