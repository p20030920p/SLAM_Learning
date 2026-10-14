# IR-MCL

English | [中文](ir-mcl.zh-CN.md)

**Bonn IPBLab indoor lab, the one released localization sequence (1543 scans, 1041 beams kept at 32).** A neural occupancy field renders a synthetic scan for every particle, and the rendered-versus-real range difference becomes the observation model of a particle filter.

![IR-MCL](../../results/reference/ir-mcl/media/preview.gif)

[Result replay](../../results/reference/ir-mcl/media/replay/replay.mp4) · [Full execution recording](../../results/reference/ir-mcl/media/session/full-session.mp4) · [Run](../../results/reference/ir-mcl/runs/ir-mcl-wsl/record.json) · [Timing](../../results/reference/ir-mcl/media/timing.json)

## Results

Global localization with the supplied config and weights, scored by the repository's own evo evaluation over its 1354-frame window: location RMSE **5.32 cm**, yaw RMSE **1.07°**. The paper reports 5.13 cm and 1.05° for the same sequence and the same window.

The retained native estimated trajectory, ground-truth trajectory and config reproduce all eight rounded metrics without spatial alignment. This evaluates localization on Seq 1; dynamic-map self-recovery remains a separate experiment.

[Paper](https://arxiv.org/abs/2210.03113) · [Paper HTML](https://ar5iv.labs.arxiv.org/html/2210.03113) · [Original repository](https://github.com/PRBonn/ir-mcl/tree/aab8c91b37e59f94442d8eddfa2f920ab1ecc4c5) · [Compatibility patch](../../results/reference/ir-mcl/runs/ir-mcl-wsl/compatibility.patch)

## Usage

[Setup and commands](../guides/REPRODUCE.md) · [Sources](../guides/ATTRIBUTION.md)

## Scope

Global localization only, on the single released sequence. The four other self-recorded sequences and the public-dataset observation-model experiments are outside this run, and the memory figure is not remeasured. Two source lines were adjusted and the C++ extension is built against the environment's own pybind11; both are disclosed in the patch.
