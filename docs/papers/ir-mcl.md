# IR-MCL

English | [中文](ir-mcl.zh-CN.md)

**Bonn IPBLab indoor lab, the one released localization sequence (1543 scans, 1041 beams kept at 32).** A neural occupancy field renders a synthetic scan for every particle, and the rendered-versus-real range difference becomes the observation model of a particle filter.

## Original paper datasets and scenes

| Evaluation | Data / scene |
| --- | --- |
| Global localization / pose tracking | Bonn IPBLab: offices, corridor and kitchen; Kuka YouBot with Hokuyo UTM-30LX 2D LiDAR. A 31,608-frame mapping sequence trains the field; five shorter sequences test localization. |
| Observation-model comparison | Freiburg Building 079, Intel Lab and MIT CSAIL Lab: indoor 2D scans split into training/validation/test subsets. These measure predicted-scan accuracy, not global-localization performance. |
| Evaluated task | Localization in a known environment represented by a trained neural occupancy field; global initialization and tracking are reported separately. |

[Paper §IV-A–C](https://ar5iv.labs.arxiv.org/html/2210.03113#S4). Its experiments do not establish recovery under our corridor scan restriction or major persistent map changes. Our reproduction covers only the released IPBLab Seq 1.

## Observed effects before watching

| Method | Map type | Metric / effect |
| --- | --- | --- |
| IR-MCL | Neural occupancy field | RMSE 5.31 cm / 1.07°; Seq-1 localization works |

**Failure hypothesis to check:** an obsolete learned field can render the wrong expected scan; repeated corridor geometry or too few informative beams can leave several pose hypotheses plausible. Check rendered-versus-measured residuals and particle coverage. These are diagnostic inferences, not observed failures in our Seq-1 run.

The media below are retained historical evidence; the [latest actual execution](../../results/reference/desktop-live-ir-mcl/execution.mp4) observes fresh author-code inference.

![IR-MCL](../../results/reference/ir-mcl/media/preview.gif)

[Result replay](../../results/reference/ir-mcl/media/replay/replay.mp4) · [Full execution recording](../../results/reference/ir-mcl/media/session/full-session.mp4) · [Run](../../results/reference/ir-mcl/runs/ir-mcl-wsl/record.json) · [Timing](../../results/reference/ir-mcl/media/timing.json)

## Results

Global localization with the supplied config and weights, scored by the repository's own evo evaluation over its 1354-frame window: location RMSE **5.32 cm**, yaw RMSE **1.07°**. The paper reports 5.13 cm and 1.05° for the same sequence and the same window.

Only position and yaw RMSE are displayed here; the native estimated trajectory, truth, config and full scores remain recomputable. Seq 1 evaluates localization in an existing map, so DA/SA do not apply; dynamic-map self-recovery remains a separate experiment.

[Paper](https://arxiv.org/abs/2210.03113) · [Paper HTML](https://ar5iv.labs.arxiv.org/html/2210.03113) · [Original repository](https://github.com/PRBonn/ir-mcl/tree/aab8c91b37e59f94442d8eddfa2f920ab1ecc4c5) · [Compatibility patch](../../results/reference/ir-mcl/runs/ir-mcl-wsl/compatibility.patch)

## Usage

[Setup and commands](../guides/REPRODUCE.md) · [Sources](../guides/ATTRIBUTION.md)

## Scope

Global localization only, on the single released sequence. The four other self-recorded sequences and the public-dataset observation-model experiments are outside this run, and the memory figure is not remeasured. Two source lines were adjusted and the C++ extension is built against the environment's own pybind11; both are disclosed in the patch.
