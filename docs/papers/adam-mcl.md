# AdaM-MCL

English | [中文](adam-mcl.zh-CN.md)

**Authored 128-cell indoor plan, one held-out scene, 200 particles.** A CNN turns a map and a 2-D scan into a samplable pose distribution, so global-localization particles are drawn from the whole map instead of a uniform prior.

## Original paper datasets and scenes

| Evaluation | Data / scene |
| --- | --- |
| Synthetic transfer | 20 maps, each 43×43 m; 18 training / two held-out test maps, six test sequences. Unknown obstacles are added or structure removed; each sequence includes global localization and one kidnapping. |
| Real observations | UPO Royal Alcazar of Seville, 150×100 m; Rawseeds Bicocca indoor, split into two 40×30 m parts. Training scans are simulated from each real scene's SLAM map or floorplan, with added obstacles. |
| Recovery evaluation | Each method/sequence is repeated 100 times; convergence requires position <2 m and yaw <10° for five consecutive updates. |

[Paper §V-A/C](https://arxiv.org/html/2009.00211#S5). Real-scene testing still supplies that environment's map for synthetic training; it does not demonstrate deployment into any unknown building without its map. Our surrogate maps, short training and cell units differ from the paper protocol.

## Observed effects before watching

| Method | Map type | Metric / effect |
| --- | --- | --- |
| AdaM-MCL | Authored 128-cell grid | RMSE 32.23 cells; historical sustained convergence 0/10 |

**Failure hypotheses to check:** inadequate training, map/scan scale or encoding mismatch, and DSOM proposals that fail to cover the true pose. The 2432-step checkpoint versus the upstream 2,880,000-step default is a known reproduction difference, not proof that training alone caused failure. Inspect proposal coverage and filtering separately before concluding the published method fails.

The video below is historical and may display withdrawn score labels; use the erratum for its numbers. The [latest actual execution](../../results/reference/desktop-adam-mcl/execution.mp4) and [latest result replay](../../results/reference/desktop-adam-mcl/result.mp4) belong to the separate 123-update run.

![AdaM-MCL recorded evaluation session](../../results/reference/adam-mcl/media/preview.gif)

[MP4](../../results/reference/adam-mcl/media/replay/replay.mp4) · [Run](../../results/reference/adam-mcl/runs/adam-mcl-wsl/record.json) · [Timing](../../results/reference/adam-mcl/media/timing.json)

## Results

The released pipeline runs end to end: the authors' data generator, path planner, training entry point and `test_MCL` evaluation all execute unmodified apart from the disclosed patch. Ten repeats of one 123-update sequence give a corrected mean per-trial position RMSE of 34.82 cells (mean final error 47.71 cells) at 0.43 s per filter update. Under the paper's convergence rule rescaled to this plan, 0 of 10 repeats hold the band for five consecutive updates, in either the global-localization or the kidnapping phase.

## Usage

[Reproduction harness](../../results/reference/adam-mcl/harness/README.md) · [Setup and commands](../guides/REPRODUCE.md) · [Sources](../guides/ATTRIBUTION.md)

## Scope

The pinned commit ships `Dataset/` and `Trained_models/` empty; the authors' 20 simulation maps, six evaluation sequences and checkpoints are Google Drive downloads that are unreachable here, and the UPO and Bicocca datasets were not obtained. This run authors its own 128-cell plans, feeds them to the authors' own generator and path planner, and trains DSOM for 2 432 optimizer steps against the authors' 2 880 000-step default. Cells are not the paper's metres, so **no Table I or Table II value is compared**. Only global localization and kidnapping are exercised; the real-dataset experiments, the PFRNN and PF-Net baselines, full SLAM, navigation and hardware accuracy remain unverified.

[Score erratum](../../results/reference/adam-mcl/ERRATUM.md): original log distances were mistakenly square-rooted by the historical exporter; original evidence retained.
