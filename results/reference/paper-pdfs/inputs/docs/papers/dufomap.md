# DUFOMap — author pipeline reproduction

English | [中文](dufomap.zh-CN.md) | [PDF](../../output/pdf/dufomap.en.pdf)

**Executed:** the complete 141-scan public KITTI-00 teaser, with supplied poses. This reproduces dynamic-point removal and map scoring; trajectory estimation is outside the experiment.

![DUFOMap measured replay](../media/dufomap/poster.png)

[MP4](../media/dufomap/replay.mp4) · [GIF](../media/dufomap/preview.gif) · [Run](../../results/reference/dufomap-wsl/record.json) · [Media provenance](../../results/reference/paper-media-dufomap/record.json)

## Method and execution

[DUFOMap (2024)](https://arxiv.org/html/2403.01449v1) accumulates occupied and observed void space. A point is classified using whether its location was observed empty. Pose/range tolerances protect against registration and measurement errors. The author implementation is DUFOMap 1.1.1; exact dependencies and upstream revisions are pinned in the repository.

```bash
bash scripts/setup_linux.sh
uv run slam-study fetch
uv run slam-study run --method dufomap
```

The full archive checksum is verified. GT annotations enter evaluation and coloring only. A 10-frame smoke run deliberately produces no paper score. Windows, fresh Ubuntu CI and local WSL runs yield identical full-teaser confusion counts.

## Measured output

| Metric | Measured % | Paper Table I % | Difference, pp |
| --- | ---: | ---: | ---: |
| SA: static retention | 97.979798 | 97.96 | +0.019798 |
| DA: dynamic removal | 98.702895 | 98.72 | -0.017105 |
| AA: geometric mean | 98.340682 | 98.34 | +0.000682 |

Evaluation uses 17,362,230 labeled points and a 5 cm map nearest-neighbor rule. Original PCL and SciPy agree pointwise, with zero disagreements. Execution succeeds, but not every paper value meets the predeclared 0.01 pp tolerance. A newer binding or parameter difference remains possible; its cause is not established.

The same-instance diagnostic increases SA by 5.347532 pp when scoring the same retained points using map proximity instead of original identities. This is a scoring effect, not an algorithm improvement. [Controls and raw counts](../RESULTS.md).

## Limitation and research relevance

The authors discuss pose sensitivity, sparse returns and regions never observed empty (III-B, V-C/E). This method already models uncertainty margins; calling it noise-unaware would be inaccurate. Enlarging a margin trades static preservation against dynamic removal, as our direct-label sensitivity shows.

Our open question is whether temporally correlated registration errors can be separated from genuine scene change at matched removal recall and observation budget. Rays sharing one pose error do not automatically supply independent evidence. This is relevant to robust mapping in dynamic environments, and to preserving geometry that later supports semantic localization.

A shared-pose/provisional-update sidecar is plausible when stable anchors exist. It must outperform margin sweeps at equal recall and delay; otherwise reject the extra mechanism. A region never seen empty is an information limitation, not a reason to invent a confident deletion. [Cross-paper argument](../STUDY.md).

## Video interpretation

The clip shows 21 named scans with raw, removed and retained points against the final offline map. Green means removed dynamic, red removed static and blue retained dynamic. Metrics use all declared points before display thinning. Playback speed is unrelated to runtime. The remaining full-sequence, trajectory and real-hardware evaluations are not completed.
